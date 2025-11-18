from flask import Flask, request, jsonify, send_from_directory, Response
from datetime import datetime
import os
import uuid
import json

app = Flask(__name__)

DATA_FILE = "events.json"

# 🔹 Laad bestaande afspraken bij het opstarten
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        events = json.load(f)
else:
    events = []


def save_events():
    """Sla events permanent op in JSON-bestand."""
    with open(DATA_FILE, "w") as f:
        json.dump(events, f, indent=2)


@app.route('/create-event', methods=['POST'])
def create_event():
    """
    Ontvangt een nieuw event en slaat het op.
    Wordt ook automatisch zichtbaar in de ICS-feed (/calendar.ics)
    """
    data = request.json
    titel = data.get('titel')
    starttijd = data.get('starttijd')
    eindtijd = data.get('eindtijd')

    if not all([titel, starttijd, eindtijd]):
        return jsonify({"error": "titel, starttijd en eindtijd zijn verplicht"}), 400

    event_id = str(uuid.uuid4())

    event = {
        "id": event_id,
        "titel": titel,
        "starttijd": starttijd,
        "eindtijd": eindtijd
    }

    events.append(event)
    save_events()  # 🔹 Bewaar in JSON

    bevestiging = f"Aangemaakt: {starttijd}–{eindtijd} ‘{titel}’."
    return jsonify({"bevestiging": bevestiging})


@app.route('/list-events', methods=['GET'])
def list_events():
    """
    Haal een lijst met afspraken op voor een specifieke datum.
    """
    datum = request.args.get('datum')
    aantal = int(request.args.get('aantal', 10))
    if not datum:
        return jsonify({"error": "datum is verplicht"}), 400

    filtered = [e for e in events if datum in e['starttijd']]
    return jsonify({"events": filtered[:aantal]})


@app.route('/calendar.ics', methods=['GET'])
def serve_ics():
    """
    Genereert dynamische ICS-feed van alle opgeslagen events.
    Google haalt deze automatisch op via de URL:
    https://myagenda1.onrender.com/calendar.ics
    """
    ics_events = []
    for e in events:
        start = e['starttijd'].replace("-", "").replace(":", "").replace("T", "T")
        end = e['eindtijd'].replace("-", "").replace(":", "").replace("T", "T")

        ics_events.append(f"""BEGIN:VEVENT
UID:{e['id']}@myagenda1.onrender.com
SUMMARY:{e['titel']}
DTSTART:{start}
DTEND:{end}
DTSTAMP:{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}
END:VEVENT""")

    ics_content = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//MY AIGENDA//EN\n"
        + "\n".join(ics_events)
        + "\nEND:VCALENDAR"
    )
    return Response(ics_content, mimetype='text/calendar')


@app.route('/openapi.yaml', methods=['GET'])
def serve_openapi():
    """Serve het OpenAPI-specificatiebestand."""
    return send_from_directory(os.getcwd(), 'openapi.yaml')


@app.route('/')
def home():
    """Simpele homepage met uitleg."""
    return """
    <h1>MY AIGENDA API draait ✅</h1>
    <p>Gebruik deze endpoints:</p>
    <ul>
        <li><code>POST /create-event</code> – maak een nieuwe afspraak aan</li>
        <li><code>GET /list-events?datum=YYYY-MM-DD</code> – toon afspraken</li>
        <li><code>GET /calendar.ics</code> – ICS-feed voor Google Agenda</li>
        <li><code>GET /openapi.yaml</code> – OpenAPI-specificatie</li>
    </ul>
    <p>ℹ️ Voeg <b>https://myagenda1.onrender.com/calendar.ics</b> toe in Google Agenda via “Agenda toevoegen via URL”.</p>
    <p>📦 Alle afspraken worden opgeslagen in <code>events.json</code>, zodat ze behouden blijven bij herstart.</p>
    """


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
