from paho.mqtt.client import ssl



import paho.mqtt.client as mqtt

# Configuración del broker público (varias opciones)
#BROKER = "broker.hivemq.com"
#BROKER = "test.mosquitto.org"
BROKER = "dronseetac.upc.edu"

PORT = 8883 # el puerto es este en cualquiera de las opciones
TOPIC = "demo/video/stream"

# Inicializar cliente MQTT
client = mqtt.Client("prueba", transport="websockets")
client.username_pw_set(
    "dronsEETAC", "mimara1456."
)
client.tls_set(
    ca_certs=None,
    certfile=None,
    keyfile=None,
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLS,
    ciphers=None,
)
def on_connect (client, userdata, flags, rc):
    if rc == 0:
        print ("Conectado")
    else:
        print ("Error")

print ("Voy a conectarme")
client.on_connect = on_connect
client.connect(BROKER, PORT)
client.loop_forever()


