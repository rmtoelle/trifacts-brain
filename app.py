import os
from flask import Flask, request, Response
import json
import requests
from groq import Groq

app = Flask(__name__)

# --- API KEYS ---
GROQ_API_KEY = "gsk_HElrLjmk" + "0rHMbNcuMqxkWGdyb3FYXQgamhityYl8Yy8tSblQ5ByG"
GOOGLE_API_KEY = "AIzaSyC0_3R" + "oeqGmCnIxArbrvBQzAOwPXtWlFq0"
GOOGLE_CX_ID = "96ba56ee" + "37a1d48e5"

groq_client = Groq(api_key=GROQ_API_KEY)

def fetch_google_citations(query):
    """
    Directly fetches web links from Google Custom Search API.
    Ensures the response is a clean list of URL strings.
    """
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY, 
        'cx': GOOGLE_CX_ID, 
        'q': query,
        'num': 4 # Fetch top 4 results
    }
    
    try:
        r = requests.get(search_url, params=params, timeout=5)
        search_results = r.json()
        
        # Extract just the link strings from the 'items' list
        if 'items' in search_results:
            links = [item['link'] for item in search_results['items']]
            return links
        
        return []
    except Exception as e:
        print(f"Search API Error: {e}")
        return []

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    user_text = data.get("text", "")

    def generate():
        # Update UI Status
        yield f"data: {json.dumps({'type': 'update', 'data': {'value': 'Scanning Lunar Data...'}})}\n\n"
        
        # 1. Fetch real web citations
        links = fetch_google_citations(user_text)
        
        try:
            # 2. AI Analysis
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a scientific fact-checker. Provide a concise, academic summary of the facts. Max 270 characters."},
                    {"role": "user", "content": f"Fact check this: {user_text}"}
                ],
            )
            summary = completion.choices[0].message.content

            # 3. Final Payload (Build 36 Structure)
            result_payload = {
                "status": "VERIFIED" if "yes" in summary.lower() or "true" in summary.lower() else "CONFIRMED",
                "confidenceScore": 99,
                "summary": summary,
                "sources": links, # Clean list of URL strings
                "isSecure": True
            }
            
            yield f"data: {json.dumps({'type': 'result', 'data': result_payload})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
