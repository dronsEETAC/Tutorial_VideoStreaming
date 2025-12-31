import threading
import time
import cv2
import numpy as np
import yaml
import tkinter as tk
from PIL import Image, ImageTk


def start_video ():
    global cap,  cam_matrix, dist_coefs, new_cam_mtx
    global x, y, w, h

    yamlname = 'calibration_data_px.yaml'
    stream_source = 0  # cámbialo si necesitas usar un stream remoto

    with open(yamlname) as f:
        data = yaml.safe_load(f)

    cam_matrix = np.array(data['camera_matrix'])
    dist_coefs = np.array(data['distortion_coefficients'])

    cap = cv2.VideoCapture(stream_source)

    if not cap.isOpened():
        print("No se pudo abrir el stream de video.")
        return
    h,w =480,640
    new_cam_mtx, roi = cv2.getOptimalNewCameraMatrix(cam_matrix, dist_coefs, (w, h), 1, (w, h))
    x, y, w, h = roi

    threading.Thread (target = show_video).start()

def show_video ():
    global video_original_label,  video_corregido_label

    while True:
        ret, img = cap.read()
        if not ret:
            print("No se pudo leer un frame del stream.")
            break
        dst = img
        if correct:
            u_img = cv2.undistort(dst, cam_matrix, dist_coefs, None, new_cam_mtx)
            dst = u_img[y:y + h, x:x + w]

        dst = apply_zoom(dst)

        if selected_color:
            detect_color(dst)

        frame_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img2 = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img2)
        video_original_label.imgtk = imgtk
        video_original_label.configure(image=imgtk)

        # me aseguro que la imagen corregida tiene el tamaño que toca
        frame_resized = cv2.resize(
            dst,
            (640, 480),
            interpolation=cv2.INTER_LINEAR
        )

        frame_rgb2 = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img3 = Image.fromarray(frame_rgb2)
        imgtk2 = ImageTk.PhotoImage(image=img3)
        video_corregido_label.imgtk = imgtk2
        video_corregido_label.configure(image=imgtk2)

        time.sleep (0.1)

    cap.release()
    cv2.destroyAllWindows()

def toggle_correct ():
    global correct
    correct = not correct

def set_color (color):
    global selected_color
    selected_color = color

def update_zoom (value):
    global zoom_factor
    zoom_factor = float(value)

def apply_zoom(frame):
    h, w = frame.shape[:2]
    sidex, sidey = int(w/zoom_factor), int(h/zoom_factor)

    cx, cy = w // 2, h // 2
    x1 = cx - sidex // 2
    y1 = cy - sidey // 2
    x2 = cx + sidex // 2
    y2 = cy + sidey // 2

    cropped = frame[y1:y2, x1:x2]
    zoomed = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
    return zoomed

def clear_color ():
    global selected_color
    selected_color = None

def detect_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    ranges = {
            "red": [
                ((0, 120, 70), (10, 255, 255)),
                ((170, 120, 70), (180, 255, 255))
            ],
            "green": [((36, 50, 70), (89, 255, 255))],
            "blue": [((90, 50, 70), (128, 255, 255))],
            "yellow": [((20, 100, 100), (35, 255, 255))]
    }

    mask = None
    for lower, upper in ranges[selected_color]:
            m = cv2.inRange(hsv, np.array(lower), np.array(upper))
            mask = m if mask is None else mask | m

    contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)


def main():
    global selected_color
    global correct
    global zoom_factor
    global video_original_label,  video_corregido_label

    correct = False
    selected_color = None
    zoom_factor = 1.0
    root = tk.Tk()
    root.title("Webcam con Zoom y Detección de Color")
    controls = tk.Frame(root)
    controls.pack(side=tk.LEFT, fill=tk.Y, padx=5)

    btn_start = tk.Button(
            controls, text="Iniciar vídeo", command=start_video
    )
    btn_start.pack(fill=tk.X, pady=2)

    btn_correct = tk.Button(
            controls, text="Corregir imagen", command=toggle_correct
        )
    btn_correct.pack(fill=tk.X, pady=2)

    tk.Label(controls, text="Zoom").pack(pady=(10, 0))
    zoom_scale = tk.Scale(
            controls,
            from_=1.0,
            to=10.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            command=update_zoom
    )
    zoom_scale.set(1.0)
    zoom_scale.pack(fill=tk.X)

    tk.Label(controls, text="Detectar color").pack(pady=(10, 0))

    colors = [
            ("Amarillo", "yellow"),
            ("Rojo", "red"),
            ("Verde", "green"),
            ("Azul", "blue")
    ]

    for name, color in colors:
            tk.Button(
                controls,
                text=name,
                bg=color,
                command=lambda c=color: set_color(c)
    ).pack(fill=tk.X, pady=1)

    btn_clear = tk.Button(
            controls, text="Sin detección", command=clear_color
    )
    btn_clear.pack(fill=tk.X, pady=5)
    # Paneles de vídeo
    video_original_label = tk.Label(root)
    video_original_label.pack(side=tk.RIGHT, padx=5, pady=5)
    video_corregido_label = tk.Label(root)
    video_corregido_label.pack(side=tk.RIGHT, padx=5, pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
