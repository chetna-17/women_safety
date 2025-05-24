from flask import Flask, request, jsonify,send_file
import pandas as pd
import os
import joblib
from datetime import datetime
from flask_cors import CORS
import folium

app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)

LOG_FILE = "panic_alerts_log.csv"
MODEL_FILE = "model.pkl"
FEATURES_FILE = "model_features.csv"

# Load ML Model & Features
try:
    clf = joblib.load(MODEL_FILE)
    print("✅ Model loaded.")
except Exception as e:
    print("❌ Error loading model:", e)
    clf = None

try:
    X_template = pd.read_csv(FEATURES_FILE)
    print("✅ Feature columns loaded.")
except Exception as e:
    print("❌ Error loading features:", e)
    X_template = pd.DataFrame()

@app.route('/')
def index():
    # Serve your static panic_form.html
    return app.send_static_file('panic_form.html')

@app.route('/submit', methods=['POST'])
def submit_alert():
    print("📥 Received POST request...")

    try:
        data = request.get_json()
        print("🧾 JSON received:", data)

        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400

        lat = data.get('lat')
        lon = data.get('lon')
        incident_type = data.get('incident_type')

        if not all([lat, lon, incident_type]):
            return jsonify({'status': 'error', 'message': 'Incomplete data'}), 400

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Prediction Logic
        outcome_text = "N/A"
        probability = "N/A"
        if clf and not X_template.empty:
            input_df = pd.DataFrame(columns=X_template.columns)
            input_df.loc[0] = [0] * len(X_template.columns)
            input_df.at[0, 'Latitude'] = float(lat)
            input_df.at[0, 'Longitude'] = float(lon)

            incident_col = f"Incident Type_{incident_type}"
            if incident_col in input_df.columns:
                input_df.at[0, incident_col] = 1

            try:
                prob = clf.predict_proba(input_df)[0][1]
                result = clf.predict(input_df)[0]
                outcome_text = 'Unresolved/In Progress' if result == 1 else 'Resolved'
                probability = round(prob, 2)
            except Exception as e:
                print("⚠️ Prediction failed:", e)

        # Append to CSV
        new_entry = pd.DataFrame([{
            'Latitude': lat,
            'Longitude': lon,
            'Incident Type': incident_type,
            'Timestamp': timestamp,
            'Predicted Outcome': outcome_text,
            'Probability': probability
        }])

        if os.path.exists(LOG_FILE):
            new_entry.to_csv(LOG_FILE, mode='a', index=False, header=False)
        else:
            new_entry.to_csv(LOG_FILE, index=False)

        print("✅ CSV write done.")

        # Update Map
        m = folium.Map(location=[float(lat), float(lon)], zoom_start=14)
        popup_content = (
            f"📍 Incident: {incident_type}<br>"
            f"🕒 {timestamp}<br>"
            f"🔮 Outcome: {outcome_text}<br>"
            f"📊 Probability: {probability}"
        )
        folium.Marker(
            location=[float(lat), float(lon)],
            popup=popup_content,
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)
        m.save("latest_alert_map.html")
        print("🗺️ Map saved as latest_alert_map.html")

        return jsonify({'status': 'success', 'message': 'Alert received'}), 200

    except Exception as e:
        print("💥 Exception occurred:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    from flask import send_file

@app.route('/map')
def view_map():
    map_path = "latest_alert_map.html"
    if os.path.exists(map_path):
        return send_file(map_path)
    else:
        return "<h3>No map available yet.</h3>", 404


if __name__ == '__main__':
    app.run(debug=True)
