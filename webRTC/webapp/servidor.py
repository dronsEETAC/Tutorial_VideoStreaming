# signaling_server.py
from flask import Flask, render_template, request, jsonify
import uuid
from aiortc import RTCPeerConnection, RTCSessionDescription
import asyncio

app = Flask(__name__)

pcs = {}  # session_id -> RTCPeerConnection

@app.route("/")
def index():
    return render_template("indexWebAppMQTT.html")

@app.route("/offer", methods=["POST"])
def offer():
    """
    Recibe SDP offer del cliente y devuelve la respuesta (answer)
    """
    data = request.json
    sdp = data["sdp"]
    type_ = data["type"]

    pc = RTCPeerConnection()
    session_id = str(uuid.uuid4())
    pcs[session_id] = pc

    # Creamos un track de video (emisor ya lo tiene)
    # En este ejemplo asumimos que el emisor Python ya captura y envía el track
    # Para recibir video del emisor remoto, aiortc en Python se encarga de reenviar

    async def run_offer():
        offer = RTCSessionDescription(sdp, type_)
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        return pc.localDescription

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    local_desc = loop.run_until_complete(run_offer())

    return jsonify({"sdp": local_desc.sdp, "type": local_desc.type, "session_id": session_id})

@app.route("/candidate", methods=["POST"])
def candidate():
    # Por simplicidad, omitimos implementación detallada de ICE candidates
    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8107)
