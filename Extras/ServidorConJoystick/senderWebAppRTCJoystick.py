# sender.py
# Archivo: ./sender.py
# Emisor: captura cámara y crea offer. Envía registro primero.

import asyncio
import json
import threading
import time
from threading import Thread

import cv2

from aiortc import RTCPeerConnection, RTCIceCandidate, RTCSessionDescription, VideoStreamTrack, RTCConfiguration, RTCIceServer
from av import VideoFrame
from websockets import connect

from aiortc.sdp import candidate_from_sdp

from dronLink.Dron import Dron
from djitellopy import Tello
import tkinter as tk
from tkinter import ttk

class CameraSource:
    def __init__(self, opcion, dron):
        global throttle, yaw, roll, pitch
        if opcion == 0 or opcion == 1:
            throttle = 1500
            yaw = 1500
            roll = 1500
            pitch = 1500
            self.cap = cv2.VideoCapture(opcion)

        else: # dron Tello
            dron.streamon()

            throttle = 0
            yaw = 0
            roll = 0
            pitch = 0
            self.cap = cv2.VideoCapture(
                "udp://127.0.0.1:11111?fifo_size=500000&overrun_nonfatal=1",
                cv2.CAP_FFMPEG
            )
        if not self.cap.isOpened():
                raise RuntimeError("No se pudo abrir la cámara")
        self.lock = asyncio.Lock()



    async def read(self):
        async with self.lock:
            frame = None

            # 🔥 descartar frames antiguos
            for _ in range(3):
                ret, f = self.cap.read()
                if ret:
                    frame = f

            if frame is None:
                return None

            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


class CameraVideoTrack(VideoStreamTrack):
    def __init__(self, source: CameraSource):
        super().__init__()
        self.source = source

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        frame = await self.source.read()

        if frame is None:
            await asyncio.sleep(0.1)
            return await self.recv()

        avf = VideoFrame.from_ndarray(frame, format="rgb24")
        avf.pts = pts
        avf.time_base = time_base
        return avf


def dict_to_ice_candidate(cand: dict):
    if cand is None:
        return None
    ice = candidate_from_sdp(cand["candidate"])
    ice.sdpMid = cand.get("sdpMid") or "0"
    ice.sdpMLineIndex = cand.get("sdpMLineIndex") or 0
    return ice

async def cleanup_client2(id):
    global ofertas
    pc = None
    for item in ofertas:
        if item["id"] == id:
            pc = item["conexion"]
            break
    if not pc:
        print("No he encontrado conexión para el receptor:", id)
        return
    for sender in pc.getSenders():
        if sender.track:
            print ("stop")
            #sender.track.stop()
    await pc.close()
    ofertas = [item for item in ofertas if item["id"] != id]

async def cleanup_client(id):
    global ofertas

    pc = None
    for item in ofertas:
        if item["id"] == id:
            pc = item["conexion"]
            break

    if not pc:
        print("No he encontrado conexión para el receptor:", id)
        return

        # Detener tracks (NO async)
    for sender in pc.getSenders():
        if sender.track:
            sender.track.stop()

    # Cerrar PeerConnection
    if pc.connectionState != "closed":
        await pc.close()

    # Eliminar de la lista
    ofertas = [item for item in ofertas if item["id"] != id]

    print(f"Conexión cerrada para receptor {id}")

def procesarRC (dron, opcion):
    global  throttle, yaw, roll, pitch
    if opcion == 0 or opcion == 1:
        send_rc = dron.send_rc
        send_rc(roll, pitch, throttle, yaw)
        dron.setFlightMode('LOITER')
    else:
        send_rc = dron.send_rc_control
    while True:
        send_rc(roll, pitch, throttle,yaw)
        time.sleep (1)

def scaleArdupilot (value):
    return int (value*500 + 1500)

def scaleTello( value):
    """
    Convierte valor del eje (-1 a 1) a rango RC (-100 a 100)
    """
    if value < 0:
        value = -value
        return int(-value * value * value * value * 100)
    else:
        return int(value * value * value * value * 100)

def askUser (dron):
    global fin, empezar
    input("\nPulsa cualquier tecla para empezar: ")
    print ("\nVamos a empezar")
    empezar = True
    input("\nPulsa cualquier tecla para aterrizar: ")
    fin = True
    dron.land()




async def run(server_url: str, stream_id: str, opcion, dron):
    global cameraTrack, cameraSource
    global throttle, yaw, roll, pitch
    global empezar, fin, parado
    global ofertas
    ofertas = []

    if opcion == 0 or opcion == 1:
        scale = scaleArdupilot
    else:
        scale = scaleTello


    async with connect(server_url) as ws:
        print ("Voy a registrarme como emisor del video")
        await ws.send(json.dumps({"type": "registro", "role": "emisor"}))
        empezar = False


        async for raw in ws:
                data = json.loads(raw)
                if data.get("type") == "peticion":
                    id =  data.get("id")
                    print ("Recibo una petición del receptor: ", id)
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
                    # creo un nuevo track para este cliente
                    # En versiones anteriores estaba creando un solo track compartido por todos los clientes
                    # Al cerrar un cliente mataba el track y se congelaban todos los clientes restantes
                    track = CameraVideoTrack(cameraSource)
                    pc.addTrack(track)

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
                if data.get("type") == "client-disconnect":
                    id = data.get("id")
                    print("Se desconecta el cliente: ", id)
                    await cleanup_client(id)
                    print ("Ya he eliminado el envío al cliente: ", id)

                if data.get("type") == "move":

                    if fin:
                        print ("Envio mensaje de fin")
                        await ws.send(json.dumps({"type": "end"}))
                    else:
                        if data.get ("id") == 'left':
                            throttle = scale (float(data.get ("y")))
                            yaw = scale(float(data.get("x")))
                        else:
                            pitch = scale(float(data.get("y")))
                            roll = scale(float(data.get("x")))

def arrancar(opcion, dron):
    server = "ws://dronseetac.upc.edu:8108"
    sid = "mi_stream"
    asyncio.run(run(server, sid, opcion, dron))

def on_radio_change():
    global opcion
    opcion = int( radio_var.get())

def connection():
    global opcion, fin, parado, cameraSource, dron
    if opcion == 0:
        dron = Dron()
        connection_string = 'tcp:127.0.0.1:5763'
        baud = 115200
        dron.connect(connection_string, baud)
    elif opcion == 1:
        dron = Dron()
        connection_string = 'com3'
        baud = 57600
        dron.connect(connection_string, baud)
    elif opcion == 2:
        dron = Tello()
        dron.connect()
        print('BATERIA: ', dron.get_battery())

    cameraSource = CameraSource(opcion, dron)

    fin = False
    parado = True
    threading.Thread(target=arrancar, args=[opcion,dron,]).start()


def start ():
    global opcion, dron
    if opcion == 0 or opcion == 1:
        dron.arm()
        dron.takeOff(5)
    else:
        dron.takeoff()
    threading.Thread(target=procesarRC, args=[dron, opcion]).start()


def close ():
    global dron
    global fin
    dron.land()
    fin = True

if __name__ == "__main__":
    '''global opcion, fin, parado
    fin = False
    parado = True

    server = "ws://dronseetac.upc.edu:8108"
    sid = "mi_stream"

    print ("Elige la fuente del video stream: ")
    print("0 ---  SITL (por defecto)")
    print("1 ---  Hexsoon")
    print("2 ---  Tello")
    try:
        opcion = int (input ("Escribe el número de la opción elegida: "))
        if opcion == 0:
            dron = Dron()
            connection_string = 'tcp:127.0.0.1:5763'
            baud = 115200
            dron.connect(connection_string, baud)
        elif opcion == 1:
            dron = Dron()
            connection_string = 'com3'
            baud = 57600
            dron.connect(connection_string, baud)
        elif opcion == 2:
            dron = Tello()
            dron.connect()
            print('BATERIA: ', dron.get_battery())
    except ValueError:
        print ("No has introducido ninguna opción")'''

    '''ofertas = []
    cameraSource = CameraSource(opcion, dron)
    asyncio.run(run(server, sid, opcion, dron))'''




    # Crear ventana principal
    root = tk.Tk()
    root.title("Ejemplo Tkinter")
    root.geometry("300x250")

    # Variable compartida para los RadioButtons
    radio_var = tk.IntVar(value=1)

    # Frame para los radios
    radio_frame = ttk.LabelFrame(root, text="Opciones")
    radio_frame.pack(padx=10, pady=10, fill="x")

    # RadioButtons
    ttk.Radiobutton(
        radio_frame, text="SITL (por defecto)",
        variable=radio_var, value=0,
        command=on_radio_change
    ).pack(anchor="w", padx=10, pady=2)

    ttk.Radiobutton(
        radio_frame, text="Hexsoon",
        variable=radio_var, value=1,
        command=on_radio_change
    ).pack(anchor="w", padx=10, pady=2)

    ttk.Radiobutton(
        radio_frame, text="Tello",
        variable=radio_var, value=2,
        command=on_radio_change
    ).pack(anchor="w", padx=10, pady=2)

    # Frame para los botones
    button_frame = ttk.LabelFrame(root, text="Acciones")
    button_frame.pack(padx=10, pady=10, fill="x")

    # Botones
    ttk.Button(
        button_frame, text="Conectar",
        command=connection
    ).pack(fill="x", padx=10, pady=2)

    ttk.Button(
        button_frame, text="Empezar",
        command=start
    ).pack(fill="x", padx=10, pady=2)

    ttk.Button(
        button_frame, text="Acabar",
        command=close
    ).pack(fill="x", padx=10, pady=2)


    # Arrancar la aplicación
    root.mainloop()