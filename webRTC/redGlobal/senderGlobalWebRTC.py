# sender.py
# Archivo: ./sender.py
# Emisor: captura cámara y crea offer. Envía registro primero.

import asyncio
import json
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
from websockets import connect

class CameraVideoTrack(VideoStreamTrack):
    def __init__(self, device=0):
        super().__init__()
        self.cap = cv2.VideoCapture(device)

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        ret, frame = self.cap.read()
        if not ret:
            await asyncio.sleep(0.1)
            return await self.recv()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        avf = VideoFrame.from_ndarray(frame, format="rgb24")
        avf.pts = pts
        avf.time_base = time_base
        print ("Envio")
        return avf

async def run(server_url: str, stream_id: str):
    pc = RTCPeerConnection()
    pc.addTrack(CameraVideoTrack())

    async with connect(server_url) as ws:
        # enviar registro
        await ws.send(json.dumps({"type": "register", "role": "sender", "stream_id": stream_id}))
        print("Registrado como sender")

        # ICE -> enviar candidates al peer vía signaling
        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            print ("En icecandidate")
            if candidate:
                print("Candidate")
                await ws.send(json.dumps({"type": "candidate", "role": "sender", "stream_id": stream_id, "candidate": candidate.to_dict()}))

        # crear offer
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        await ws.send(json.dumps({"type": "sdp", "role": "sender", "stream_id": stream_id, "sdp": pc.localDescription.sdp, "sdp_type": pc.localDescription.type}))
        print("Offer enviada, esperando answer...")

        # procesar mensajes entrantes (answer + candidates)
        async for raw in ws:
            data = json.loads(raw)
            # solo procesar mensajes del receiver
            if data.get("role") != "receiver":
                continue
            if data.get("type") == "sdp":
                desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdp_type"])
                await pc.setRemoteDescription(desc)
                print("Answer recibida y aplicada")
            elif data.get("type") == "candidate":
                await pc.addIceCandidate(data["candidate"])
                print("Candidate recibido y añadido")


if __name__ == "__main__":
    import sys

    # Poner la IP pública de la máquina
    # en la que se ejecuta el proxy
    server = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8108"
    #server = sys.argv[1] if len(sys.argv) > 1 else "ws://dronseetac.upc.edu:8107"
    #server = sys.argv[1] if len(sys.argv) > 1 else "ws://IP_Proxy:8107"
    sid = sys.argv[2] if len(sys.argv) > 2 else "mi_stream"
    asyncio.run(run(server, sid))
