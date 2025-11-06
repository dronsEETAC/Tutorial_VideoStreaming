# receptorGlobalWebsockets.py
# instalar opencv-python y websockets
import cv2
import base64
import numpy as np
import asyncio
import websockets


# Poner la IP pública de la máquina
# en la que se ejecuta el proxy
PROXY_URL = "ws://IP-proxy:8000/stream"

async def receive_video():
    async with websockets.connect(PROXY_URL, max_size=None) as ws:
        print("[INFO] Conectado al proxy.")
        while True:
            try:
                frame_data = await ws.recv()
                img_bytes = base64.b64decode(frame_data)
                npimg = np.frombuffer(img_bytes, dtype=np.uint8)
                frame = cv2.imdecode(npimg, 1)

                if frame is not None:
                    cv2.imshow("Receptor", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            except websockets.ConnectionClosed:
                print("[WARN] Conexión cerrada por el servidor.")
                break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(receive_video())
