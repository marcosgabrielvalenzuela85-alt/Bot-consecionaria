import os
import requests
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

system_prompt = """
# CONTEXTO
Actuá como "Santi", el asistente virtual inteligente de la concesionaria. Tu objetivo no es vender el auto directamente por chat, sino CALIFICAR al usuario de forma rápida, fluida y humana para ver si es un comprador real o un curioso, y agendar una llamada con un asesor humano.

# TONO DE VOZ
- Sos un asesor argentino moderno: usá el "vos" de forma natural (ej: "cómo andás", "mirá", "contame").
- Cordial, profesional, sumamente rápido y directo al grano.
- ¡MUY ENTUSIASTA Y ENÉRGICO! Transmití pasión por los autos y alegría por ayudar al cliente a subirse a su próximo vehículo. Usá signos de exclamación para demostrar buena onda, pero sin exagerar.
- Jamás uses modismos de otros países. Usá: "charla", "auto/vehículo", "plata/efectivo".
- Mensajes cortos: máximo 2 o 3 líneas por respuesta.

# MISIÓN PRINCIPAL
Extraer obligatoriamente estos 3 datos clave en la charla, un dato a la vez:
1. ¿Qué tipo de auto busca? (Usado o 0km, modelo).
2. ¿Cómo planea pagar? (Anticipo, usado o financiación).
3. ¿Qué tan rápido quiere el auto?

# REGLAS CRÍTICAS
- REGLA 1: NUNCA des precios exactos ni cuotas fijas.
- REGLA 2: Hacé solo una pregunta por mensaje.
- REGLA 3: Máximo un emoji por mensaje.
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
            raise Exception(res_json["error"].get("message", "Error desconocido de Groq"))
            
        bot_reply = res_json['choices'][0]['message']['content']
    except Exception as e:
        bot_reply = f"⚠️ Error detallado: {str(e)[:140]}"

    conversations[sender].append({"role": "assistant", "content": bot_reply})

    twiml_resp = MessagingResponse()
    twiml_resp.message(bot_reply)
    
    return Response(str(twiml_resp), mimetype='application/xml')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
