import asyncio
import websockets

SERVER_URL = "ws://localhost:8108/ws"

async def listen():
    async with websockets.connect(SERVER_URL) as ws:
        print(f"✅ Conectado al servidor WebSocket: {SERVER_URL}")

        # Tarea que envía mensajes al servidor
        async def send_messages():
            while True:
                msg = input("📤 Escribe un mensaje (o 'exit' para salir): ")
                if msg.lower() == "exit":
                    await ws.close()
                    break
                await ws.send(msg)

        # Tarea que recibe mensajes del servidor
        async def receive_messages():
            try:
                async for message in ws:
                    print(f"📩 Recibido: {message}")
            except websockets.ConnectionClosed:
                print("❌ Conexión cerrada por el servidor")

        # Ejecutar ambas tareas en paralelo
        await asyncio.gather(send_messages(), receive_messages())

if __name__ == "__main__":
    asyncio.run(listen())
