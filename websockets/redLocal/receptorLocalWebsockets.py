import asyncio
import websockets
import base64
import cv2
import numpy as np

# el receptor del stream de video va a desempeñar el rol de servidor del websocket,
# exponiendolo en el puerto 8756
HOST = '0.0.0.0'
PORT = 8765

async def handle_client(websocket):
    print(f"🎥 Cliente conectado desde {websocket.remote_address}")
    try:
        async for message in websocket:
            # Decodificar frame recibido (base64 → numpy → imagen)
            frame_data = base64.b64decode(message)
            np_arr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is not None:
                cv2.imshow("Receptor - Video recibido", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except websockets.ConnectionClosed:
        print("❌ Conexión cerrada.")
    finally:
        cv2.destroyAllWindows()

async def main():
    print(f"🖥️ Esperando conexión en ws://{HOST}:{PORT}")
    async with websockets.serve(handle_client, HOST, PORT):
        await asyncio.Future()  # Mantener servidor activo

if __name__ == "__main__":
    asyncio.run(main())
