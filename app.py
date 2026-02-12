import os
from flask import Flask, request, Response
import json
import requests

app = Flask(__name__)

# --- API KEYS (Isolated for Troubleshooting) ---
GOOGLE_API_KEY = "AIzaSyC0_3R" + "oeqGmCnIxArbrvBQzAOwPXtWlFq0"
GOOGLE_CX_ID = "96ba56ee" + "37a1d48e5"

def fetch_google_citations(query):
    """STEP 1: Test only the Google Citation Pipe"""
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {'key': GOOGLE_API_KEY, 'cx': GOOGLE_CX_ID, 'q': query}
    try:
        r = requests.get(search_url, params=params, timeout=5)
        # We physically grab the links here
        items = r.json().get('items', [])
        links = [item['link'] for item in items[:4]]
        print(f"DEBUG: Found {len(links)} links")
        return links
    except Exception as e:
        print(f"DEBUG: Google API Error: {e}")
        return []

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    user_text = data.get("text", "")

    def generate():
        # INITIAL PULSE: Tells the app the server is alive
        yield f"data: {json.dumps({'type': 'update', 'data': {'value': 'CHECKING GOOGLE ENGINE...'}})}\n\n"
        
        # ACTION: Grab the links
        links = fetch_google_citations(user_text)
        
        # TROUBLESHOOTING PAYLOAD: 
        # We send a fake summary just to see if the SOURCES list populates the UI.
        result_payload = {
            "status": "TEST MODE",
            "confidenceScore": 100,
            "summary": f"TROUBLESHOOTING STEP 1: If you see links below, the Google Pipe is working for query: {user_text}",
            "sources": links, # THIS IS WHAT WE ARE TESTING
            "isSecure": True
        }
        
        # Send the final 'result' packet
        yield f"data: {json.dumps({'type': 'result', 'data': result_payload})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
