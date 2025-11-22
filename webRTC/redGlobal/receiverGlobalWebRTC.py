# receiver.py
# Archivo: ./receiver.py
# Receptor: espera offer, crea answer y muestra vídeo.

import asyncio
import json
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription
from websockets import connect

async def display_track(track):
    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")

        cv2.imshow("Receiver2", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows()

async def run(server_url: str, stream_id: str):
    pc = RTCPeerConnection()
    print ("He creado la estructura de datos")

    @pc.on("track")
    def on_track(track):
        print("Track recibido:", track.kind)
        if track.kind == "video":
            asyncio.create_task(display_track(track))

    async with connect(server_url) as ws:
        print ("Ya estoy conectado al proxy")
        await ws.send(json.dumps({"type": "peticion"}))
        print("Ya he enviado mi petición de conexión. Espero oferta ....")

        async for raw in ws:
            print ("Recibo algo del server")
            data = json.loads(raw)
            if data.get("type") == "sdp":
                print ("Es la oferta del emisor")
                desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdp_type"])
                await pc.setRemoteDescription(desc)
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                print ("Ya tengo preparada la respuesta")
                await ws.send(json.dumps({"type": "sdp", "role": "receiver", "stream_id": stream_id, "sdp": pc.localDescription.sdp, "sdp_type": pc.localDescription.type}))
                print("Respuesta enviada")



if __name__ == "__main__":
    server ="ws://127.0.0.1:8108"
    sid = "mi_stream"
    asyncio.run(run(server, sid))
