# Dipendenze necessarie:
# pip install pyrealsense2
# pip install opencv-contrib-python
# pip install numpy

import pyrealsense2 as rs
import numpy as np
import cv2
import cv2.aruco as aruco
import sys # Per sys.exit()

def aruco_pose_estimation_realsense_factory_intrinsics():
    # 1. Configurazione della telecamera RealSense
    pipeline = rs.pipeline()
    config = rs.config()

    # Abilita il flusso di colore e profondità
    config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

    # Inizia lo streaming e ottieni il profilo per gli intrinseci
    print("Avvio della pipeline RealSense e recupero parametri intrinseci...")
    profile = None
    try:
        profile = pipeline.start(config)
        # Aspetta qualche frame per stabilizzare il pipeline
        for _ in range(30): # ~1 secondo a 30fps
            pipeline.wait_for_frames()
    except Exception as e:
        print(f"ERRORE: Impossibile avviare la telecamera RealSense. Assicurati che sia connessa e non in uso.")
        print(f"Dettagli errore: {e}")
        sys.exit(1)

    # 2. Recupera i parametri intrinseci della telecamera dal flusso di colore usando l'API pyrealsense2
    # Questi sono i parametri predefiniti di fabbrica della tua RealSense D415.
    color_intrinsics = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()

    camera_matrix = np.array([[color_intrinsics.fx, 0, color_intrinsics.ppx],
                              [0, color_intrinsics.fy, color_intrinsics.ppy],
                              [0, 0, 1]], dtype=np.float32)

    dist_coeffs = np.array([color_intrinsics.coeffs[0], color_intrinsics.coeffs[1], color_intrinsics.coeffs[2],
                            color_intrinsics.coeffs[3], color_intrinsics.coeffs[4]], dtype=np.float32)

    print("Parametri intrinseci della RealSense recuperati (di fabbrica, NON calibrati):")
    print("Matrice della telecamera:\n", camera_matrix)
    print("Coefficienti di distorsione:\n", dist_coeffs)
    print("\nAVVISO: I valori di posa potrebbero essere imprecisi senza una calibrazione personalizzata.")


    # 3. Allineamento dei frame di profondità al frame di colore
    align_to = rs.stream.color
    align = rs.align(align_to)

    # 4. Definizione del dizionario ArUco e parametri
    # Scegli il dizionario ArUco che stai usando (es. DICT_7X7_250)
    ARUCO_DICT = aruco.DICT_7X7_250 # <-- MODIFICA QUESTO SE USI UN DIZIONARIO DIVERSO
    aruco_dict = aruco.getPredefinedDictionary(ARUCO_DICT)
    parameters = aruco.DetectorParameters()

    # Dimensione reale del lato del marker ArUco in METRI (ES. se il lato è 5 cm, usa 0.05)
    # QUESTO VALORE DEVE CORRISPONDERE ALLA DIMENSIONE REALE DEL TUO MARKER STAMPATO!
    MARKER_LENGTH = 0.10  # Metri <-- MODIFICA QUESTO CON IL VALORE REALE DEL TUO MARKER

    print(f"\nPronto per la stima della posa ArUco (con terna, usando intrinseci di fabbrica).")
    print(f"Utilizzando dizionario: {ARUCO_DICT} e marker lungo {MARKER_LENGTH} metri.")
    print("Premi 'q' per uscire.")

    try:
        while True:
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)
            color_frame = aligned_frames.get_color_frame()

            if not color_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

            corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

            if ids is not None:
                aruco.drawDetectedMarkers(color_image, corners) 

                rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(corners, MARKER_LENGTH, camera_matrix, dist_coeffs)

                for i, _id in enumerate(ids):
                    rvec = rvecs[i]
                    tvec = tvecs[i]

                    # Disegna gli assi sulla terna (più grandi e sottili)
                    cv2.drawFrameAxes(color_image, camera_matrix, dist_coeffs, rvec, tvec, MARKER_LENGTH * 0.8, thickness=1)

                    x, y, z = tvec[0]
                    distance_cm = z * 100 

                    rotation_matrix, _ = cv2.Rodrigues(rvec)
                    sy = np.sqrt(rotation_matrix[0,0] * rotation_matrix[0,0] +  rotation_matrix[1,0] * rotation_matrix[1,0])
                    singular = sy < 1e-6

                    if not singular:
                        roll = np.arctan2(rotation_matrix[2,1], rotation_matrix[2,2])
                        pitch = np.arctan2(-rotation_matrix[2,0], sy)
                        yaw = np.arctan2(rotation_matrix[1,0], rotation_matrix[0,0])
                    else:
                        roll = np.arctan2(-rotation_matrix[1,2], rotation_matrix[1,1])
                        pitch = np.arctan2(-rotation_matrix[2,0], sy)
                        yaw = 0 

                    # Scrive l'ID del marker sull'immagine con una dimensione più piccola
                    center_x = int(corners[i][0][0][0] + (corners[i][0][2][0] - corners[i][0][0][0]) / 2)
                    center_y = int(corners[i][0][0][1] + (corners[i][0][2][1] - corners[i][0][0][1]) / 2)
                    text_x = center_x - 30 
                    text_y = center_y - 30

                    cv2.putText(color_image, f"ID: {_id[0]}", (text_x, text_y), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 1, cv2.LINE_AA) 

                    print(f"ID Marker: {_id[0]}")
                    print(f"  Posizione (X, Y, Z): ({x:.4f} m, {y:.4f} m, {z:.4f} m)")
                    print(f"  Distanza dalla Camera (Z): {distance_cm:.2f} cm")
                    print(f"  Orientamento (Roll, Pitch, Yaw): ({np.degrees(roll):.2f}°, {np.degrees(pitch):.2f}°, {np.degrees(yaw):.2f}°)")
                    print("-" * 30)

            cv2.imshow('ArUco Pose Estimation (Factory Intrinsics)', color_image)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    aruco_pose_estimation_realsense_factory_intrinsics()