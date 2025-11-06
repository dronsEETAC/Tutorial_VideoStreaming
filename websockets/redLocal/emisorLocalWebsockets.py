import asyncio
import websockets
import cv2
import base64
import time

# IP del receptor, que actua como servidor del WebSocket, exponiéndolo en el puerto 8765
SERVER_IP = "IP dentro de la red de área local"  # IP dentro de la red de área local
PORT = 8765

async def send_video():
    uri = f"ws://{SERVER_IP}:{PORT}"
    print(f"📡 Conectando a {uri}...")
    async with websockets.connect(uri) as websocket:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ No se pudo abrir la cámara.")
            return

        print("🎥 Enviando video... presiona 'q' para salir.")
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Codificar frame a JPEG y luego a Base64
            _, buffer = cv2.imencode('.jpg', frame)
            encoded = base64.b64encode(buffer).decode('utf-8')

            await websocket.send(encoded)
            time.sleep(0.05)  # ~20 FPS

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(send_video())
