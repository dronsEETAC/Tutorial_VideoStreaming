from flask import Flask, render_template
from flask_sock import Sock
import json

app = Flask(__name__)
sock = Sock(app)

clients = {}

@app.route("/")
def index():
    return render_template("index.html")

@sock.route("/ws")
def websocket(ws):
    peer_id = ws.receive()
    clients[peer_id] = ws
    print("Conectado:", peer_id)

    try:
        while True:
            msg = ws.receive()
            data = json.loads(msg)
            target = data["target"]

            if target in clients:
                clients[target].send(msg)
    finally:
        del clients[peer_id]
        print("Desconectado:", peer_id)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8107,
        #ssl_context=("cert.pem", "key.pem")
    )