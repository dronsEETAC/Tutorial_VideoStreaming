# emisorLocalMQTT.py
import cv2
import base64
import asyncio
import websockets

FLASK_WS_URL = "ws://147.83.249.79:8107/ws"  # Cambia IP o dominio
FLASK_WS_URL = "ws://127.0.0.1:5000/ws"  # Cambia IP o dominio
async def send_video():
    cap = cv2.VideoCapture(0)
    try:
        async with websockets.connect(FLASK_WS_URL, max_size=None) as ws:
            print("[INFO] Conectado al servidor Flask")
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                _, buffer = cv2.imencode(".jpg", frame)
                b64frame = base64.b64encode(buffer).decode("utf-8")

                await ws.send(b64frame)
                await asyncio.sleep(0.05)  # ~20 FPS
    except Exception as e:
        print("[ERROR]", e)
    finally:
        cap.release()

async def main():
    while True:
        await send_video()
        print("[INFO] Reconectando en 3s...")
        await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
