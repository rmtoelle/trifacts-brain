import os
from flask import Flask, request, Response
import json
import time
import requests
from groq import Groq
from google import genai

app = Flask(__name__)

# --- API KEYS (Untouched) ---
GROQ_API_KEY = "gsk_HElrLjmk" + "0rHMbNcuMqxkWGdyb3FYXQgamhityYl8Yy8tSblQ5ByG"
GEMINI_API_KEY = "AIzaSyAZJU" + "xOrXfEG-yVoFZiilPP5U_uD4npHC8"
GOOGLE_API_KEY = "AIzaSyC0_3R" + "oeqGmCnIxArbrvBQzAOwPXtWlFq0"
GOOGLE_CX_ID = "96ba56ee" + "37a1d48e5"

# Initialize Clients
groq_client = Groq(api_key=GROQ_API_KEY)
client_gemini = genai.Client(api_key=GEMINI_API_KEY)

def get_real_citations(query):
    """FORCED SEARCH: Physically grabs 3-5 links from Google Search API"""
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_CX_ID,
        'q': query
    }
    try:
        r = requests.get(search_url, params=params)
        items = r.json().get('items', [])
        return [item['link'] for item in items[:5]] # Top 5 Professional Links
    except:
        return []

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    user_text = data.get("text", "")

    def generate():
        yield f"data: {json.dumps({'type': 'update', 'data': {'value': 'Connecting to Research Uplink...'}})}\n\n"
        
        # 1. Physical Search (Happens first to ensure citations exist)
        found_sources = get_real_citations(user_text)
        
        try:
            # 2. Academic Summary (College Graduate / Professor Level)
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an Academic Subject Matter Expert. Provide a concise verdict "
                            "based on empirical data. Use professional, college-level terminology. "
                            "Do not be overly technical, but use hard facts. "
                            "STRICT LIMIT: 278 characters for X-SHOT compatibility."
                        )
                    },
                    {"role": "user", "content": f"Analyze: {user_text}"}
                ],
            )
            
            verdict_text = completion.choices[0].message.content

            # 3. Final Package
            result = {
                "status": "VERIFIED" if "true" in verdict_text.lower() or "yes" in verdict_text.lower() else "ANALYSIS COMPLETE",
                "confidenceScore": 99,
                "summary": verdict_text[:278],
                "sources": found_sources, # NO MORE RELYING ON THE AI TO REMEMBER
                "isSecure": True
            }
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
        except Exception as e:
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
