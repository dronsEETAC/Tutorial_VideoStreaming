# Tutorial de videostreaming para el Drone Engineering Ecosystem   

## 1. Introducción
Una de las aplicaciones más habituales de los drones es la captación de imágenes. Un caso particular es el envío a tierra en tiempo real del stream de video capturado por la cámara del dron.    

La forma de implementar el video streaming depende del escenario concreto. No es lo mismo el caso en el que el emisor del vídeo sea la Raspberry Pi abordo y el receptor sea un portátil conectado a la misma red de área local que el caso en el que tanto el emisor como el receptor están conectados a Internet y físicamente lejos. Además, existen varios protocolos de comunicación y herramientas para implementar video streaming, con sus ventajas en inconvenientes.    

En este tutorial describimos en detalle los diferentes escenarios, protocolos y herramientas. Además, proporcionamos los códigos necesarios para cada caso concreto. En particular consideraremos tres escenarios:   

1. Local: emisor y receptor (o receptores) conectados en la misma red de área local
2. Global: emisor y receptor (o receptores) conectados a Internet
3. WebApp: receptor conectado a una WebApp (es un caso particular del anterior)
   
Por otra parte, consideraremos tres protocolos para implementar video streaming: MQTT, websockets y WebRTC.   

Naturalmente, otro escenario posible, que no se considera aquí, es que el dron tenga un sistema tema de transmisión de video por un canal específico que le conecta directamente con un receptor de vídeo conectado a la estación de tierra.    

## 2. Escenario local   

En este caso, el emisor y el receptor están conectados a la misma red de área local y, por tanto, cada uno puede conectarse directamente con el otro conociendo su dirección IP dentro de la red. Por ejemplo, el emisor puede ser una Raspberry Pi (RPi) abordo del dron con una cámara conectada y el receptor puede ser un portátil que se ha conectado al punto de acceso WiFi ofrecido por la RPi. De hecho, puede haber varios receptores, todos ellos conectados a ese punto de acceso. Veamos la implementación de video streaming usando cada uno de los tres protocolos considerados en este tutorial.   

### 2.1 MQTT (Message Queuing Telemetry Transport)   
 
Se trata de un protocolo de comunicación ligero y especialmente eficiente para comunicaciones de pequeños paquetes de datos entre dispositivos de bajo consumo. Está especialmente ideado para IoT (Internet de las cosas).   

El protocolo utiliza el mecanismo de suscripción/publicación. Los dispositivos conectados a través de MQTT pueden publicar mensajes y pueden suscribirse a ciertos tipos de mensajes. Por ejemplo, la RPi puede suscribirse a los mensajes de tipo “despegar”. Cualquiera de los dispositivos conectados puede publicar un mensaje de tipo “despegar” de manera que ese mensaje llegará a la RPi que dará la orden al autopiloto. De manera análoga, todos los dispositivos pueden suscribirse a mensajes del tipo “frame” de manera que cuando la RPi tenga un nuevo frame procedente de la cámara puede publicar ese “frame” que llegará a todos los suscritos, que podrán mostrar el stream de video a los usuarios correspondientes.   
 
La comunicación usando MQTT requiere de la intervención de un agente software que se denomina bróker y que se encarga de administrar las publicaciones y las suscripciones y encaminar los mensajes que se publican. Naturalmente, el bróker también tiene que estar conectado a la red de área local.   
 
El bróker puede ponerse en marcha en la RPi o en la estación de tierra. La herramienta mosquitto es ideal para crear un bróker y ponerlo en marcha. El siguiente vídeo muestra cómo instalar mosquitto en Windows:    

[![](https://markdown-videos-api.jorgenkh.no/url?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3Dsxspkg8U_Lc)](https://www.youtube.com/watch?v=sxspkg8U_Lc)    
 
 
Es importante tener en cuesta que el fichero de configuración (mosquitto.conf) debe editarse con permisos de administración y que las dos líneas que hay que añadir son:   
```
listener 1883 0.0.0.0
allow_anonymous true
```
y deben añadirse en ese orden (en el vídeo se añaden en orden contrario). En el caso de que haya que parar/reanudar el borker mosquitto deben usarse los comandos siguientes, ejecutados con permiso de administrador:   
```
net stop mosquitto
net start mosquitto
```
En la carpeta MQTT/Local pueden encontrarse los códigos de un emisor y un receptor. El emisor publica los frames del stream de video en un bróker mosquitto que se ejecuta en el mismo ordenador que el receptor. El receptor se ha suscrito a los frames de vídeo y por tanto los recibe y los muestra al usuario.   
 
Se observará inmediatamente que la fluidez del vídeo no es ideal, porque MQTT no está pensado para transmisión de datos grandes y frecuentes (como los frames de un stream de video). La fluidez puede ajustarse haciendo que los frames se envíen con menos calidad (menos bytes) y con menos frecuencia. En el código del emisor se indica con comentarios cómo controlar esos dos parámetros.   
 
### 2.2 Websockets   

Como ya se ha indicado el protocolo MQTT es ideal para comunicar mensajes cortos y poco frecuentes. Sin embargo, no es el mecanismo ideal para comunicar el stream de video, puesto la gestión que debe realizar el bróker introduce retardos que afectan a la fluidez del vídeo.      

Una alternativa que mejora la experiencia de usuario es utilizar Websockets para la comunicación del stream de video. Este mecanismo utiliza TCP/IP (igual que MQTT) pero no necesita de la intermediación de ningún bróker. La gestión de la información que viaja es más eficiente que en el caso de MQTT y, por tanto, los retardos son mucho menores y la fluidez mucho mejor.   

Cuando se usa una comunicación de Websocket, uno de los agentes implicados (emisor o receptor) debe desempeñar el rol de servidor y el otro el rol de cliente. El servidor crea el websocket y queda a la espera de conexiones. El cliente se conecta al servidor usando la IP de éste en la red de área local. La conexión se realiza utilizando el protocolo HTTP, exactamente igual que haría un navegador para conectarse a una página web (de ahí el término websocket). Una vez realizada la conexión, ésta se mantiene abierta creando un canal de comunicación bidireccional. A partir de ese momento, tanto el servidor como el cliente pueden desempeñar el rol de emisor o de receptor, y el stream de video circula por el canal creado con mayor fluidez que en el caso de MQTT.    
 
En la carpeta Websockets/Local pueden encontrarse los códigos de un emisor y un receptor que utilizan websockets para implementar video streaming. En ese caso, el receptor es el que actúa de servidor del websocket, pero podría ser perfectamente al revés. Se observará que la fluidez es mucho mejor que en el caso de MQTT. No obstante, puede modificarse en el emisor la calidad del frame que se envía y la frecuencia de envío exactamente igual que en el caso del emisor vía MQTT.   

### 2.3 WebRTC   

El protocolo Websockets no es tampoco el mecanismo ideal ya que el uso de TCP introduce elementos de control de flujo, como por ejemplo recuperación de paquetes perdidos, que no se requieren en el caso de la trasmisión de video, puesto que la pérdida eventual de frames no necesariamente representa un excesivo perjuicio de la experiencia de usuario. Otros protocolos, como por ejemplo WebRTC, se basan en UDP/IP y, por tanto, no esperan confirmaciones de paquetes, lo cual da como resultado una transmisión de mayor fluidez.    

De nuevo, uno de los agentes implicados (emisor o receptor) debe actuar como servidor y el otro como cliente. El cliente se conecta al servidor usando la IP de éste en la red local. Para establecer la conexión el cliente y servidor intercambian algunos mensajes por websocket. Una vez establecida la conexión el emisor envía el stream de video que llegará al receptor con menor retraso y mejor fluidez, como corresponde al uso de UDP en vez de TCP, aunque con posibles pérdidas de paquetes que, si bien serían inadmisibles si se están enviando instrucciones, no van a afectar significativamente a la experiencia de usuario en el caso de video streaming.    
 
En la carpeta WebRTC/Local pueden encontrarse los códigos de un emisor (que en este caso es el que actúa como servidor) y un receptor que utilizan WebRTC para implementar video streaming.    

## 3. Escenario global   

En el escenario global tanto el emisor como el receptor (o receptores) están conectados a Internet y el stream de vídeo se va a transmitir a través de la red global. Por tanto, el receptor puede estar lejos del emisor. De nuevo, la implementación puede hacerse usando cualquiera de los tres protocolos considerados.   
 
### 3.1 MQTT    

En este caso, el bróker tiene que estar también conectado a Internet para que el receptor pueda publicar los frames de vídeo y el receptor pueda recibirlos. Lo más cómodo en este caso es utilizar un bróker público y gratuito. Algunos de los más utilizados son:   

| Broker | Puerto TCP | Puerto Websockets |
|---------------|-------------|---------|
|test.mosquitto.org  |1883 | 8080 |
|broker.hivemq.com | 1883 |8000|
|broker.emqx.io    |1883| 8083 |

El puerto TCP que se indica en la tabla es el que debe usarse para una conexión global entre emisor y receptor. El puerto websockets es el que deberá usar la webapp, tal y como se explicará en el apartado 4.1.
En la carpeta MQTT/Global pueden encontrarse los códigos de un emisor y un receptor que se comunican el stream de video a través de un bróker público y gratuito. Los códigos son exactamente iguales que los del caso del escenario local excepto por lo que respecta a la conexión con el bróker. En los comentarios del código se indica cómo conectarse al resto de brokers públicos mencionados.   
 
### 3.2 Websockets

En un escenario global el emisor y receptor están conectados a Internet pero pertenecen a redes de área local diferentes y no tienen asignadas IP públicas. Por tanto, no es posible establecer una conexión directa entre un cliente y un servidor, tal y como sí es posible en el caso del escenario local.   

En este caso, la comunicación vía Websocket requiere de un proxy que haga de intermediario. El proxy debe estar conectado a internet y tener asignada una IP pública. El proxy actuará de servidor y creará el Websocket de manera que tanto el emisor como el receptor se conectarán al proxy usando la IP pública de éste. Ahora el emisor enviará el video stream al proxy que lo reenviará al receptor.   
 
En la carpeta Websocket/Global pueden encontrarse los códigos de un emisor, un receptor y un proxy. Es importante tener en cuenta que el proxy debe ejecutarse en un ordenador conectado a internet y con una IP pública para que tanto el emisor como el receptor puedan conectarse.   

### 3.3 WebRTC   

Al igual que en el caso de Websockets, si se usa WebRTC en un escenario global es necesaria la intervención de un proxy que hará el rol de servidor al que se conectarán tanto el emisor como el receptor. 
En la carpeta WebRTC/Global pueden encontrarse los códigos de un emisor, un receptor y un proxy, que también debe ejecutarse en un ordenador con IP pública.    
 
## 4. WebApp   

Este escenario es un caso particular del escenario global, en el que el cliente es una WebApp. Esto permite que el video stream se reciba en un dispositivo móvil que se ha conectado a la WebApp.   
 
Una WebApp es un servidor que sirve páginas web, igual que el servidor que sirve las páginas web de www.upc.edu. Pero las páginas web que sirve no tienen noticias o enlaces a documentos. Tienen botones de tal manera que cuando nos conectamos a la web desde el navegador del móvil lo que nos aparece en la pantalla es una página con botones, uno de los cuales, por ejemplo, nos permite hacer despegar el dron. Además, la WebApp puede proporcionar al cliente el stream de video que recibe del emisor para que el usuario puede verlo en su dispositivo móvil.    
 
Normalmente, la comunicación entre el servidor web y el navegador del dispositivo móvil que se conecta se realiza mediante el protocolo HTTP. Al conectarnos al servidor se realiza un GET para obtener el fichero HTML de la página principal y si se pulsa un botón de esa página se realiza un POST que permite al servidor detectar que el usuario quiere, por ejemplo, despegar el dron. La comunicación entre el servidor web y el dispositivo que controla el dron puede realizarse mediante MQTT o incluso WebSockets (no WebRTC porque no es admisible perder paquetes cuando se envían instrucciones).   
 
No obstante, cuando se trata de llevar el stream de video hasta el cliente que se ha conectado al servidor web, el protocolo HTTP entre servidor web y navegador no es adecuado porque el mecanismo de petición/respuesta en el que se basa HTTP no soporta la frecuencia de transmisión de frames que requiere el stream de video. La alternativa es que el navegador del móvil se comunique directamente con el emisor usando cualquiera de los tres mecanismos de comunicación que estamos considerando en este tutorial.    
 
### 4.1 MQTT   

En este caso, una vez que el navegador del dispositivo móvil ha obtenido del servidor web la página HTML, la comunicación entre el emisor del stream de video y el navegador que se ha conectado a la WebApp se realiza vía MQTT (el emisor publica frames y el script de la WebApp suscribe los frames). Simplemente hay que tener en cuenta que en este caso el puerto del bróker al que debe conectarse el script que ejecuta el navegador debe ser un puerto que trabaje con websocket. En el apartado 3.1 se indica cuáles son esos puertos en el caso de los bróker públicos y gratuitos recomendados.    
 
En la carpeta MQTT/WebApp se proporcionan los códigos de una WebApp (servidor en Python y template en HTML) y de un emisor que publica en el bróker los frames de vídeo para que lleguen al dispositivo móvil.   
 
### 4.2 WebSockets   
 
En este caso, el servidor web actúa además como proxy para conectar vía websocket el emisor con el receptor (el navegador que se ha conectado a la WebApp). El emisor envía los frames al servidor web vía Websockets y el servidor web reenvía el frame al navegador. En la carpeta Websockets/WebApp se proporcionan los códigos de una WebApp (servidor en Python y template en HTML) que actúa como proxy entre el emisor del stream de video y el cliente que se conecta a la WebAp.    

### 4.3 WebRTC 

PENDIENTE
