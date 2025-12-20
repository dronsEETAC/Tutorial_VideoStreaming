# sender.py
# Archivo: ./sender.py
# Emisor: captura cámara y crea offer. Envía registro primero.

import asyncio
import json
import cv2

from aiortc import RTCPeerConnection, RTCIceCandidate, RTCSessionDescription, VideoStreamTrack, RTCConfiguration, RTCIceServer
from av import VideoFrame
from websockets import connect

from aiortc.sdp import candidate_from_sdp
from dronLink.Dron import Dron


ofertas = []
class CameraVideoTrack(VideoStreamTrack):
    def __init__(self, device=0):
        super().__init__()
        self.cap = cv2.VideoCapture(device)
        print ("Camara preparada")

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

# ---------------------------------------------------------
#  SUPONEMOS QUE YA EXISTE ESTA FUNCIÓN EN TU PROYECTO
# ---------------------------------------------------------
def DamePosicion():
    # Debe devolver (lat, lon) como floats
    # Ejemplo ficticio:
    return 41.27643480257282, 1.9886956161819893
# ---------------------------------------------------------

async def enviar_telemetria(dc):
    """Envía lat/lon por el DataChannel a 10 Hz."""
    global lat, lon, heading
    while True:
        msg = json.dumps({"lat": lat, "lon": lon, "heading": heading})
        dc.send(msg)
        await asyncio.sleep(0.1)   # 10 Hz (10 veces por segundo)

def dict_to_ice_candidate(cand: dict):
    if cand is None:
        return None
    ice = candidate_from_sdp(cand["candidate"])
    ice.sdpMid = cand.get("sdpMid") or "0"
    ice.sdpMLineIndex = cand.get("sdpMLineIndex") or 0
    return ice

async def run(server_url: str, stream_id: str):
    global cameraTrack, ofertas, dron, lat, lon

    dron = Dron()
    connection_string = 'tcp:127.0.0.1:5763'
    baud = 115200
    # connection_string = 'com3'
    # baud = 57600
    dron.connect(connection_string, baud)
    print('conectado')

    def procesarTelemetria(telemetryInfo):
        global lat, lon, heading
        # estos son los 3 datos de telemetrìa que enviaré
        lat = telemetryInfo ['lat']
        lon = telemetryInfo['lon']
        heading = telemetryInfo['heading']

    dron.send_telemetry_info(procesarTelemetria)

    async with connect(server_url) as ws:
        print ("Voy a registrarme como emisor del video")
        await ws.send(json.dumps({"type": "registro", "role": "emisor"}))
        async for raw in ws:
            data = json.loads(raw)
            if data.get("type") == "peticion":
                id =  data.get("id")
                print ("Recibo una petición del receptor: ", id)
                config = RTCConfiguration(iceServers=[
                    RTCIceServer(urls="stun:stun.relay.metered.ca:80"),
                    RTCIceServer(urls="turn:standard.relay.metered.ca:80",
                                 username="337f189c0bf26e1022e19f05",
                                 credential="pSwi01maZzQZTUAf")
                ])

                pc = RTCPeerConnection(config)

                @pc.on("icecandidate")
                async def on_ice(candidate):
                    if candidate:
                        print ("Obtengo candidato")
                        cjson = candidate.to_dict()
                        await ws.send(json.dumps({
                            "type": "ice",
                            "role": "emisor",
                            "id": id,
                            "candidate": cjson
                        }))
                        print("Envio al servidor candidato para el receptor: ", id)
                    else:
                        await ws.send(json.dumps({
                            "type": "ice",
                            "role": "emisor",
                            "id": id,
                            "candidate": None
                        }))
                        print("Envio fin de candidatos para el receptor: ", id)
                # creo el track para el stream de video
                pc.addTrack(cameraTrack)
                # y creo el canal para los datos de telemetría
                dc = pc.createDataChannel("telemetry")

                @dc.on("open")
                def on_open():
                    print("Canal WebRTC abierto, iniciando envío...")
                    # pongo en marcha la función que va a enviar los datos de telemetría
                    # por el canal de datos
                    asyncio.create_task(enviar_telemetria(dc))

                @dc.on("close")
                def on_close():
                    print("DataChannel cerrado")


                offer = await pc.createOffer()
                await pc.setLocalDescription(offer)
                ofertas.append ({
                    'id': id,
                    'conexion': pc
                })

                await ws.send(json.dumps(
                    {"type": "sdp", "role": "emisor", "id": id, "sdp": pc.localDescription.sdp,
                     "sdp_type": pc.localDescription.type}))
                print ("Envio oferta para el receptor: ", id)

            if data.get("type") == "sdp":
                id = data.get("id")
                print ("Recibo aceptación del receptor: ", id)
                desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdp_type"])
                for item in ofertas:
                    if item["id"] == id:
                        pc = item["conexion"]
                        break

                await pc.setRemoteDescription(desc)


            if data.get("type") == "ice" and data.get("role") == "receptor":
                    id = data.get("id")
                    print ("Recibo candidato del receptor: ", id)
                    pc = None
                    for item in ofertas:
                        if item["id"] == id:
                            pc = item["conexion"]
                            break
                    if not pc:
                        print("No he encontrado conexión para el receptor:", id)
                        continue

                    cand = data.get("candidate")

                    try:
                        # Convertir dict -> RTCIceCandidate
                        rtc_cand = dict_to_ice_candidate(cand)
                        await pc.addIceCandidate(rtc_cand)
                        print (" Candidato añadido para receptor: ", id)
                    except Exception as e:
                        print("Error añadiendo candidato:", e)
                    continue

if __name__ == "__main__":
    cameraTrack = CameraVideoTrack()
    import sys
    server = "ws://dronseetac.upc.edu:8108"
    #server = "ws://127.0.0.1:8108"
    sid = "mi_stream"
    asyncio.run(run(server, sid))
