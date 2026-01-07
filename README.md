# Tutorial de video streaming para el Drone Engineering Ecosystem   

## 1. Introducción
Una de las aplicaciones más habituales de los drones es la captación de imágenes. Un caso particular es el envío a tierra en tiempo real del stream de video capturado por la cámara del dron.    

La forma de implementar el video streaming depende del escenario concreto. No es lo mismo el caso en el que el emisor del vídeo sea la Raspberry Pi abordo y el receptor sea un portátil conectado al punto de acceso de la Raspberry Pi que el caso en el que tanto el emisor como el receptor están conectados a Internet y físicamente lejos. Además, existen varios protocolos de comunicación y herramientas para implementar video streaming, con sus ventajas en inconvenientes.    

En este tutorial describimos en detalle los diferentes escenarios, protocolos y herramientas. Además, proporcionamos los códigos necesarios para cada caso concreto. En particular consideraremos tres escenarios:   

1. Local: emisor y receptor (o receptores) conectados en la misma red de área local (LAN)
2. Global: emisor y receptor (o receptores) conectados a Internet
3. WebApp: receptor conectado a una WebApp (es un caso particular del anterior)
   
Por otra parte, consideraremos tres protocolos para implementar video streaming: MQTT, websockets y WebRTC.   

Naturalmente, otro escenario posible, que no se considera aquí, es que el dron tenga un sistema tema de transmisión de video por un canal específico que le conecta directamente con un receptor de vídeo conectado a la estación de tierra.    

## 2. Escenario local   

En este caso, el emisor y el receptor están conectados a la misma LAN y, por tanto, cada uno puede conectarse directamente con el otro conociendo su dirección IP dentro de la red. Por ejemplo, el emisor puede ser una Raspberry Pi (RPi) abordo del dron con una cámara conectada y el receptor puede ser un portátil que se ha conectado al punto de acceso WiFi ofrecido por la RPi. De hecho, puede haber varios receptores, todos ellos conectados a ese punto de acceso. Veamos la implementación de video streaming usando cada uno de los tres protocolos considerados en este tutorial.   

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
En la carpeta MQTT/redLocal pueden encontrarse los códigos de un emisor y un receptor. El emisor publica los frames del stream de video en un bróker mosquitto que se ejecuta en el mismo ordenador que el receptor. El receptor se ha suscrito a los frames de vídeo y por tanto los recibe y los muestra al usuario.   
 
Se observará inmediatamente que la fluidez del vídeo no es ideal, porque MQTT no está pensado para transmisión de datos grandes y frecuentes (como los frames de un stream de video). La fluidez puede ajustarse haciendo que los frames se envíen con menos calidad (menos bytes) y con menos frecuencia. En el código del emisor se indica con comentarios cómo controlar esos dos parámetros.   
 
### 2.2 Websockets   

Como ya se ha indicado el protocolo MQTT es ideal para comunicar mensajes cortos y poco frecuentes. Sin embargo, no es el mecanismo ideal para comunicar el stream de video, puesto la gestión que debe realizar el bróker introduce retardos que afectan a la fluidez del vídeo. Además, MQTT funciona sobre TCP/IP con lo cual se introducen retardos adicionales debido al control de flujo que realiza TCP para que no se pierdan paquetes en la transmisión.      

Una alternativa que mejora la experiencia de usuario es utilizar Websockets para la comunicación del stream de video. Este mecanismo utiliza también TCP/IP y, por tanto, incurre en esos retardos debidos al control de flujo, pero no necesita de la intermediación de ningún bróker. La gestión de la información que viaja es más eficiente que en el caso de MQTT y, por tanto, los retardos son mucho menores y la fluidez mucho mejor.   

Cuando se usa una comunicación de Websocket, uno de los agentes implicados (emisor o receptor) debe desempeñar el rol de servidor y el otro el rol de cliente. El servidor crea el websocket y queda a la espera de conexiones. El cliente se conecta al servidor usando la IP de éste en la LAN. La conexión se realiza utilizando el protocolo HTTP, exactamente igual que haría un navegador para conectarse a una página web (de ahí el término websocket). Una vez realizada la conexión, ésta se mantiene abierta creando un canal de comunicación bidireccional. A partir de ese momento, tanto el servidor como el cliente pueden desempeñar el rol de emisor o de receptor del stream de vídeo, que circula por el canal creado con mayor fluidez que en el caso de MQTT.    
 
En la carpeta Websockets/redLocal pueden encontrarse los códigos de un emisor y un receptor que utilizan websockets para implementar video streaming. En ese caso, el receptor es el que actúa de servidor del websocket, pero podría ser perfectamente al revés. Se observará que la fluidez es mucho mejor que en el caso de MQTT. No obstante, puede modificarse en el emisor la calidad del frame que se envía y la frecuencia de envío exactamente igual que en el caso del emisor vía MQTT.   

### 2.3 WebRTC   

El protocolo Websockets no es tampoco el mecanismo ideal ya sigue incurriendo en los retardos propios de TCP debidos al control de flujo y mecanismos de recuperación de paquetes perdidos. Una aplicación de video streaming no requiere de estos mecanismos puesto que la pérdida eventual de frames no necesariamente representa un excesivo perjuicio de la experiencia de usuario. El protocolo WebRTC (Web Real-Time Communication) se basan en UDP/IP y, por tanto, no espera confirmaciones de paquetes, lo cual da como resultado una transmisión de mayor fluidez.    

De nuevo, uno de los agentes implicados (emisor o receptor) debe actuar como servidor y el otro como cliente. El cliente se conecta al servidor usando la IP de éste en la LAN. Para establecer la conexión el cliente y servidor intercambian algunos mensajes por websocket. Básicamente el emisor del video stream debe enviar por el websocket una oferta y el receptor debe responder con una aceptación. En ese intercambio, emisor y receptor se dan a conocer mutuamente información necesaria para la comunicación del stream de video (por ejemplo, sus IPs dentro de la LAN). Una vez establecida la conexión el emisor envía el stream de video que llegará al receptor con menor retraso y mejor fluidez, como corresponde al uso de UDP en vez de TCP, aunque con posibles pérdidas de paquetes que, si bien serían inadmisibles si se están enviando instrucciones, no van a afectar significativamente a la experiencia de usuario en el caso de video streaming.    
 
En la carpeta WebRTC/redLocal pueden encontrarse los códigos de un emisor (que en este caso es el que actúa como servidor) y un receptor que utilizan WebRTC para implementar video streaming.    

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
En la carpeta MQTT/redGlobal pueden encontrarse los códigos de un emisor y un receptor que se comunican el stream de video a través de un bróker público y gratuito. Los códigos son exactamente iguales que los del caso del escenario local excepto por lo que respecta a la conexión con el bróker. En los comentarios del código se indica cómo conectarse al resto de brokers públicos mencionados.   
 
### 3.2 Websockets

En un escenario global el emisor y receptor están conectados a Internet pero pertenecen a LANs diferentes y no tienen asignadas IP públicas. Por tanto, no es posible establecer una conexión directa entre un cliente y un servidor, tal y como sí es posible en el caso del escenario local.   

En este caso, la comunicación vía Websocket requiere de un proxy que haga de intermediario. El proxy debe estar conectado a internet y tener asignada una IP pública. El proxy actuará de servidor y creará el Websocket de manera que tanto el emisor como el receptor se conectarán al proxy usando la IP pública de éste. Ahora el emisor enviará el video stream al proxy que lo reenviará al receptor.   
 
En la carpeta Websocket/redGlobal pueden encontrarse los códigos de un emisor, un receptor y un proxy. Es importante tener en cuenta que el proxy debe ejecutarse en un ordenador conectado a internet y con una IP pública para que tanto el emisor como el receptor puedan conectarse.   

### 3.3 WebRTC   

Al igual que en el caso de Websockets, si se usa WebRTC en un escenario global es necesaria la intervención de un proxy que hará el rol de servidor al que se conectarán tanto el emisor como el receptor.   
 
En la carpeta WebRTC/redGlobal pueden encontrarse los códigos de un emisor, un receptor y un proxy, que también debe ejecutarse en un ordenador con IP pública. En la implementación propuesta es posible enviar el stream de video a varios receptores. Para que eso sea posible es necesario que el emisor envíe una oferta a cada uno de los receptores. Por ese motivo, el proxy es algo más complejo ya que tiene que mantener una lista de receptores para avisar al emisor de que se requiere una nueva oferta cada vez que se conecta un receptor y luego poder reenviar la oferta al receptor correspondiente.    

En el caso de que el emisor y el receptor pertenezcan a LANs diferentes, el intercambio de oferta y respuesta no es suficiente para establecer la conexión, puesto que de nada sirve que el emisor conozca la IP del receptor en la LAN de este. Necesita información adicional que le permita alcanzar al receptor en Internet. Para ello, el receptor debe enviar al emisor información sobre la dirección IP pública del router al que esté conectado e información adicional sobre cóomo está conectado el receptor al router. Para obtener esta información el receptor necesita la ayuda de un servidor externo de tipo STUN (Session Traversal Utilities for NAT). Este servidor recopila la información y se la entrega al receptor para que éste la envíe por websocket al emisor a través del proxy (igual que envió la aceptación de la oferta). En realidad, el servidor STUN puede enviar al receptor varias alternativas que denominamos candidatos. Cada candidato es un posible camino para llegar al receptor a través de internat. El receptor enviará al emisor todos los candidatos que le proporcione el servidor STUN. El emisor guardará todos esos candidatos para poder elegir el mejor y realizar la transmisión del stream a través de la opción elegida.    

En el caso de que el receptor pertenezca a una LAN con altos niveles de protección (cortafuegos, etc.), es posible que los candidatos proporcionados por el servidor STUN no permitan la conexión. En esos casos, es necesario uitilizar un servidor de tipo TURN (Traversal Using Relays around NAT). En este caso, los candidatos que proporciona el servidor TURN incluyen el camino que permite que el video stream pase por el propio servidor TURN para que este los retrasmita al receptor (por eso se llaman candidatos de tipo relay). Esta estrategia permite la transmisión en la mayoría de los casos, aunque el éxito no está asegurado porque es posible que el receptor pertenezca a una red en la que está deshabilitadas cierto tipo de recepciones por UDP (eso puede ocurrir en receptores de instituciones oficiales como por ejemplo una Universidad). Naturalmente, el uso de un servidor TURN incurre en ciertos retardos que pueden afectar a la fluidez del video, en comparación con las situaciones en las que no es necesaria su intervención.   

En los códigos proporcionados en la carpeta WebRTC/redGlobal tanto el emisor como el receptor envian candidatos apoyandose en servidores STUN y TURN. En la configuración de la conexión se indica qué servidores van a usarse. Existen muchas opciones gratuitas para servidor STUN. También hay opciones gratuitas para servidores TURN aunque en muchos casos se requiere registrarse en la organiación que los facilita para obtener unas claves de acceso. Una opción recomentada es https://www.metered.ca/tools/openrelay/.   


## 4. WebApp   

Este escenario es un caso particular del escenario global, en el que el cliente es una WebApp. Esto permite que el video stream se reciba en un dispositivo móvil que se ha conectado a la WebApp.   
 
Una WebApp es un servidor que sirve páginas web, igual que el servidor que sirve las páginas web de www.upc.edu. Pero las páginas web que sirve no tienen noticias o enlaces a documentos. Tienen botones de tal manera que cuando nos conectamos a la web desde el navegador del móvil lo que nos aparece en la pantalla es una página con botones, uno de los cuales, por ejemplo, nos permite hacer despegar el dron. Además, la WebApp puede proporcionar al cliente el stream de video que recibe del emisor para que el usuario puede verlo en su dispositivo móvil.    
 
Normalmente, la comunicación entre el servidor web y el navegador del dispositivo móvil que se conecta se realiza mediante el protocolo HTTP. Al conectarnos al servidor se realiza un GET para obtener el fichero HTML de la página principal y si se pulsa un botón de esa página se realiza un POST que permite al servidor detectar que el usuario quiere, por ejemplo, despegar el dron. La comunicación entre el servidor web y el dispositivo que controla el dron puede realizarse mediante MQTT o incluso WebSockets (no WebRTC porque no es admisible perder paquetes cuando se envían instrucciones).   
 
No obstante, cuando se trata de llevar el stream de video hasta el cliente que se ha conectado al servidor web, el protocolo HTTP entre servidor web y navegador no es adecuado porque el mecanismo de petición/respuesta en el que se basa HTTP no soporta la frecuencia de transmisión de frames que requiere el stream de video. La alternativa es que el navegador del móvil se comunique directamente con el emisor usando cualquiera de los tres mecanismos de comunicación que estamos considerando en este tutorial.    
 
### 4.1 MQTT   

En este caso, una vez que el navegador del dispositivo móvil ha obtenido del servidor web la página HTML, la comunicación entre el emisor del stream de video y el navegador que se ha conectado a la WebApp se realiza vía MQTT (el emisor publica frames y el script de la WebApp suscribe los frames). Simplemente hay que tener en cuenta que en este caso el puerto del bróker al que debe conectarse el script que ejecuta el navegador debe ser un puerto que trabaje con websocket. En el apartado 3.1 se indica cuáles son esos puertos en el caso de los bróker públicos y gratuitos recomendados.    
 
En la carpeta MQTT/WebApp se proporcionan los códigos de una WebApp (servidor en Python y template en HTML) y de un emisor que publica en el bróker los frames de vídeo para que lleguen al dispositivo móvil.   
 
### 4.2 WebSockets   
 
En este caso, el servidor web actúa además como proxy para conectar vía websocket el emisor con el receptor (el navegador que se ha conectado a la WebApp). El emisor envía los frames al servidor web vía Websockets y el servidor los reenvía al navegador. En la carpeta Websockets/WebApp se proporcionan los códigos de una WebApp (servidor en Python y template en HTML) que actúa como proxy entre el emisor del stream de video y el cliente que se conecta a la WebAp.    

### 4.3 WebRTC 

En la carpeta WebRTC/WebApp pueden encontrarse los códigos de una WebApp que facilita la transmisión del stream de video entre un emisor en python y el cliente que se conecta a la Webapp. Como corresponde a la comunicación via WebRTC, el emisor y el cliente interambian mensajes iniciales por websocket a través del servidor, que lo único que hace es hacer de puente entre ambos. Esos mensajes incluyen los candidatos obtenidos de los servidores STUN y TURN, tal y como se ha explicado en el apartado 3.3. Una vez puestos de acuerdo el stream de video fluye desde el emisor al cliente de forma muy fluida. La implementación propuesta también permite que varios clientes reciban el stream simultáneamente.   

Esta opción es la ideal para que el stream de video captado por el dron mientras vuela en el DroneLab pueda ser visto en los dispositivos móviles de los visitantes. En esa situación el portátil en el que se ejecuta el programa emisor del video stream estará conectado a la Wifi del DroneLab. En el caso de que los dispositivos móviles también estén conectados a esa Wifi la transmisión del video se realizará sin intervención de servidores STUN o TURN, y el video se recibirá con gran fluidez. En el caso de los dispositivos móviles que estén conectados a otras redes (por ejemplo, al servicio de datos de su compañía telefónica) será necesaria la intermediación de servidores STUN y muy probablemente TURN, con lo que la fluidez puede verse algo afectada, e incluso es posible que la conexión no pueda establecerse.    

La implementación que hay aquí permite a varios clientes web conectarse y recibir el stream de video. Se ha incluido la mecánica necesaria para que cuando un cliente web se desconecta se cierre el canal WebRTC por el que se emitía el stream de video para ese cliente. Eso hace que el sistema sea más escalable y permite muchos clientes web simultáneos. Si no se hace esto, el sistema se satura al conectar 5 o más clientes. Es lo que puede pasar en el resto de implemmentaciones de WebRTC que hay en este repositorio en las que no se ha introducido la mecánica de desconexión.   

Es importante observar que para que la desconexión de un cliente web funcione bien, cada cliente web debe tener su propio track, que se cerrará en el momento de la desconexión sin afectar a los otros clientes web, cada uno de los cuales tiene su propio track. En el resto de implementacione de este repositorio, todos los clientes de WebRTC comparten el mismo track, con lo que si se desconectase uno de ellos y se cerrara el track, se congelaría el stream de video en todos los demás.   


## 5. Extras     
En la carpeta de extras hay algunos códigos que no corresponden a ninguno de los escenarios anteriores y no son, por tanto, de aplicación en el ecosistema, pero que han resultado de mucha utilidad como pasos intermedios para la implementación que se ha descrito en el punto 4.3 (que ha sido la más complicada de todas).    

### 5.1 ServidorFlaskWebRTC   
Esta es una webapp que sirve al cliente el stream de video que el propio servidor captura. No es de aplicación en el ecosistema porque no interesa el video de la máquina en la que se ejecuta el servidor, sino el video del dron.    

### 5.2 ProxyWebRTC-clientesVarios    
Aquí tenemos un programa en python que hace de proxy para facilitar la comunicación entre emisor y receptor. Este proxy NO es una web app. Simplemente permite que emisor y receptos puedan ponerse de acuerdo a través del proxy que naturalmente debe tener una IP publica. Hay dos tipos de receptores. Uno es un programa en python y otro es un HTML+javascript que se ejecuta usando un navegador.   

### 5.3 ReceptorWebRTCGlobalCs    
Este caso si puede ser de aplicación en el contexto del ecosistema porque se trata de recibir el video stream por WebRTC y mostrarlo en un formulario en C#. De momento, no sabemos cómo hacer para recibir el stream directamente en el formulario, pero si sabemos hacer que lo reciba un script de python y éste lo envie al formulario mediante un socket interno. Eso es lo que hay implementado en esta carpeta.   

Hay que poner en marcha el proxyWebRTC, entonces poner en marcha el formulario C#, que esta en la carpeta Receptor, y después poner en marcha el senderGlobalWebRTC. El formulario pondrá en marcha el script receiverParaCs, que es prácticamente igual al receiverGlobalWebRTC, pero con los cambios necesarios para enviar los frames al formulario, en lugar de mostrarlos en una ventana de OpenCV.   

### 5.4 ServidorVideoTelemetría   
La comunicación via WebRTC puede usarse también para el envío de datos, como por ejemplo, datos de telemetría. Un paquete de datos de telemetría es mucho más pequeño que un frame de video. Por tanto, podría enviarse pertectamente usando MQTT o Websockets. Sin embargo, también ocurre en ese caso como con los frames de video. No es especialmente grave que se pierda algún paquete de datos de telemetría de vez en cuando, cosa que puede pasar al usar WebRTC, debido al uso de UDP. Por tanto, si usamos WebRTC para enviar datos de telemetría, podríamos subir la frecuencia de envío de esos datos si fuese necesario.   

En la carpeta ServidorVideoTelemetría puede encontrarse el código de una webapp que muestra al usuario el stream de video (como en casos anteriores) y también muestra un mapa satelital en el que se representa la posición del dron en cada momento. Por tanto, el cliente web recibe por WebRTC tanto el stream de vídeo como los datos de telemetría (solo lat, lon y heading). El servidor web no tiene ninguna novedad respecto al indicado en el apartado 4.3, puesto que lo único que tiene que hacer es retrasmitir de un lado al otro los mensajes que llegan por el websocket. En emisor si que tiene novedades, porque ahora debe enviar por WebRTC también los datos de telemetría. Para ello usa la librería DronLink que ofrece funciones para conectarse al dron y para obtener los datos de telemetría.   

Como aportación extra, el cliente web puede tomar fotos y también grabar vídeos que se almacenan localmente.   

### 5.5 Corrección Ojo de Pez    
Esa carpeta tiene el código necesario para realizar la corrección de imágenes distorsionadas por el efecto Ojo de Pez. Con frecuencia, las cámaras que se montan en un dron para vuelos FPV producen imágenes con el efecto Ojo de Pez, que introducen una distorsión que puede ser adecuada para el vuelo FPV, pero que puede dificultar la toma de imágenes para realizar operaciones como reconocimiento de objetos o stitching.  

La distorsión puede corregirse aplicando el código que está en el fichero *calibrate.py*. Este código necesita una colección de imágenes tomadas con la cámara, que se encuentran en la carpeta input21. El código calcula unos parámetros necesarios para la corrección y genera el fichero *calibration_data_px.yaml* que se encuentra en la carpeta output21. Ese fichero puede usarse ya para la corrección de las imágenes tomadas por la cámara. En el fichero *undistortVideo.py* hay un código que usa el corrector para corregir las imágenes que hay en input21. El resultado está en output21. Además, en el fichero *demostrador.py* hay un código que captura el stream de video de la camara, hace la corrección y permite hacer un zoom de la imagen corregida. También puede detectar contornos del color que se seleccione. Naturalmente, cada cámara necesita su corrector. El corrector que hay en esta carpeta es el que corresponde a la cámara FPV Camera Walksnail Avatar HD.   

La imagen siguiente muestra el programa *demostrador.py* en acción. La imagen de la derecha es la original con efecto ojo de pez. La de la izquierda es la imagen corregida, con un poco de zoom y con reconocimiento de contornos de color verde.     
 
<img width="1657" height="608" alt="image" src="https://github.com/user-attachments/assets/9a6692c3-d727-44bd-b1eb-a43e4feb6d34" />


### 5.6 VideoWebRTC_desdeMovil    
Esta carpeta contiene una webapp que permite enviar por WebRTC al receptor el stream de video de la cámara del dispositivo móvil que se conecta. No tiene mayor novedad respecto al mecanismo WebRTC. Lo más importante es que para que el dispositivo movil capture el stream de video de la cámara es necesario que la webapp trabaje con https y por tanto use certificados.    



