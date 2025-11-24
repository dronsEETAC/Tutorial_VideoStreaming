# proxyWebsockets.py
# instalar websockets
import asyncio
import websockets


emitters = set()
receivers = set()

async def handle_emitter(websocket):
    # añado el emisor a la lista de emisores
    emitters.add(websocket)
    print("[INFO] Emisor conectado.")
    try:
        async for frame_data in websocket:
            dead_receivers = set()
            print ("Recibo frame y se lo envío a los receptores")
            for r in receivers:
                try:
                    await r.send(frame_data)
                except:
                    # este receptor está desconectado
                    dead_receivers.add(r)
            # actualizo la lista de receptores eliminando los que se han desconectado
            receivers.difference_update(dead_receivers)
    except Exception as e:
        print(f"[WARN] Emisor desconectado: {e}")
    finally:
        emitters.remove(websocket)
        print("[INFO] Emisor eliminado.")

async def handle_receiver(websocket):
    # se ha conectado un receptor
    # lo añado a la lista de receptores
    receivers.add(websocket)
    print(f"[INFO] Receptor conectado. Total: {len(receivers)}")
    try:
        await websocket.wait_closed()
    finally:
        receivers.remove(websocket)
        print("[INFO] Receptor desconectado.")

async def handler(websocket, path=None):
    # tengo que averiguar si se ha conectado un emisor o un receptor
    try:
        # websockets >=12.x usa websocket.request.path
        current_path = getattr(websocket, "request", None)
        if current_path:
            path = websocket.request.path
    except AttributeError:
        pass

    if not path:
        path = "/"

    if path == "/emisor":
        # se ha conectado un emisor
        await handle_emitter(websocket)
    elif path == "/receptor":
        # se ha conectado un receptor
        await handle_receiver(websocket)
    else:
        print(f"[WARN] Ruta desconocida: {path}")
        await websocket.close()

async def main():
    print("🚀 Proxy activo en ws://0.0.0.0:8000")
    async with websockets.serve(handler, "0.0.0.0", 8000):
        await asyncio.Future()  # Ejecutar para siempre

if __name__ == "__main__":
    asyncio.run(main())
