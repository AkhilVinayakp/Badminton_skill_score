import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder
import mlflow
import mlflow.sklearn
from prefect import flow, task, get_run_logger
from datetime import datetime, timedelta
import argparse
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data-gen')))
from config import POSTGRES_CONFIG

MLFLOW_TRACKING_URI = "http://localhost:5000"  # Change if using remote MLflow server
MLFLOW_EXPERIMENT = "badminton_score_regression"
MLFLOW_MODEL_NAME = "badminton_rf_regressor"

@task
def load_data_from_postgres(start_date, end_date):
    logger = get_run_logger()
    cfg = POSTGRES_CONFIG
    db_url = f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    engine = create_engine(db_url)
    query = f"""
        SELECT shot_type, landing_position_x, landing_position_y, shuttle_speed_kmh, score, timestamp
        FROM {cfg['table']}
        WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}'
    """
    df = pd.read_sql(query, engine)
    logger.info(f"Loaded {len(df)} rows from PostgreSQL between {start_date} and {end_date}.")
    logger.info(f"Columns loaded: {list(df.columns)}")
    return df

@task
def preprocess_data(df):
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    X_cat = encoder.fit_transform(df[['shot_type']])
    cat_feature_names = encoder.get_feature_names_out(['shot_type'])
    X_num = df[['landing_position_x', 'landing_position_y', 'shuttle_speed_kmh']].values
    X = np.hstack([X_cat, X_num])
    feature_names = list(cat_feature_names) + ['landing_position_x', 'landing_position_y', 'shuttle_speed_kmh']
    y = df['score'].values
    return X, y, feature_names, encoder

@task
def train_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    return model, mse, r2

@task
def log_to_mlflow(model, mse, r2, feature_names, encoder, start_date, end_date):
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)
    with mlflow.start_run():
        mlflow.log_param("model_type", "RandomForestRegressor")
        mlflow.log_param("start_date", start_date)
        mlflow.log_param("end_date", end_date)
        mlflow.log_metric("mse", mse)
        mlflow.log_metric("r2", r2)
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name=MLFLOW_MODEL_NAME
        )
        # Save encoder as artifact
        import joblib
        encoder_path = "encoder.joblib"
        joblib.dump(encoder, encoder_path)
        mlflow.log_artifact(encoder_path)
        print(f"Logged to MLflow: MSE={mse:.4f}, R2={r2:.4f}, model registered as {MLFLOW_MODEL_NAME}")

@flow(name="Badminton ML Training Pipeline")
def badminton_training_pipeline(start_date: str, end_date: str):
    logger = get_run_logger()
    df = load_data_from_postgres(start_date, end_date)
    if df.empty:
        logger.warning("No data found for the given date range.")
        return
    X, y, feature_names, encoder = preprocess_data(df)
    model, mse, r2 = train_model(X, y)
    log_to_mlflow(model, mse, r2, feature_names, encoder, start_date, end_date)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Badminton ML Training Pipeline")
    parser.add_argument('--start_date', type=str, required=False, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, required=False, help='End date (YYYY-MM-DD)')
    args = parser.parse_args()

    # Default: last 7 days
    now = datetime.now()
    default_end = now.strftime('%Y-%m-%d %H:%M:%S')
    default_start = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    start_date = args.start_date if args.start_date else default_start
    end_date = args.end_date if args.end_date else default_end

    badminton_training_pipeline(start_date, end_date) 