import asyncio
import websockets
from flask import Flask, render_template
from threading import Thread
import json
import random
import time

app = Flask(__name__)

receptores = []
wsEmisor = None

@app.route('/')
def index():
    return render_template('indexJoystick.html')

async def elegir():
    # Entre todos los clientes conectados va eligiendo y avisando a uno aleatoriamente, cada 20 segundos,
    # aunque espera 5 segundos antes de elegir al siguiente
    indiceAnterior = -1
    enMarcha = True
    seleccionando = True

    while enMarcha:
        if receptores and seleccionando:
            if indiceAnterior == -1:
                # Esperamos 10 segundos antes de elegir el primero
                await asyncio.sleep (10)
            indice = random.randrange(len(receptores))
            if len(receptores) == 1 or  indice != indiceAnterior:
                # solo elegimos otro si es diferente al último que se eligió
                cliente = receptores[indice]

                await cliente.send(json.dumps({"type": "startJoystick"}))
                print("He avisado a un cliente: ", indice)

                await asyncio.sleep(20)

                await cliente.send(json.dumps({"type": "stopJoystick"}))
                print("Retiro el Joystick del cliente: ", indice)
                await asyncio.sleep(5)
                indiceAnterior =  indice
        else:
            await asyncio.sleep(1)
    print("Acabamos")


async def handler(ws):
    global wsEmisor, receptores
    global seleccionando, enMarcha

    async for raw in ws:
            data = json.loads(raw)

            if data.get("type") == "registro" and data.get("role") == "emisor":
                print ("Se registra el emisor")
                wsEmisor = ws
                if len (receptores) > 0:
                    print ("Traslado al emisor los indices de los receptores que estaban esperando")
                    for indice, receptor in enumerate(receptores):
                        await wsEmisor.send(json.dumps({
                            "type": "receptor",
                            "id": indice
                        }))

            if data.get("type") == "peticion":
                print ("Recibo petición de receptor")
                receptores.append(ws)
                if wsEmisor:
                    indice = len(receptores)-1
                    print ("Envio al emisor en indice de este nuevo receptor")
                    await wsEmisor.send(json.dumps({
                        "type": "peticion",
                        "id": indice
                    }))
                else:
                    print ("El emisor aun no se ha conectado")

            if data.get("type") == "sdp" and data.get("role") == "emisor":
                id = data.get("id")
                print ("Recibo y traslado la oferta para el receptor: ", id)
                cliente = receptores[id]
                await cliente.send (raw)

            elif data.get("type") == "sdp" and data.get("role") == "receptor":
                id = receptores.index (ws)
                print ("Recibo y traslado al emisor la aceptación del receptor: ", id)
                data["id"] = id
                await wsEmisor.send(json.dumps(data))

            elif data.get("type") == "ice" and data.get("role") == "receptor":
                id = receptores.index(ws)
                data["id"] = id
                print ("Recibo y traslado al emisor un candidato para el receptor: ", id)
                await wsEmisor.send(json.dumps(data))

            elif data.get("type") == "ice" and data.get("role") == "emisor":
                print("Recibo y traslado a todos los receptores un candidato para el emisor")
                for receptor in receptores:
                    await receptor.send(raw)
            elif data.get("type") == "client-disconnect":
                id = receptores.index(ws)
                print ("Se descinecta el cliente: ", id)
                data["id"] = id
                await wsEmisor.send(json.dumps(data))
            elif data.get("type") == "move":
                # recibo datos del Joystick que debo enviar al emisor para que mueva el dron
                print ("***: ", data)
                await wsEmisor.send(json.dumps(data))
            elif data.get("type") == "start":
                print("Empezamos")
                seleccionando = True
            elif data.get("type") == "end":
                print("Recibo petición de fin")
                enMarcha = False


async def start_websocket_server():
    # Servidor WebSocket escuchando en puerto 8108
    asyncio.create_task(elegir())

    async with websockets.serve(handler, "0.0.0.0", 8108):
        print("🚀 Servidor WebSocket iniciado en ws://0.0.0.0:8108")
        print("📊 Servidor listo para manejar múltiples streams")
        await asyncio.Future()  # Mantener corriendo


def run_websocket_server():
    """Ejecutar el servidor WebSocket en un event loop separado"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_websocket_server())
    except KeyboardInterrupt:
        print("\n🛑 Servidor WebSocket detenido manualmente.")
    finally:
        loop.close()

def main():
    # Crear y empezar el thread del servidor WebSocket
    websocket_thread = Thread(target=run_websocket_server, daemon=True)
    websocket_thread.start()

    print("🔄 Iniciando servidor WebSocket en segundo plano...")

    # Iniciar servidor Flask
    print("🌐 Iniciando servidor Flask en http://0.0.0.0:8106")

    print ("ATENCION: poner en marcha el cliente antes de poner en marcha en emisor del video")
    app.run(host='0.0.0.0', port=8106, debug=False)

if __name__ == "__main__":
    main()

