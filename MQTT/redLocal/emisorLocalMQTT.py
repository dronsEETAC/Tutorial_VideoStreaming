import cv2
import paho.mqtt.client as mqtt
import base64
import time

# el broker mosquitto se ejecuta en la máquina en la que está el receptor
# hay que conocer la IP de esa máquina dentro de la red de área local
BROKER = "IP de la máquina donde se ejecuta mosquitto"
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
    # puede ajustarse el nivel de calidad con un valor entre 1 (poca calidad) a 100 (máxima calidad)
    # cuanta más calidad más "pesa" el frame y menos fluido será el streamm de vídeo
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')

    # Publicar frame
    client.publish(TOPIC, jpg_as_text)

    # enviaremos 10 frames por segundo
    # este valor también se puede cambiar para buscar el mejor compromiso para no saturar al broker y no perder fluidez
    # en el stream de video
    time.sleep(0.1)  # Control de FPS (~20 FPS)

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
