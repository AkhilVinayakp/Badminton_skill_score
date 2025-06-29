import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import json
from config import *
import argparse
from sqlalchemy import create_engine

class EnhancedBadmintonDataGenerator:
    def __init__(self):
        self.court_length = COURT_LENGTH
        self.court_width = COURT_WIDTH
        self.shot_types = SHOT_TYPES
        self.user_skill_levels = USER_SKILL_LEVELS
        self.users = USERS
        self.score_thresholds = SCORE_THRESHOLDS
        self.session_settings = SESSION_SETTINGS
        self.generation_settings = GENERATION_SETTINGS
        
        # Set random seed for reproducibility
        np.random.seed(42)
        random.seed(42)
    
    def get_shot_type_with_frequency(self):
        """Get shot type based on frequency distribution"""
        shot_types = list(self.shot_types.keys())
        frequencies = [self.shot_types[shot]['frequency'] for shot in shot_types]
        
        # Normalize frequencies
        total_freq = sum(frequencies)
        normalized_freq = [f/total_freq for f in frequencies]
        
        return np.random.choice(shot_types, p=normalized_freq)
    
    def generate_shot_data(self, user, shot_type, timestamp):
        """Generate data for a single shot with enhanced realism"""
        shot_config = self.shot_types[shot_type]
        user_skill = self.user_skill_levels[user['skill']]
        
        # Generate landing position with more realistic distribution
        x = np.random.uniform(*shot_config['landing_x_range'])
        y = np.random.uniform(*shot_config['landing_y_range'])
        
        # Add some clustering around optimal positions based on skill
        if np.random.random() < user_skill['consistency']:
            # More skilled players tend to hit closer to optimal positions
            optimal_x = self.generation_settings['optimal_position_x']
            optimal_y = self.generation_settings['optimal_position_y']
            
            # Add some controlled randomness around optimal position
            x = np.random.normal(optimal_x, 1.0 * (1 - user_skill['consistency']))
            y = np.random.normal(optimal_y, 0.5 * (1 - user_skill['consistency']))
            
            # Ensure within court bounds
            x = max(0.5, min(12.9, x))
            y = max(0.5, min(5.6, y))
        
        # Generate speed based on shot type and user skill
        base_speed = np.random.normal(shot_config['speed_mean'], shot_config['speed_std'])
        speed = max(self.generation_settings['speed_min'], 
                   min(self.generation_settings['speed_max'], 
                       base_speed * user_skill['skill_multiplier']))
        
        # Calculate score with enhanced algorithm
        score = self.calculate_shot_score(x, y, speed, shot_type, user_skill)
        
        # Determine score type
        score_type = self.get_score_type(score)
        
        return {
            'user_id': user['id'],
            'user_name': user['name'],
            'user_skill_level': user['skill'],
            'timestamp': timestamp,
            'shot_type': shot_type,
            'landing_position_x': round(x, self.generation_settings['round_decimals']),
            'landing_position_y': round(y, self.generation_settings['round_decimals']),
            'shuttle_speed_kmh': round(speed, 1),
            'score': round(score, 1),
            'score_type': score_type
        }
    
    def calculate_shot_score(self, x, y, speed, shot_type, user_skill):
        """Enhanced score calculation algorithm"""
        shot_config = self.shot_types[shot_type]
        
        # Position accuracy (closer to optimal positions = higher score)
        optimal_x = self.generation_settings['optimal_position_x']
        optimal_y = self.generation_settings['optimal_position_y']
        
        # Calculate distance from optimal position
        distance_from_optimal = np.sqrt((x - optimal_x)**2 + (y - optimal_y)**2)
        max_distance = np.sqrt(self.court_length**2 + self.court_width**2)
        position_accuracy = 1 - (distance_from_optimal / max_distance)
        
        # Speed accuracy (optimal speed range for each shot type)
        speed_accuracy = 1 - abs(speed - shot_config['speed_mean']) / shot_config['speed_mean']
        speed_accuracy = max(0, min(1, speed_accuracy))  # Clamp between 0 and 1
        
        # Base score calculation with weighted components
        position_weight = self.generation_settings['position_weight']
        speed_weight = self.generation_settings['speed_weight']
        
        base_score = (position_accuracy * position_weight + speed_accuracy * speed_weight) * 100
        
        # Add shot type bonus
        shot_bonus = shot_config['score_bonus'] * user_skill['skill_multiplier']
        
        # Add user skill multiplier
        skill_bonus = base_score * (user_skill['skill_multiplier'] - 1) * 0.3
        
        # Calculate final score
        final_score = base_score + shot_bonus + skill_bonus
        
        # Add some randomness based on user consistency
        consistency_factor = np.random.normal(1, 1 - user_skill['consistency'])
        final_score = final_score * consistency_factor
        
        # Ensure score is within bounds
        final_score = max(0, min(100, final_score))
        
        return final_score
    
    def get_score_type(self, score):
        """Determine score type based on thresholds"""
        for score_type, (min_score, max_score) in self.score_thresholds.items():
            if min_score <= score < max_score:
                return score_type
        return 'perfect_shot'  # Default for scores >= 100
    
    def generate_daily_data(self, user, date):
        """Generate data for a single user on a single day"""
        daily_data = []
        
        # Get shots per day range based on user skill
        shots_range = self.user_skill_levels[user['skill']]['shots_per_day_range']
        num_shots = np.random.randint(*shots_range)
        
        # Generate session timing
        session_start = datetime.combine(date, datetime.min.time().replace(
            hour=self.session_settings['start_hour']))
        
        duration_range = self.session_settings['session_duration_hours']
        session_duration = timedelta(hours=np.random.uniform(*duration_range))
        
        # Generate shots with realistic timing
        shot_times = []
        for i in range(num_shots):
            # Distribute shots more evenly throughout the session
            progress = i / (num_shots - 1) if num_shots > 1 else 0.5
            base_time = session_start + timedelta(
                seconds=progress * session_duration.total_seconds())
            
            # Add some randomness around the base time
            time_variance = session_duration.total_seconds() / num_shots * 0.3
            shot_time = base_time + timedelta(
                seconds=np.random.uniform(-time_variance, time_variance))
            
            shot_times.append(shot_time)
        
        # Sort shot times
        shot_times.sort()
        
        # Generate shot data for each time
        for shot_time in shot_times:
            # Use frequency-based shot type selection
            shot_type = self.get_shot_type_with_frequency()
            
            # Generate shot data
            shot_data = self.generate_shot_data(user, shot_type, shot_time)
            daily_data.append(shot_data)
        
        return daily_data
    
    def generate_monthly_data(self, start_date=None):
        """Generate data for all users over a month"""
        if start_date is None:
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        all_data = []
        
        # Generate data for each day in the month
        current_date = start_date
        while current_date.month == start_date.month:
            # Check if we should include this day
            include_day = True
            if self.session_settings['weekdays_only'] and current_date.weekday() >= 5:
                include_day = False
            
            if include_day:
                for user in self.users:
                    daily_data = self.generate_daily_data(user, current_date)
                    all_data.extend(daily_data)
            
            current_date += timedelta(days=1)
        
        return pd.DataFrame(all_data)
    
    def save_data(self, df, filename='badminton_enhanced_data.csv'):
        """Save the generated data to CSV with enhanced statistics"""
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        print(f"Total records: {len(df)}")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # Enhanced summary statistics
        print("\n=== SUMMARY STATISTICS ===")
        print(f"Number of users: {df['user_id'].nunique()}")
        print(f"Number of shot types: {df['shot_type'].nunique()}")
        print(f"Average score: {df['score'].mean():.2f}")
        print(f"Score standard deviation: {df['score'].std():.2f}")
        
        print("\n=== SCORE DISTRIBUTION ===")
        score_counts = df['score_type'].value_counts()
        for score_type, count in score_counts.items():
            percentage = (count / len(df)) * 100
            print(f"{score_type}: {count} ({percentage:.1f}%)")
        
        print("\n=== SHOT TYPE DISTRIBUTION ===")
        shot_counts = df['shot_type'].value_counts()
        for shot_type, count in shot_counts.items():
            percentage = (count / len(df)) * 100
            print(f"{shot_type}: {count} ({percentage:.1f}%)")
        
        print("\n=== USER PERFORMANCE SUMMARY ===")
        user_stats = df.groupby(['user_name', 'user_skill_level']).agg({
            'score': ['mean', 'std', 'count'],
            'shuttle_speed_kmh': 'mean'
        }).round(2)
        print(user_stats)
        
        return df

def push_to_postgres(df):
    cfg = POSTGRES_CONFIG
    db_url = f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    engine = create_engine(db_url)
    df.to_sql(cfg['table'], engine, if_exists='append', index=False)
    print(f"Data pushed to PostgreSQL table: {cfg['table']}")

def main(push_to_db=False):
    print("Generating enhanced synthetic badminton data...")
    generator = EnhancedBadmintonDataGenerator()
    df = generator.generate_monthly_data()
    generator.save_data(df, 'badminton_enhanced_data.csv')
    sample_df = df.head(100)
    sample_df.to_csv('badminton_enhanced_sample.csv', index=False)
    print(f"\nSample data (first 100 records) saved to badminton_enhanced_sample.csv")
    print("\n=== EXAMPLE RECORDS ===")
    print(df.head(10).to_string(index=False))
    if push_to_db:
        push_to_postgres(df)
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced Badminton Data Generator")
    parser.add_argument('--push_to_db', action='store_true', help='Push generated data to PostgreSQL database')
    args = parser.parse_args()
    main(push_to_db=args.push_to_db) 