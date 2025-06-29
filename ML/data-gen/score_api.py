from flask import Flask, request, jsonify
import mlflow.pyfunc
import mlflow.sklearn
import joblib
import numpy as np
import os
import pandas as pd
from sqlalchemy import create_engine, text

# Configuration
MLFLOW_TRACKING_URI = "http://localhost:5000"
MLFLOW_MODEL_NAME = "badminton_rf_regressor"
# Since the model is not automatically promoted, load the latest version
MLFLOW_MODEL_STAGE = None  # None means load latest version

# Initialize Flask app
app = Flask(__name__)

# Load model and encoder from MLflow
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
from mlflow.tracking import MlflowClient
client = mlflow.tracking.MlflowClient()

if MLFLOW_MODEL_STAGE:
    model_uri = f"models:/{MLFLOW_MODEL_NAME}/{MLFLOW_MODEL_STAGE}"
    latest_run = client.get_latest_versions(MLFLOW_MODEL_NAME, [MLFLOW_MODEL_STAGE])[0].run_id
else:
    # Get latest version
    versions = client.get_latest_versions(MLFLOW_MODEL_NAME, stages=None)
    if not versions:
        raise Exception(f"No versions found for model {MLFLOW_MODEL_NAME}")
    latest_version = max(versions, key=lambda v: int(v.version))
    model_uri = f"models:/{MLFLOW_MODEL_NAME}/{latest_version.version}"
    latest_run = latest_version.run_id

model = mlflow.sklearn.load_model(model_uri)

# Find and load the encoder artifact
artifacts = client.list_artifacts(latest_run)
encoder_path = None
for artifact in artifacts:
    if artifact.path == "encoder.joblib":
        encoder_path = client.download_artifacts(latest_run, "encoder.joblib")
        break
if encoder_path is None:
    raise FileNotFoundError("encoder.joblib not found in MLflow artifacts.")
encoder = joblib.load(encoder_path)

# Get feature order from encoder
cat_feature_names = encoder.get_feature_names_out(['shot_type'])
feature_names = list(cat_feature_names) + ['landing_position_x', 'landing_position_y', 'shuttle_speed_kmh']

# Add PostgreSQL config (reuse from config.py if available, else hardcode here)
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'badminton_db',
    'user': 'postgres',
    'password': '',
    'table': 'badminton_shots_predicted'
}

def get_db_engine():
    cfg = POSTGRES_CONFIG
    db_url = f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    return create_engine(db_url)

@app.route('/predict_score', methods=['POST'])
def predict_score():
    data = request.get_json()
    # Validate input
    required_fields = ['shot_type', 'landing_position_x', 'landing_position_y', 'shuttle_speed_kmh']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    # Prepare input for model
    shot_type = data['shot_type']
    landing_position_x = float(data['landing_position_x'])
    landing_position_y = float(data['landing_position_y'])
    shuttle_speed_kmh = float(data['shuttle_speed_kmh'])
    # One-hot encode shot_type
    X_cat = encoder.transform([[shot_type]])
    X_num = np.array([[landing_position_x, landing_position_y, shuttle_speed_kmh]])
    X = np.hstack([X_cat, X_num])
    # Predict
    score = model.predict(X)[0]
    return jsonify({'predicted_score': float(score)})

@app.route('/save_shot', methods=['POST'])
def save_shot():
    data = request.get_json()
    required_fields = [
        'user_id', 'user_name', 'user_skill_level', 'timestamp', 'shot_type',
        'landing_position_x', 'landing_position_y', 'shuttle_speed_kmh', 'score', 'score_type'
    ]
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    # Prepare data for insertion
    insert_data = {field: data[field] for field in required_fields}
    # Insert into PostgreSQL
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            columns = ', '.join(insert_data.keys())
            placeholders = ', '.join([f':{k}' for k in insert_data.keys()])
            sql = f"INSERT INTO {POSTGRES_CONFIG['table']} ({columns}) VALUES ({placeholders})"
            print(f"SQL: {sql}")
            print(f"Data: {insert_data}")
            conn.execute(text(sql), insert_data)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Error saving shot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Badminton Skill Score API is running.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9290) 