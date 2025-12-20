import cv2

def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo leer el frame")
            break

        # Dimensiones del frame original
        height, width, _ = frame.shape

        # Lado del cuadrado central (mitad del tamaño menor)
        side = min(width, height) // 2

        # Centro de la imagen
        cx = width // 2
        cy = height // 2

        # Coordenadas del cuadrado central
        x1 = cx - side // 2
        y1 = cy - side // 2
        x2 = cx + side // 2
        y2 = cy + side // 2

        # Recorte del cuadrado central
        cropped = frame[y1:y2, x1:x2]

        # Reescalar el recorte al tamaño original (zoom)
        zoomed = cv2.resize(
            cropped,
            (width, height),
            interpolation=cv2.INTER_LINEAR
        )

        # Mostrar ventanas
        cv2.imshow("Video original", frame)
        cv2.imshow("Zoom central ampliado", zoomed)

        # Salir con 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
