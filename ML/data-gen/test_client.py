import requests

url = "http://localhost:8080/predict_score"
payload = {
    "shot_type": "smash",
    "landing_position_x": 7.5,
    "landing_position_y": 3.0,
    "shuttle_speed_kmh": 90
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    print("Predicted score:", response.json()["predicted_score"])
else:
    print("Error:", response.status_code, response.text) 