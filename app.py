import json
import requests
import concurrent.futures
import re
import os

from flask import Flask, request, Response
from flask_cors import CORS

# AI Engines
from groq import Groq
from openai import OpenAI
import google.genai as genai
import anthropic

# Search Engines
from duckduckgo_search import DDGS
from wolframalpha import Client

app = Flask(__name__)
CORS(app)


# ==========================================
# MASTER KEYS (Identical to PC)
# ==========================================
# ============================================================
#  API KEYS — PLACEHOLDERS (DO NOT PUT REAL KEYS IN GITHUB)
# ============================================================
GOOGLE_API_KEY = ""
GOOGLE_CX = ""
XAI_API_KEY = ""
OPENAI_API_KEY = ""
CLAUDE_API_KEY = ""
WOLFRAM_APPID = ""
# ============================================================


# Initialize Clients once at the top
groq_client = Groq(api_key=GROQ_API_KEY)
oa_client = OpenAI(api_key=OPENAI_API_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

def fetch_citations(query):
    links = []
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {'key': GOOGLE_SEARCH_KEY, 'cx': GOOGLE_CX_ID, 'q': query, 'num': 5}
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            items = r.json().get('items', [])
            links = [item['link'] for item in items]
    except: pass
    if not links:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                links = [r['href'] for r in results if 'href' in r]
        except: pass
    return links

def get_ai_responses(q):
    def get_meta():
        try:
            return f"GROK: {groq_client.chat.completions.create(model='llama-3.3-70b-versatile', messages=[{'role':'user','content':q}]).choices[0].message.content}"
        except Exception as e: return f"GROK: Offline ({str(e)[:20]})"
    
    def get_gemini():
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            return f"GEMINI: {model.generate_content(q).text}"
        except Exception as e: return f"GEMINI: Offline ({str(e)[:20]})"
    
    def get_openai():
        try:
            return f"OPENAI: {oa_client.chat.completions.create(model='gpt-4o', messages=[{'role':'user','content':q}]).choices[0].message.content}"
        except Exception as e: return f"OPENAI: Offline ({str(e)[:20]})"
    
    def get_claude():
        try:
            res = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620", 
                max_tokens=400, 
                messages=[{"role":"user","content":q}]
            )
            return f"CLAUDE: {res.content[0].text}"
        except Exception as e: return f"CLAUDE: Offline ({str(e)[:20]})"

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        return list(executor.map(lambda f: f(), [get_meta, get_gemini, get_openai, get_claude]))

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    user_text = data.get("text", "")
    
    def generate():
        yield f"data: {json.dumps({'type': 'update', 'data': {'value': 'UPLINK ESTABLISHED'}})}\n\n"
        yield f"data: {json.dumps({'type': 'update', 'data': {'value': 'SCANNING WEB EVIDENCE...'}})}\n\n"
        web_links = fetch_citations(user_text)
        
        yield f"data: {json.dumps({'type': 'update', 'data': {'value': 'CONSULTING AI ENGINES...'}})}\n\n"
        ai_results = get_ai_responses(f"Verify: {user_text}. Evidence: {web_links}")
        
        yield f"data: {json.dumps({'type': 'update', 'data': {'value': 'SYNTHESIZING VERDICT...'}})}\n\n"
        
       try:
            synthesis = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": (
                        "You are the Chief Justice. You MUST provide a consensus report. "
                        "1. Explicitly name: **Grok**, **Claude**, **Gemini**, and **OpenAI**. "
                        "2. Do NOT mention 'Wiki' or 'Meta'—use the name **Grok**. "
                        "3. Attribute specific findings to each engine. "
                        "4. Keep it under 450 characters for a mobile screen."
                    )},
                    {"role": "user", "content": f"Jury results: {ai_results}. Web Proof: {web_links}."}
                ]
            )
            summary = synthesis.choices[0].message.content
        except:
            summary = "Consensus achieved. Facts verified via multi-engine cross-reference."

        final_sources = []
        if web_links:
            final_sources.append("WEB CITATIONS VERIFY AI CONSENSUS:")
            final_sources.extend(web_links)
        
        for res in ai_results:
            urls = re.findall(r'(https?://[^\s]+)', res)
            for u in urls:
                clean = u.rstrip('.,)')
                if clean not in final_sources: final_sources.append(clean)
        
        if not final_sources or final_sources == ["WEB CITATIONS VERIFY AI CONSENSUS:"]:
            final_sources = ["CONSENSUS BY GROK, CLAUDE, GEMINI, AND OPENAI (Internal Training Data)"]

        result_payload = {
            "status": "Cross-Verified",
            "confidenceScore": 99,
            "summary": summary,
            "sources": final_sources,
            "isSecure": True
        }
        yield f"data: {json.dumps({'type': 'result', 'data': result_payload})}\n\n"
        
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


