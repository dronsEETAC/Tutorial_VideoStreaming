#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# websocket_proxy_flask.py

import asyncio
import websockets
from flask import Flask, render_template
from threading import Thread
import json

# Diccionario para almacenar clientes por stream_id
# Estructura: {stream_id: set([websocket1, websocket2, ...])}
clients_by_stream = {}

app = Flask(__name__)
connected_clients = set()

# Ruta principal que sirve el indexWebAppWebRTC.html
@app.route('/')
def index():
    return render_template('indexWebAppWebRTC.html')


async def websocket_handler(websocket):
    # añado el cliente al conjunto de los conectados (si ya está no se hace nada
    # porque estoy usando un set
    connected_clients.add(websocket)

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


async def start_websocket_server():
    # Servidor WebSocket escuchando en puerto 8108
    async with websockets.serve(websocket_handler, "0.0.0.0", 8108):
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
    print("🌐 Iniciando servidor Flask en http://127.0.0.1:5003")

    print ("ATENCION: poner en marcha el cliente antes de poner en marcha en emisor del video")
    app.run(host='0.0.0.0', port=5003, debug=False)


if __name__ == "__main__":
    main()