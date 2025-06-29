# Configuration file for Badminton Data Generator

# Court dimensions (standard badminton court in meters)
COURT_LENGTH = 13.4
COURT_WIDTH = 6.1

# Shot type configurations
SHOT_TYPES = {
    'smash': {
        'speed_mean': 120,  # km/h
        'speed_std': 15,
        'landing_x_range': (0.5, 12.9),  # mostly in opponent's court
        'landing_y_range': (0.5, 5.6),
        'score_bonus': 15,  # higher scoring potential
        'frequency': 0.25  # 25% of shots
    },
    'drop': {
        'speed_mean': 60,
        'speed_std': 10,
        'landing_x_range': (8.0, 12.9),
        'landing_y_range': (0.5, 5.6),
        'score_bonus': 10,
        'frequency': 0.20  # 20% of shots
    },
    'slice': {
        'speed_mean': 80,
        'speed_std': 12,
        'landing_x_range': (0.5, 12.9),
        'landing_y_range': (0.5, 5.6),
        'score_bonus': 8,
        'frequency': 0.15  # 15% of shots
    },
    'clear': {
        'speed_mean': 90,
        'speed_std': 15,
        'landing_x_range': (8.0, 12.9),
        'landing_y_range': (0.5, 5.6),
        'score_bonus': 5,
        'frequency': 0.20  # 20% of shots
    },
    'back_hand': {
        'speed_mean': 70,
        'speed_std': 12,
        'landing_x_range': (0.5, 12.9),
        'landing_y_range': (0.5, 5.6),
        'score_bonus': 3,
        'frequency': 0.10  # 10% of shots
    },
    'cross_court': {
        'speed_mean': 85,
        'speed_std': 12,
        'landing_x_range': (0.5, 12.9),
        'landing_y_range': (0.5, 5.6),
        'score_bonus': 12,
        'frequency': 0.10  # 10% of shots
    }
}

# User skill levels
USER_SKILL_LEVELS = {
    'beginner': {
        'skill_multiplier': 0.6,
        'consistency': 0.4,
        'shots_per_day_range': (15, 35)
    },
    'intermediate': {
        'skill_multiplier': 0.8,
        'consistency': 0.6,
        'shots_per_day_range': (20, 45)
    },
    'advanced': {
        'skill_multiplier': 1.0,
        'consistency': 0.8,
        'shots_per_day_range': (25, 55)
    },
    'expert': {
        'skill_multiplier': 1.2,
        'consistency': 0.9,
        'shots_per_day_range': (30, 60)
    }
}

# User profiles
USERS = [
    {'id': 1, 'name': 'Alice Johnson', 'skill': 'beginner'},
    {'id': 2, 'name': 'Bob Smith', 'skill': 'intermediate'},
    {'id': 3, 'name': 'Charlie Brown', 'skill': 'advanced'},
    {'id': 4, 'name': 'Diana Prince', 'skill': 'expert'},
    {'id': 5, 'name': 'Eve Wilson', 'skill': 'intermediate'},
    {'id': 6, 'name': 'Frank Miller', 'skill': 'beginner'},
    {'id': 7, 'name': 'Grace Lee', 'skill': 'advanced'},
    {'id': 8, 'name': 'Henry Davis', 'skill': 'expert'},
    {'id': 9, 'name': 'Ivy Chen', 'skill': 'intermediate'},
    {'id': 10, 'name': 'Jack Taylor', 'skill': 'advanced'}
]

# Score thresholds
SCORE_THRESHOLDS = {
    'bad_shot': (0, 30),
    'average_shot': (30, 50),
    'good_shot': (50, 80),
    'perfect_shot': (80, 100)
}

# Training session settings
SESSION_SETTINGS = {
    'start_hour': 9,  # 9 AM
    'session_duration_hours': (2, 3),  # 2-3 hours
    'weekdays_only': True,  # Skip weekends
    'include_weekends': False
}

# Data generation settings
GENERATION_SETTINGS = {
    'include_timestamp': True,
    'round_decimals': 2,
    'speed_min': 30,  # km/h
    'speed_max': 150,  # km/h
    'optimal_position_x': 10.7,  # near the back line
    'optimal_position_y': 3.05,  # center of court
    'position_weight': 0.6,  # weight for position accuracy in scoring
    'speed_weight': 0.4   # weight for speed accuracy in scoring
}

# PostgreSQL database configuration
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'badminton_db',
    'user': 'postgres',
    'password': '',
    'table': 'badminton_shots'
} 