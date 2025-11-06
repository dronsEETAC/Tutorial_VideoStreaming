# app.py
from flask import Flask, render_template
from flask_sock import Sock
import asyncio
import base64

app = Flask(__name__)
sock = Sock(app)

clients = set()  # navegadores conectados

@app.route("/")
def index():
    return render_template("indexWebAppWebsockets.html")

@sock.route("/ws")
def ws(ws):
    """
    Recibe frames del emisor y los reenvía a todos los clientes web
    """
    # Detectar si ws es emisor o navegador
    remote = ws.environ.get("REMOTE_ADDR")
    try:
        while True:
            frame_data = ws.receive()
            if frame_data is None:
                break
            # reenviar a todos los clientes conectados (excepto el emisor)
            for client in list(clients):
                try:
                    client.send(frame_data)
                except:
                    clients.remove(client)
    except:
        pass

@sock.route("/viewer")
def viewer(ws):
    """Clientes web que quieren ver video"""
    clients.add(ws)
    try:
        while True:
            asyncio.sleep(1)
    finally:
        clients.remove(ws)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
