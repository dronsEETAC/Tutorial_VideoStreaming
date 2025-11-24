# emisorLocalMQTT.py
# instalar opencv-python y websockets
import cv2
import base64
import asyncio
import websockets


# Poner la IP pública de la máquina
# en la que se ejecuta el proxy
# en el propio path indico que soy emisor
PROXY_URL = "ws://IP-proxy:8000/emisor"

async def send_video():
    print ("Preparando cámara ...")
    cap = cv2.VideoCapture(0)
    print ("Cámara preparada")
    try:
        async with websockets.connect(PROXY_URL, max_size=None) as ws:
            print("[INFO] Conectado al proxy.")
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                _, buffer = cv2.imencode('.jpg', frame)
                b64frame = base64.b64encode(buffer).decode("utf-8")

                try:
                    print ("Envio frame")
                    await ws.send(b64frame)
                except websockets.ConnectionClosed:
                    print("[WARN] Conexión cerrada. Reintentando...")
                    break

                await asyncio.sleep(0.05)  # ~20 FPS
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        cap.release()

async def main():
    while True:
        await send_video()
        print("[INFO] Reintentando conexión en 3 segundos...")
        await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
