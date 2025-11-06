import cv2
import paho.mqtt.client as mqtt
import base64
import numpy as np

# el broker se ejecuta en la misma máquina que este receptor (localhost)
BROKER = "localhost"
PORT = 1883
TOPIC = "demo/video/stream"


def on_message(client, userdata, message):
    # acabo de recibir un nuevo frame
    try:
        # Decodificar el mensaje base64
        img_data = base64.b64decode(message.payload)
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is not None:
            cv2.imshow("Receptor - Video recibido", frame)
            cv2.waitKey(1)
    except Exception as e:
        print("Error al decodificar frame:", e)

# Inicializar cliente MQTT
client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, PORT)

client.subscribe(TOPIC)
client.loop_start()

print("📺 Esperando video... presiona Ctrl+C para salir.")
try:
    while True:
        pass
except KeyboardInterrupt:
    pass
finally:
    cv2.destroyAllWindows()
    client.loop_stop()
    client.disconnect()
