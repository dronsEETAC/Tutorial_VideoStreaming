# sender.py
# Archivo: ./sender.py
# Emisor: captura cámara y crea offer. Envía registro primero.

import asyncio
import json
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
from websockets import connect
ofertas = []
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
        return avf

async def run(server_url: str, stream_id: str):
    global cameraTrack, ofertas

    async with connect(server_url) as ws:
        print ("Ya estoy conectado al proxy")
        await ws.send(json.dumps({"type": "registro", "role": "emisor"}))
        print ("Ya me he registrado")

        async for raw in ws:
            print ("Recibo algo del proxy")
            data = json.loads(raw)
            if data.get("type") == "receptor":
                print ("Un receptor necesita oferta")
                id =  data.get("id")
                pc = RTCPeerConnection()
                pc.addTrack(cameraTrack)
                offer = await pc.createOffer()
                await pc.setLocalDescription(offer)
                ofertas.append ({
                    'id': id,
                    'conexion': pc
                })
                print ("ya tengo preparada la oferta")
                await ws.send(json.dumps(
                    {"type": "sdp", "role": "emisor", "id": id, "sdp": pc.localDescription.sdp,
                     "sdp_type": pc.localDescription.type}))
                print ("Ya he enviado la oferta")

            if data.get("type") == "sdp":
                id = data.get("id")
                print ("Es la aceptacion del receptor: ", id)
                desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdp_type"])
                for item in ofertas:
                    if item["id"] == id:
                        pc = item["conexion"]
                        break
                print ("Ya tengo la conexión para este cliente")
                await pc.setRemoteDescription(desc)
                print("Acepto la petición y pongo en marcha el stream")


if __name__ == "__main__":
    cameraTrack = CameraVideoTrack()
    import sys
    server = "ws://127.0.0.1:8108"
    server = "ws://dronseetac.upc.edu:8108"
    sid = "mi_stream"
    asyncio.run(run(server, sid))
