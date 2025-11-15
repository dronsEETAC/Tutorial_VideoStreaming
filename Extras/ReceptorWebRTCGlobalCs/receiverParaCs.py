# receiver.py
# Archivo: ./receiver.py
# Receptor: espera offer, crea answer y muestra vídeo.

import asyncio
import json
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription
from websockets import connect
import socket
import struct



async def display_track(track):
    SERVER_IP = "127.0.0.1"
    SERVER_PORT = 5000

    # --- Inicializar socket ---
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")

        #cv2.imshow("Receiver", img)

        ret, jpeg = cv2.imencode(".jpg", img)
        data = jpeg.tobytes()
        print("Envio frame")

        # Enviar tamaño + datos
        sock.sendall(struct.pack(">I", len(data)) + data)


        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows()

async def run(server_url: str, stream_id: str):
    pc = RTCPeerConnection()

    @pc.on("track")
    def on_track(track):
        print("Track recibido:", track.kind)
        if track.kind == "video":
            asyncio.create_task(display_track(track))

    async with connect(server_url) as ws:
        # registro
        await ws.send(json.dumps({"type": "register", "role": "receiver", "stream_id": stream_id}))
        print("Registrado como receiver, esperando offer...")


        async for raw in ws:
            data = json.loads(raw)
            if data.get("role") != "sender":
                continue
            if data.get("type") == "sdp":
                print ("Ha llegado la oferta del emisor")
                # oferta llegada: aplicarla y crear answer
                desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdp_type"])
                await pc.setRemoteDescription(desc)
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                await ws.send(json.dumps({"type": "sdp", "role": "receiver", "stream_id": stream_id, "sdp": pc.localDescription.sdp, "sdp_type": pc.localDescription.type}))
                print("Answer enviada")



if __name__ == "__main__":
    import sys

    # Poner la IP pública de la máquina
    # en la que se ejecuta el proxy
    #server = sys.argv[1] if len(sys.argv) > 1 else "ws://dronseetac.upc.edu:8107"
    server = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8108"

    #server = sys.argv[1] if len(sys.argv) > 1 else "ws://IP_proxy:8107"
    sid = sys.argv[2] if len(sys.argv) > 2 else "mi_stream"
    asyncio.run(run(server, sid))
