# signaling_server.py
import asyncio
import json
import logging
#from websockets import serve, WebSocketServerProtocol
from websockets import serve

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

clients = {}  # stream_id -> {"sender": ws, "receiver": ws, "queue": [msg,...]}

async def send_or_queue(stream_id: str, target_role: str, msg: str):
    """Enviar msg al peer si está conectado; si no, encolarlo."""
    entry = clients.setdefault(stream_id, {"sender": None, "receiver": None, "queue": []})
    peer = entry.get(target_role)
    is_open = peer and not getattr(getattr(peer, "closed_event", None), "is_set", lambda: False)()
    if is_open:
        try:
            await peer.send(msg)
            logging.info("Reenviado msg a %s/%s (stream=%s)", target_role, getattr(peer, "remote_address", None), stream_id)
            return True
        except Exception as e:
            logging.warning("Error enviando a peer %s: %s — encolando", target_role, e)
    # encolar si no está abierto
    entry["queue"].append(msg)
    logging.info("Peer %s no conectado -> mensaje encolado (stream=%s). Cola tamaño=%d", target_role, stream_id, len(entry["queue"]))
    return False


async def handler(ws):
    """Handler compatible con websockets >=12.x"""
    path = getattr(ws.request, "path", "/")  # obtener path si se necesita
    ws.max_size = None
    remote = ws.remote_address
    logging.info("Nueva conexión %s (path=%s)", remote, path)
    stream_id = None
    role = None
    try:
        async for raw in ws:
            try:
                data = json.loads(raw)
            except Exception:
                logging.warning("Mensaje no-JSON de %s: %s", remote, repr(raw)[:200])
                continue

            # Registro inicial
            if "role" in data and "stream_id" in data and data.get("type") == "register":
                role = data["role"]
                stream_id = str(data["stream_id"])
                entry = clients.setdefault(stream_id, {"sender": None, "receiver": None, "queue": []})
                entry[role] = ws
                logging.info("Registro: %s conectado como %s (stream=%s)", remote, role, stream_id)

                # enviar cola de mensajes si los hay
                if entry["queue"]:
                    logging.info("Enviando %d mensajes encolados a %s (stream=%s)", len(entry["queue"]), role, stream_id)
                    for queued in entry["queue"]:
                        try:
                            await ws.send(queued)
                        except Exception as e:
                            logging.warning("Error enviando mensaje encolado a %s: %s", role, e)
                    entry["queue"].clear()
                continue

            # Validación mínima
            if stream_id is None or role is None:
                await ws.send(json.dumps({"error": "Debe registrarse primero con type:'register'"}))
                continue

            # Enviar al otro peer
            peer_role = "receiver" if role == "sender" else "sender"
            await send_or_queue(stream_id, peer_role, json.dumps(data))

    except asyncio.CancelledError:
        raise
    except Exception as e:
        logging.exception("Error en handler para %s: %s", remote, e)
    finally:
        # Limpieza al desconectarse
        if stream_id and role:
            entry = clients.get(stream_id)
            if entry and entry.get(role) is ws:
                entry[role] = None
            if entry and not entry.get("sender") and not entry.get("receiver") and not entry.get("queue"):
                clients.pop(stream_id, None)
        logging.info("Conexión cerrada %s (stream=%s role=%s)", remote, stream_id, role)


async def main():
    host = "0.0.0.0"
    port = 8107
    async with serve(handler, host, port):
        logging.info("Signaling server en ws://%s:%d", host, port)
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
