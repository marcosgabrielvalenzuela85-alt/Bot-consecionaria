import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests

app = Flask(__name__)

# Lee la clave de forma segura desde la nube
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

conversations = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "default")
    
    system_prompt = (
        "Eres un asesor de ventas estrella, súper entusiasta, carismático y apasionado por los autos en una concesionaria exclusiva. "
        "Usa emojis con moderación para darle vida a los mensajes, celebra las elecciones del cliente y haz que la charla se sienta cálida, humana y emocionante, nunca como un formulario frío.\n"
        "Tu objetivo es guiar la conversación con energía positiva para conocer de forma natural y fluida:\n"
        "   - El nombre del cliente\n"
        "   - Qué busca (0km o usado) y qué modelo le enamora\n"
        "   - Su plan financiero (contado o financiación cómoda)\n"
        "   - Su ubicación (ciudad o zona)\n"
        "   - Su contacto preferido\n"
        "REGLA DE ORO: Mantén los mensajes cortos (máximo 2 o 3 oraciones), sé muy amigable, celebra sus gustos y haz solo una pregunta a la vez."
    )
    
    if sender not in conversations:
        conversations[sender] = [
            {"role": "system", "content": system_prompt}
        ]
    
    conversations[sender].append({"role": "user", "content": incoming_msg})
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": conversations[sender]
    }
    
    ai_reply = "¡Hola! 🚗 ¡Qué alegría tenerte por aquí en nuestra concesionaria! ¿Estás buscando algún modelo en particular, 0km o usado?"
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            ai_reply = data["choices"][0]["message"]["content"]
            conversations[sender].append({"role": "assistant", "content": ai_reply})
        elif "error" in data:
            ai_reply = f"Error de Groq: {data['error'].get('message', 'Desconocido')}"
    except Exception as e:
        print("Error:", e)

    twilio_resp = MessagingResponse()
    twilio_resp.message(ai_reply)
    return str(twilio_resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

