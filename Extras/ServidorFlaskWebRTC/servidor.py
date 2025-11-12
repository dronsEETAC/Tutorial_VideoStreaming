# Path: ./app.py
"""
Flask + aiortc: Stream de cámara real del servidor vía WebRTC (versión estable)
"""

import asyncio
import logging
import os
import cv2
import time

from flask import Flask, render_template, request, jsonify
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
import av

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flask-webrtc-camera")

app = Flask(__name__, template_folder="templates")

# --- Video Track usando la cámara física ---
class CameraVideoTrack(VideoStreamTrack):
    """
    StreamTrack que captura frames desde la cámara local (OpenCV)
    """
    def __init__(self, camera_index=0):
        super().__init__()
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la cámara {camera_index}")
        self.start_time = time.monotonic()
        self.frame_index = 0
        self.fps = 30
        # si quiero enviar una foto como stream de video
        self.imagen = cv2.imread("dronLab.png")

    async def recv(self):
        # Esperar para mantener ritmo de FPS
        await asyncio.sleep(1 / self.fps)
        ret, frame = self.cap.read()

        if not ret:
            raise RuntimeError("Error leyendo frame de cámara")
        # si quiero enviar la foto
        #frame = self.imagen
        # Convertir BGR (OpenCV) -> RGB (aiortc)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Calcular timestamp
        now = time.monotonic()
        pts = int((now - self.start_time) * self.fps)

        from fractions import Fraction
        time_base = Fraction(1, self.fps)

        # Crear frame para aiortc
        video_frame = av.VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base

        self.frame_index += 1
        return video_frame

    async def stop(self):
        self.cap.release()
        await super().stop()


# --- WebRTC + Flask integration ---
pcs = set()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route("/")
def index():
    return render_template("indexWebAppWebRTC.html")

@app.route("/offer", methods=["POST"])
def offer():
    params = request.get_json()
    if not params or "sdp" not in params:
        return jsonify({"error": "missing sdp"}), 400

    offer_sdp = params["sdp"]
    offer_type = params.get("type", "offer")

    future = asyncio.run_coroutine_threadsafe(handle_offer(offer_sdp, offer_type), loop)
    answer = future.result()
    return jsonify(answer)

async def handle_offer(offer_sdp, offer_type):
    pc = RTCPeerConnection()
    pcs.add(pc)
    logger.info("PeerConnection creada: %s", id(pc))

    @pc.on("connectionstatechange")
    async def on_state_change():
        logger.info("Estado conexión: %s", pc.connectionState)
        if pc.connectionState in ["failed", "closed"]:
            await pc.close()
            pcs.discard(pc)

    # Añadir la cámara real
    video_track = CameraVideoTrack(camera_index=0)
    pc.addTrack(video_track)

    # Configurar offer/answer
    offer = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    logger.info("Answer creada correctamente.")
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    import threading

    threading.Thread(target=loop.run_forever, daemon=True).start()
    app.run(host="0.0.0.0", port=port, debug=True)