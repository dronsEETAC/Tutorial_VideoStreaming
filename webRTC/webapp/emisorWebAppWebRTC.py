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
        if not self.cap.isOpened():
            raise Exception("No se puede abrir la cámara")

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        ret, frame = self.cap.read()
        if not ret:
            print("Error leyendo frame de la cámara")
            await asyncio.sleep(0.1)
            return await self.recv()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        avf = VideoFrame.from_ndarray(frame, format="rgb24")
        avf.pts = pts
        avf.time_base = time_base
        return avf


async def run(server_url: str, stream_id: str):
    pc = RTCPeerConnection()

    # Añadir el track de video
    pc.addTrack(CameraVideoTrack())

    async with connect(server_url) as ws:

        print("🎥 Creando offer...")
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        # Enviar offer
        await ws.send(json.dumps({
            "type": "sdp",
            "role": "sender",
            "stream_id": stream_id,
            "sdp": pc.localDescription.sdp,
            "sdp_type": pc.localDescription.type
        }))
        print("📤 Offer enviada, esperando answer...")

        # Procesar mensajes entrantes (answer + candidates)
        try:
            async for raw in ws:
                try:
                    data = json.loads(raw)
                    print(f"📨 Mensaje recibido: {data.get('type')}")

                    # Solo procesar mensajes del receiver
                    if data.get("role") != "receiver":
                        print(f"⚠️  Mensaje ignorado (rol: {data.get('role')})")
                        continue

                    if data.get("type") == "sdp":
                        # Recibir y procesar answer
                        desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdp_type"])
                        await pc.setRemoteDescription(desc)
                        print("✅ Answer recibida y aplicada")

                except json.JSONDecodeError as e:
                    print(f"❌ Error decodificando JSON: {e}")
                except Exception as e:
                    print(f"❌ Error procesando mensaje: {e}")

        except Exception as e:
            print(f"❌ Error en la conexión WebSocket: {e}")
            raise

        # Mantener la conexión activa
        print("🔄 Manteniendo conexión activa...")
        await asyncio.sleep(3600)  # Mantener por 1 hora


if __name__ == "__main__":
    try:
        asyncio.run(run("ws://127.0.0.1:8108", "mi_stream"))
    except KeyboardInterrupt:
        print("\n🛑 Sender detenido manualmente")
    except Exception as e:
        print(f"❌ Error ejecutando sender: {e}")