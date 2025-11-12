from flask import Flask, render_template
import asyncio
import threading
import websockets

app = Flask(__name__)
clients = set()


@app.route('/')
def index():
    return render_template('indexWebAppWebRTC.html')


async def ws_handler(websocket):
    clients.add(websocket)
    print(f"✅ Nuevo cliente ({len(clients)} conectados)")
    try:
        async for msg in websocket:
            print(f"📨 {msg}")
            for client in list(clients):
                if client != websocket:
                    try:
                        await client.send(msg)
                    except Exception as e:
                        print(f"⚠️ Error al enviar: {e}")
    finally:
        clients.remove(websocket)
        print(f"❌ Cliente desconectado ({len(clients)} restantes)")


async def websocket_server():
    async with websockets.serve(ws_handler, "0.0.0.0", 8108):
        print("🚀 Servidor WebSocket en ws://0.0.0.0:8105")
        await asyncio.Future()  # Mantiene el server vivo


def start_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(websocket_server())


if __name__ == "__main__":
    # Lanzar servidor WebSocket en hilo aparte
    t = threading.Thread(target=start_websocket, daemon=True)
    t.start()

    print("🌐 Servidor Flask en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
