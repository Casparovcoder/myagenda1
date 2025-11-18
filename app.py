from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Tijdelijke opslag (later kun je dit koppelen aan Google Calendar of Zapier)
events = []

@app.route('/create-event', methods=['POST'])
def create_event():
    data = request.json
    titel = data.get('titel')
    starttijd = data.get('starttijd')
    eindtijd = data.get('eindtijd')

    if not all([titel, starttijd, eindtijd]):
        return jsonify({"error": "titel, starttijd en eindtijd zijn verplicht"}), 400

    event = {
        "titel": titel,
        "starttijd": starttijd,
        "eindtijd": eindtijd
    }
    events.append(event)
    bevestiging = f"Aangemaakt: {starttijd}–{eindtijd} ‘{titel}’."
    return jsonify({"bevestiging": bevestiging})

@app.route('/list-events', methods=['GET'])
def list_events():
    datum = request.args.get('datum')
    aantal = int(request.args.get('aantal', 10))
    if not datum:
        return jsonify({"error": "datum is verplicht"}), 400
    filtered = [e for e in events if datum in e['starttijd']]
    return jsonify({"events": filtered[:aantal]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
