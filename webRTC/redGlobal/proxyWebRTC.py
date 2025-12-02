# signaling_server.py
import asyncio
import json
import logging
#from websockets import serve, WebSocketServerProtocol
from websockets import serve


receptores = []
wsEmisor = None

async def handler(ws):
    global wsEmisor, receptores

    print ("Nueva conexión ")


    async for raw in ws:
            print ("Recibo algo")
            data = json.loads(raw)

            if data.get("type") == "registro" and data.get("role") == "emisor":
                print ("Es el emisor que se registra")
                wsEmisor = ws
                if len (receptores) > 0:
                    print ("Hay receptores esperando")
                    for indice, receptor in enumerate(receptores):
                        print("Aviso al emisor para que prepare una oferta para este cliente: ", indice)
                        await wsEmisor.send(json.dumps({
                            "type": "receptor",
                            "id": indice
                        }))

            if data.get("type") == "peticion":
                print ("Es una petición de recepción")
                receptores.append(ws)
                if wsEmisor:
                    print ("El emisor ya está registrado")
                    indice = len(receptores)-1
                    print ("Aviso al emisor para que prepare una oferta para este cliente: ", indice)
                    await wsEmisor.send(json.dumps({
                        "type": "receptor",
                        "id": indice
                    }))
                else:
                    print ("El emisor aun no se ha conectado")

            if data.get("type") == "sdp" and data.get("role") == "emisor":
                id = data.get("id")
                print ("Recibo una oferta para el cliente: ",data.get("id") )
                cliente = receptores[id]
                await cliente.send (raw)
                print("He re-enviado la oferta al cliente implicado")

            elif data.get("type") == "sdp" and data.get("role") == "receptor":
                id = receptores.index (ws)
                print ("Recibo aceptación del receptor: ", id)
                print ("Agrego el id al mensaje, que re-trasmito al emisor")
                data["id"] = id
                await wsEmisor.send(json.dumps(data))
                print ("Aceptación enviada al emisor")

            elif data.get("type") == "ice" and data.get("role") == "receptor":
                id = receptores.index(ws)
                print("Recibo ice del receptor: ", id)
                print("Agrego el id al mensaje, que re-trasmito al emisor")
                data["id"] = id
                await wsEmisor.send(json.dumps(data))
                print("ICE enviado al emisor")
            elif data.get("type") == "ice" and data.get("role") == "emisor":
                print("Recibo ice del emisor. Se lo envio a todos los receptores ")
                for receptor in receptores:
                    print("Aviso al emisor para que prepare una oferta para este cliente: ", indice)
                    await receptor.send(raw)





async def main():
    host = "0.0.0.0"
    port = 8108
    async with serve(handler, host, port):
        print ("Proxy en marcha en:", host, port)
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
