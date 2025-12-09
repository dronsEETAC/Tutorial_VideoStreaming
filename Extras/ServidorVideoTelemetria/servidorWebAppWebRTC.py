import asyncio
import websockets
from flask import Flask, render_template
from threading import Thread
import json


app = Flask(__name__)

receptores = []
wsEmisor = None

@app.route('/')
def index():
    #return render_template('indexWebAppWebRTC.html')
    return render_template('indexVideoMap.html')

async def handler(ws):
    global wsEmisor, receptores


    async for raw in ws:
            data = json.loads(raw)

            if data.get("type") == "registro" and data.get("role") == "emisor":
                print ("Se registra el emisor")
                wsEmisor = ws
                if len (receptores) > 0:
                    print ("Traslado al emisor los indices de los receptores que estan esperando")
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
                print ("Recibo y traslado al emisor un candidato para el receptor: ",id)
                await wsEmisor.send(json.dumps(data))

            elif data.get("type") == "ice" and data.get("role") == "emisor":
                print("Recibo y traslado a todos los receptores un candidato para el emisor")
                for receptor in receptores:
                    await receptor.send(raw)

async def start_websocket_server():
    # Servidor WebSocket escuchando en puerto 8108
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

    app.run(host='0.0.0.0', port=8106, debug=False)


if __name__ == "__main__":
    main()