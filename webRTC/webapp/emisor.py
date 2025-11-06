import asyncio
import json
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaBlackhole, MediaRecorder
from av import VideoFrame
import numpy as np
import websockets
import logging
import requests
import time
import platform

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class VideoStreamTrackCustom(VideoStreamTrack):
    """
    Track personalizado para transmitir video desde la cámara
    """

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera = cv2.VideoCapture(camera_index)
        if not self.camera.isOpened():
            # Intentar con otras cámaras
            for i in range(1, 5):
                self.camera = cv2.VideoCapture(i)
                if self.camera.isOpened():
                    logging.info(f"Cámara encontrada en índice {i}")
                    break

        if not self.camera.isOpened():
            # Crear video de prueba si no hay cámara
            logging.warning("No se pudo abrir cámara, usando video de prueba")
            self.test_video = True
            self.frame_count = 0
        else:
            self.test_video = False
            # Configurar cámara
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 15)  # Reducir FPS para mejor estabilidad
            logging.info("Cámara inicializada correctamente")

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        if self.test_video:
            # Generar frame de prueba
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            self.frame_count += 1
            # Agregar texto informativo
            cv2.putText(frame, f"Video Test Frame {self.frame_count}", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            ret, frame = self.camera.read()
            if not ret:
                logging.warning("No se pudo capturar frame, reintentando...")
                # Reintentar
                ret, frame = self.camera.read()
                if not ret:
                    # Crear frame de error
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, "ERROR: No se pudo capturar frame", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Convertir BGR a RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Crear VideoFrame
        video_frame = VideoFrame.from_ndarray(frame_rgb, format='rgb24')
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame

    def release(self):
        if hasattr(self, 'camera') and not self.test_video:
            self.camera.release()


class WebRTCVideoSender:
    def __init__(self):
        self.websocket_url = None
        self.pc = None
        self.connected = False
        self.websocket = None

    def get_websocket_port(self, max_retries=10):
        """Obtener el puerto WebSocket del servidor Flask"""
        for attempt in range(max_retries):
            try:
                logging.info(f"Intentando obtener puerto WebSocket (intento {attempt + 1}/{max_retries})...")
                response = requests.get("http://147.83.249.79:8106/websocket-port", timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    port = data["port"]
                    self.websocket_url = f"ws://147.83.249.79:{port}"
                    logging.info(f"✅ URL WebSocket obtenida: {self.websocket_url}")
                    return True
                else:
                    logging.warning(f"Servidor respondió con código: {response.status_code}")

            except requests.exceptions.ConnectionError:
                logging.warning(f"Servidor Flask no disponible, reintentando en 2 segundos...")
            except Exception as e:
                logging.error(f"Error obteniendo puerto WebSocket: {e}")

            time.sleep(2)  # Esperar antes de reintentar

        logging.error("❌ No se pudo conectar al servidor Flask después de varios intentos")
        return False

    async def setup_webrtc(self):
        try:
            # Crear PeerConnection con configuración mejorada
            self.pc = RTCPeerConnection()

            # Configuración mejorada de ICE
            self.pc._rtcConfiguration = {
                "iceServers": [
                    {"urls": ["stun:stun.l.google.com:19302"]},
                    {"urls": ["stun:stun1.l.google.com:19302"]}
                ],
                "iceTransportPolicy": "all"
            }

            # Crear y agregar el track de video
            logging.info("Inicializando cámara...")
            self.video_track = VideoStreamTrackCustom()
            self.pc.addTrack(self.video_track)

            # Configurar manejadores de eventos
            @self.pc.on("iceconnectionstatechange")
            async def on_iceconnectionstatechange():
                state = self.pc.iceConnectionState
                logging.info(f"Estado ICE: {state}")
                if state == "failed" or state == "disconnected":
                    logging.error("Conexión ICE falló")
                    await self.cleanup()

            @self.pc.on("connectionstatechange")
            async def on_connectionstatechange():
                state = self.pc.connectionState
                logging.info(f"Estado conexión WebRTC: {state}")
                if state == "connected":
                    self.connected = True
                    logging.info("✅ Conexión WebRTC establecida - Transmitiendo video...")
                elif state == "failed":
                    logging.error("❌ Conexión WebRTC falló")
                    await self.cleanup()
                elif state == "closed":
                    logging.info("Conexión WebRTC cerrada")
                    self.connected = False

            @self.pc.on("icecandidate")
            async def on_icecandidate(candidate):
                if candidate and self.websocket:
                    try:
                        await self.websocket.send(json.dumps({
                            "type": "ice_candidate",
                            "candidate": {
                                "candidate": candidate.candidate,
                                "sdpMid": candidate.sdpMid,
                                "sdpMLineIndex": candidate.sdpMLineIndex
                            }
                        }))
                        logging.info("ICE candidate enviado al servidor")
                    except Exception as e:
                        logging.error(f"Error enviando ICE candidate: {e}")

            # Crear offer con mejores opciones
            logging.info("Creando oferta WebRTC...")
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            logging.info("Oferta WebRTC creada")

            return offer

        except Exception as e:
            logging.error(f"Error en setup WebRTC: {e}")
            raise

    async def connect_and_stream(self):
        # Primero obtener el puerto WebSocket
        if not self.get_websocket_port():
            return

        try:
            logging.info(f"Conectando a WebSocket: {self.websocket_url}")

            # Configurar timeout para la conexión WebSocket
            self.websocket = await websockets.connect(
                self.websocket_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )

            logging.info("✅ Conectado al servidor WebSocket")

            # Crear y enviar offer
            offer = await self.setup_webrtc()
            await self.websocket.send(json.dumps({
                "type": "offer",
                "sdp": offer.sdp
            }))
            logging.info("📤 Offer WebRTC enviado")

            # Esperar respuesta
            response = await self.websocket.recv()
            data = json.loads(response)
            logging.info(f"📥 Respuesta recibida: {data['type']}")

            if data["type"] == "answer":
                await self.pc.setRemoteDescription(
                    RTCSessionDescription(sdp=data["sdp"], type="answer")
                )
                logging.info("Answer procesado correctamente")

            # Mantener la conexión activa
            keepalive_count = 0
            while self.connected:
                try:
                    # Esperar mensajes (ICE candidates, ping, etc.)
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                    data = json.loads(message)

                    if data.get("type") == "ice_candidate":
                        logging.info("ICE candidate recibido del servidor")
                        if data["candidate"]:
                            await self.pc.addIceCandidate(data["candidate"])
                    elif data.get("type") == "ping":
                        await self.websocket.send(json.dumps({"type": "pong"}))
                        keepalive_count += 1
                        if keepalive_count % 10 == 0:
                            logging.info("Conexión WebSocket activa")

                except asyncio.TimeoutError:
                    # Timeout normal, continuar streaming
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logging.warning("Conexión WebSocket cerrada")
                    break
                except Exception as e:
                    logging.error(f"Error procesando mensaje: {e}")
                    break

            # Si salimos del loop pero aún estamos conectados, esperar un poco
            if self.connected:
                logging.info("Esperando finalización de transmisión...")
                await asyncio.sleep(5)

        except websockets.exceptions.InvalidURI:
            logging.error("❌ URL WebSocket inválida")
        except websockets.exceptions.InvalidHandshake:
            logging.error("❌ Handshake WebSocket falló")
        except ConnectionRefusedError:
            logging.error("❌ Conexión rechazada - Verifica que el servidor esté ejecutándose")
        except Exception as e:
            logging.error(f"❌ Error en conexión: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Limpiar recursos"""
        logging.info("Limpiando recursos...")
        self.connected = False

        if hasattr(self, 'video_track'):
            self.video_track.release()
            logging.info("Cámara liberada")

        if self.pc:
            await self.pc.close()
            logging.info("Conexión WebRTC cerrada")

        if self.websocket:
            await self.websocket.close()
            logging.info("Conexión WebSocket cerrada")


async def main():
    logging.info("🚀 Iniciando emisor de video WebRTC...")
    logging.info(f"Sistema: {platform.system()} {platform.release()}")

    sender = WebRTCVideoSender()
    await sender.connect_and_stream()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Emisor detenido por el usuario")
    except Exception as e:
        logging.error(f"❌ Error fatal: {e}")