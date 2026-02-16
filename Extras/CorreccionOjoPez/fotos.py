import cv2
import os

def main():
    # Abrir la cámara (0 = cámara por defecto)
    print ("Preparando camara ...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("No se puede abrir la cámara")
        return

    foto_count = 1
    os.makedirs("fotos", exist_ok=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("No se pudo recibir frame. Saliendo...")
            break

        # Mostrar el video
        cv2.imshow("Camara", frame)

        # Esperar tecla (1 ms)
        key = cv2.waitKey(1) & 0xFF

        # Si se pulsa 'f', guardar la foto
        if key == ord('f'):
            filename = f"fotos/foto_{foto_count}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Foto guardada: {filename}")
            foto_count += 1

        # Salir con 'q'
        if key == ord('q'):
            break

    # Liberar
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
