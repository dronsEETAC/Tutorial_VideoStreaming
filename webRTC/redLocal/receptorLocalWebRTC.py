import asyncio
import json

import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from websockets import connect

async def display_track(track):
    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")

        cv2.imshow("Receiver", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows()



async def main (websocket_url: str):
    pc = RTCPeerConnection()
    print ("He creado la estructura de datos")

    @pc.on("track")
    def on_track(track):
        print("Track recibido:", track.kind)
        if track.kind == "video":
            asyncio.create_task(display_track(track))

    async with connect(websocket_url) as ws:
        print ("Ya estoy conectado al emisor. Espero una oferta ...")

        async for raw in ws:
            print ("Recibo algo del emisor")
            data = json.loads(raw)
            if data.get("type") == "sdp":
                print ("Es la oferta del emisor")
                desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdp_type"])
                await pc.setRemoteDescription(desc)
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                print ("Ya tengo preparada la respuesta")
                await ws.send(json.dumps({"type": "sdp",  "sdp": pc.localDescription.sdp, "sdp_type": pc.localDescription.type}))
                print("Respuesta enviada")



if __name__ == "__main__":
    asyncio.run(main("ws://192.168.1.70:9999"))