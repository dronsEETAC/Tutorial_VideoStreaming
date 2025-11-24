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

@sock.route("/emisor")
def ws(ws):
    print (" Se ha conectado el emisor")
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

@sock.route("/receptor")
def viewer(ws):
    print ("Se ha conectado un receptor")
    clients.add(ws)
    try:
        while True:
            asyncio.sleep(1)
    finally:
        clients.remove(ws)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
