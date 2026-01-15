import asyncio
import json

import cv2
import websockets
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
import fractions
from datetime import datetime

class CustomVideoStreamTrack(VideoStreamTrack):
    def __init__(self, camera_id):
        super().__init__()
        print ("Preparando la cámara ....")
        self.cap = cv2.VideoCapture(camera_id)
        print ("Cámara preparada")
        self.frame_count = 0

    async def recv(self):
        self.frame_count += 1
        print(f"Sending frame {self.frame_count}")
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to read frame from camera")
            return None
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = self.frame_count
        video_frame.time_base = fractions.Fraction(1, 30)  # Use fractions for time_base
        # Add timestamp to the frame
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Current time with milliseconds
        cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = self.frame_count
        video_frame.time_base = fractions.Fraction(1, 30)  # Use fractions for time_base
        return video_frame


async def handle_client(websocket):
    global video_sender
    print("Se ha conectado el receptor")
    # preparo las estructuras para la conexión WebRTC y envio la oferta
    pc = RTCPeerConnection()
    video_sender = CustomVideoStreamTrack(0)
    pc.addTrack(video_sender)
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    print ("Envio la oferta")
    await websocket.send(json.dumps(
                    {"type": "sdp", "sdp": pc.localDescription.sdp,
                     "sdp_type": pc.localDescription.type}))

    try:
        print ("Espero respuesta")
        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "sdp":
                print ("Recibo aceptación")
                desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdp_type"])

                await pc.setRemoteDescription(desc)
                print("Pongo en marcha el stream")

    except websockets.ConnectionClosed:
        print("❌ Conexión cerrada.")
    finally:
        cv2.destroyAllWindows()

async def main():
    global video_sender
    HOST = '0.0.0.0'
    PORT = 9999
    video_sender = CustomVideoStreamTrack(0)
    print(f"🖥️ Esperando conexión en ws://{HOST}:{PORT}")
    async with websockets.serve(handle_client, HOST, PORT):
        await asyncio.Future()  # Mantener servidor activo

if __name__ == "__main__":
    asyncio.run(main())