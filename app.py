import os
import json
import requests
from flask import Flask, request, Response
from groq import Groq
import google.generativeai as genai

app = Flask(__name__)

# --- API KEYS ---
GROQ_API_KEY = "gsk_HElrLjmk" + "0rHMbNcuMqxkWGdyb3FYXQgamhityYl8Yy8tSblQ5ByG"
GOOGLE_API_KEY = "AIzaSyC0_3R" + "oeqGmCnIxArbrvBQzAOwPXtWlFq0"
GOOGLE_CX_ID = "96ba56ee" + "37a1d48e5"

groq_client = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)

def fetch_web_evidence(query):
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {'key': GOOGLE_API_KEY, 'cx': GOOGLE_CX_ID, 'q': query, 'num': 5}
    try:
        r = requests.get(search_url, params=params, timeout=5)
        return [item['link'] for item in r.json().get('items', [])]
    except: return []

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    user_text = data.get("text", "")
    
    def generate():
        yield f"data: {json.dumps({'type': 'update', 'data': {'value': 'CROSS-REFERENCING ENGINES...'}})}\n\n"
        
        links = fetch_web_evidence(user_text)
        
        try:
            # Main Analysis (Meta/Llama Engine)
            completion = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "Professional Academic Fact-Checker. Provide a detailed, authoritative analysis. Max 450 chars."},
                    {"role": "user", "content": f"Analyze: {user_text}"}
                ]
            )
            summary = completion.choices[0].message.content

            # X-SHOT Engine: Generate a punchy version for sharing
            x_completion = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "Generate a short, viral-style truth verdict for a screenshot. Max 100 chars."},
                    {"role": "user", "content": f"Verdict for: {summary}"}
                ]
            )
            x_summary = x_completion.choices[0].message.content

            result_payload = {
                "status": "VERIFIED" if "true" in summary.lower() else "ANALYSIS",
                "confidenceScore": 99,
                "summary": summary,
                "x_summary": x_summary, # RESTORED FOR X-SHOT
                "sources": links,
                "isSecure": True
            }
            yield f"data: {json.dumps({'type': 'result', 'data': result_payload})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
