import cv2
import paho.mqtt.client as mqtt
import base64
import time

# Configuración del broker HiveMQ público
BROKER = "broker.hivemq.com"
#BROKER = "test.mosquitto.org"
#BROKER = "broker.emqx.io"

PORT = 1883
TOPIC = "demo/video/stream"

# Inicializar cliente MQTT
client = mqtt.Client()
client.connect(BROKER, PORT)
client.loop_start()

# Captura de video desde la webcam
cap = cv2.VideoCapture(0)

print("📡 Transmitiendo video... presiona 'q' para salir.")
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Codificar frame a JPEG
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')

    # Publicar frame al topic
    client.publish(TOPIC, jpg_as_text)


    time.sleep(0.1)  # Control de FPS (~20 FPS)

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
