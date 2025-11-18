from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import os
import requests

app = Flask(__name__)

# Tijdelijke opslag (optioneel)
events = []

# 🔹 Zet je Google API-gegevens als environment variables in Render!
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
GOOGLE_API_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def get_access_token():
    """Haal een nieuw access token op via het refresh token"""
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": GOOGLE_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    response = requests.post(GOOGLE_TOKEN_URL, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        app.logger.error(f"Fout bij token ophalen: {response.text}")
        return None


@app.route('/create-event', methods=['POST'])
def create_event():
    data = request.json
    titel = data.get('titel')
    starttijd = data.get('starttijd')
    eindtijd = data.get('eindtijd')

    if not all([titel, starttijd, eindtijd]):
        return jsonify({"error": "titel, starttijd en eindtijd zijn verplicht"}), 400

    # Voeg toe aan lokale lijst
    event = {"titel": titel, "starttijd": starttijd, "eindtijd": eindtijd}
    events.append(event)

    # 🔹 Verstuur naar Google Calendar
    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Kon geen Google access token ophalen"}), 500

    google_event = {
        "summary": titel,
        "start": {"dateTime": starttijd, "timeZone": "Europe/Amsterdam"},
        "end": {"dateTime": eindtijd, "timeZone": "Europe/Amsterdam"}
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(GOOGLE_API_URL, headers=headers, json=google_event)
    if response.status_code in (200, 201):
        g_data = response.json()
        bevestiging = f"Aangemaakt in Google Agenda: {titel} ({starttijd} – {eindtijd})"
        return jsonify({"bevestiging": bevestiging, "google_link": g_data.get("htmlLink")})
    else:
        app.logger.error(f"Google API-fout: {response.text}")
        return jsonify({"error": "Kon event niet toevoegen aan Google Agenda", "details": response.text}), 500


@app.route('/list-events', methods=['GET'])
def list_events():
    datum = request.args.get('datum')
    aantal = int(request.args.get('aantal', 10))
    if not datum:
        return jsonify({"error": "datum is verplicht"}), 400
    filtered = [e for e in events if datum in e['starttijd']]
    return jsonify({"events": filtered[:aantal]})


@app.route('/openapi.yaml', methods=['GET'])
def serve_openapi():
    """Serve the OpenAPI specification file"""
    return send_from_directory(os.getcwd(), 'openapi.yaml')


@app.route('/')
def home():
    return "MY AIGENDA API draait ✅ (met Google Calendar integratie)"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
