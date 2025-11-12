#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# websocket_proxy.py

import asyncio
import websockets

# Conjunto global de clientes conectados
connected_clients = set()

async def handler(websocket):
    # Registrar nuevo cliente
    connected_clients.add(websocket)
    print(f"✅ Nuevo cliente conectado: {websocket.remote_address}, total: {len(connected_clients)}")

    try:
        # Esperar mensajes del cliente
        async for message in websocket:
            print(f"📨 Mensaje recibido: {message}")
            # Enviar a todos los demás clientes
            for client in connected_clients:
                if client != websocket:
                    try:
                        await client.send(message)
                    except websockets.ConnectionClosed:
                        pass
    except websockets.ConnectionClosed:
        pass
    finally:
        # Quitar cliente al desconectarse
        connected_clients.remove(websocket)
        print(f"❌ Cliente desconectado: {websocket.remote_address}, total: {len(connected_clients)}")


async def main():
    # Servidor escuchando en puerto 8765
    async with websockets.serve(handler, "0.0.0.0", 8108):
        print("🚀 Servidor WebSocket iniciado en ws://0.0.0.0:8108")
        await asyncio.Future()  # Mantener corriendo

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido manualmente.")
