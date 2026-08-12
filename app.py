import os
import requests
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

system_prompt = """
Actuá como "Santi", el asistente virtual inteligente de la concesionaria. Tu objetivo es calificar al usuario rápidamente y agendar una llamada con un asesor humano.
Sos un asesor argentino moderno: usá el "vos" de forma natural. Sé cordial, directo y muy entusiasta.
Hacé solo una pregunta por mensaje. Máximo un emoji por mensaje. Nunca des precios exactos.
"""

conversations = {}

@app.route("/", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', 'default_user')
    
    if sender not in conversations:
        conversations[sender] = []
        
    conversations[sender].append({"role": "user", "content": incoming_msg})
    
    if len(conversations[sender]) > 10:
        conversations[sender] = conversations[sender][-10:]
    
    messages = [{"role": "system", "content": system_prompt}] + conversations[sender]
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.7
    }
    
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        res_json = response.json()
        
        if "error" in res_json:
            bot_reply = "¡Hola! ¿En qué modelo de auto estás pensando hoy? 🚗"
        else:
            bot_reply = res_json['choices'][0]['message']['content']
    except Exception:
        bot_reply = "¡Hola! Contame, qué tipo de auto estás buscando? 🚗"

    conversations[sender].append({"role": "assistant", "content": bot_reply})

    resp = MessagingResponse()
    resp.message(bot_reply)
    
    return Response(str(resp), mimetype='application/xml')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
