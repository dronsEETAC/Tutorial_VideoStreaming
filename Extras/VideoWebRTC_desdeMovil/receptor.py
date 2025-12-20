# receiver.py
# Archivo: ./receiver.py
# Receptor: espera offer, crea answer y muestra vídeo.

import asyncio
import json
import cv2
from aiortc import RTCPeerConnection, RTCIceCandidate, RTCSessionDescription, VideoStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.sdp import candidate_from_sdp
import ssl
import websockets

peer_id = "python"
target_id = "browser"




def dict_to_ice_candidate(cand: dict):
    if cand is None:
        return None
    ice = candidate_from_sdp(cand["candidate"])
    ice.sdpMid = cand.get("sdpMid") or "0"
    ice.sdpMLineIndex = cand.get("sdpMLineIndex") or 0
    return ice



async def display_track(track):
    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")

        cv2.imshow("Receiver2", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows()

async def main():
    # puesto que el servidor trabaja con HTTPS tenemos que conectarnos por wss
     ssl_context = ssl.create_default_context()
     ssl_context.check_hostname = False
     ssl_context.verify_mode = ssl.CERT_NONE

     async with websockets.connect(
                "wss://dronseetac.upc.edu:8107/ws",
                ssl=ssl_context
        ) as ws:


        config = RTCConfiguration(iceServers=[
                RTCIceServer(urls="stun:stun.relay.metered.ca:80"),

                RTCIceServer(urls="turn:dronseetac.upc.edu:3478",
                             username="dronseetac",
                             credential="Mimara00.")
            ])
        pc = RTCPeerConnection(config)


        @pc.on("icecandidate")
        async def on_ice(candidate):
            if candidate:
                print ("Recibo candidato")
                cjson = candidate.to_dict()
                await ws.send(json.dumps({
                    "type": "ice",
                    "role": "receptor",
                    "candidate": cjson
                }))
                print("Acabo de enviar ICE")
            else:
                # End-of-candidates
                print("Fin de candidatos")
                await ws.send(json.dumps({
                    "type": "ice",
                    "role": "receptor",
                    "candidate": None
                }))

        @pc.on("track")
        def on_track(track):
            print("Track recibido:", track.kind)
            if track.kind == "video":
                asyncio.create_task(display_track(track))


        await ws.send(peer_id)
        print("Ya he enviado mi petición de conexión. Espero oferta ....")

        async for raw in ws:
            data = json.loads(raw)
            print (data)
            if data.get("type") == "offer":
                print ("Es la oferta del emisor")

                await pc.setRemoteDescription(RTCSessionDescription(**data["offer"]))

                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                print ("Envío la respuesta")
                await ws.send(json.dumps({
                    "target": target_id,
                    "type": "answer",
                    "answer": {
                        "sdp": pc.localDescription.sdp,
                        "type": pc.localDescription.type
                    }
                }))

            if data.get("type") == "candidate":
                cand = data.get("candidate")
                if not cand:
                    print ("Fin de candidatos del emisor")
                    try:
                        await pc.addIceCandidate(None)
                    except Exception:
                        pass
                    continue

                # Convertir dict -> RTCIceCandidate
                try:
                    print("Recibo candidato del emisor")
                    rtc_cand = dict_to_ice_candidate(cand)
                    print (rtc_cand)
                    await pc.addIceCandidate(rtc_cand)
                except Exception as e:
                    print("Error añadiendo candidate:", e)
                continue

asyncio.run(main())
