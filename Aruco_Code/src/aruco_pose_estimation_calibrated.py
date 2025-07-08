# Dipendenze necessarie:
# pip install pyrealsense2
# pip install opencv-contrib-python
# pip install numpy

import pyrealsense2 as rs
import numpy as np
import cv2
import cv2.aruco as aruco
import sys  # Per sys.exit()
import os   # Per controllare l'esistenza del file di calibrazione

def aruco_pose_estimation_calibrated():
    # --- PARAMETRI DI CONFIGURAZIONE ---
    # Nome del file dove sono stati salvati i parametri di calibrazione
    # Assicurati che questo nome corrisponda al file generato da realsense_calibrate.py
    CALIBRATION_FILE = 'realsense_custom_calibration.npz' 

    # Scegli il dizionario ArUco che stai usando (es. DICT_7X7_250)
    ARUCO_DICT = aruco.DICT_7X7_250 # <-- MODIFICA QUESTO SE USI UN DIZIONARIO ArUco

    # Dimensione reale del lato del marker ArUco in METRI (es. se il lato è 10 cm, usa 0.10)
    # QUESTO VALORE DEVE CORRISPONDERE ALLA DIMENSIONE REALE DEL TUO MARKER STAMPATO!
    MARKER_LENGTH = 0.10  # Metri <-- MODIFICA QUESTO CON IL VALORE REALE DEL TUO MARKER

    # --- INIZIO SCRIPT ---

    # 1. Carica i parametri di calibrazione personalizzati
    if not os.path.exists(CALIBRATION_FILE):
        print(f"ERRORE: File di calibrazione '{CALIBRATION_FILE}' non trovato.")
        print("Per favore, esegui prima lo script 'realsense_calibrate.py' per calibrare la telecamera e generare questo file.")
        sys.exit(1) # Esce dal programma se il file non è presente

    try:
        calib_data = np.load(CALIBRATION_FILE)
        camera_matrix = calib_data['camera_matrix']
        dist_coeffs = calib_data['dist_coeffs']
        print(f"Parametri di calibrazione caricati con successo da '{CALIBRATION_FILE}'.")
        print("Matrice della telecamera (camera_matrix):\n", camera_matrix)
        print("Coefficienti di distorsione (dist_coeffs):\n", dist_coeffs)
    except Exception as e:
        print(f"ERRORE: Impossibile caricare o leggere i parametri di calibrazione da '{CALIBRATION_FILE}'.")
        print(f"Dettagli errore: {e}")
        print("Il file potrebbe essere danneggiato. Prova a rieseguire la calibrazione.")
        sys.exit(1) # Esce se il caricamento fallisce

    # 2. Configurazione della telecamera Intel RealSense
    pipeline = rs.pipeline()
    config = rs.config()

    # Abilita il flusso di colore e profondità (profondità necessaria per l'allineamento dei frame)
    config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

    # Inizia lo streaming
    print("\nAvvio della pipeline RealSense...")
    try:
        pipeline.start(config)
        # Aspetta qualche frame per stabilizzare il pipeline
        for _ in range(30): # ~1 secondo a 30fps
            pipeline.wait_for_frames()
    except Exception as e:
        print(f"ERRORE: Impossibile avviare la telecamera RealSense. Assicurati che sia connessa e non in uso.")
        print(f"Dettagli errore: {e}")
        sys.exit(1) # Esci dal programma

    # 3. Allineamento dei frame di profondità al frame di colore
    align_to = rs.stream.color
    align = rs.align(align_to)

    # 4. Definizione del dizionario ArUco e parametri del rilevatore
    aruco_dict = aruco.getPredefinedDictionary(ARUCO_DICT)
    parameters = aruco.DetectorParameters()

    print(f"\nPronto per la stima della posa ArUco (utilizzando calibrazione personalizzata).")
    print(f"Dizionario ArUco: {ARUCO_DICT}, Lunghezza Marker: {MARKER_LENGTH} metri.")
    print("Premi 'q' per uscire dalla finestra video.")

    try:
        while True:
            # Attendi il prossimo set di frame (colore e profondità)
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames) # Allinea il frame di profondità a quello di colore
            color_frame = aligned_frames.get_color_frame()

            if not color_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

            # Rileva i marker ArUco nell'immagine in scala di grigi
            corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

            if ids is not None:
                # Disegna i contorni dei marker rilevati sull'immagine a colori
                aruco.drawDetectedMarkers(color_image, corners) 

                # Stima la posa (rotazione e traslazione) per ogni marker rilevato
                rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(corners, MARKER_LENGTH, camera_matrix, dist_coeffs)

                for i, _id in enumerate(ids):
                    rvec = rvecs[i] # Vettore di rotazione del marker corrente
                    tvec = tvecs[i] # Vettore di traslazione (posizione X, Y, Z) del marker corrente

                    # Disegna gli assi 3D sul marker (X=rosso, Y=verde, Z=blu)
                    # Lunghezza assi: 80% della lunghezza del marker; Spessore linea: 1 pixel
                    cv2.drawFrameAxes(color_image, camera_matrix, dist_coeffs, rvec, tvec, MARKER_LENGTH * 0.8, thickness=1)

                    # Estrai le coordinate X, Y, Z dal vettore di traslazione (tvec è in metri)
                    x, y, z = tvec[0]
                    
                    # Calcola la distanza dalla camera in centimetri
                    distance_cm = z * 100 

                    # Converte il vettore di rotazione (Rodrigues) in angoli di Eulero (Roll, Pitch, Yaw)
                    rotation_matrix, _ = cv2.Rodrigues(rvec)
                    # Il calcolo degli angoli di Eulero è un po' complesso e può avere problemi di "gimbal lock"
                    # ma è un metodo comune per visualizzare l'orientamento.
                    sy = np.sqrt(rotation_matrix[0,0] * rotation_matrix[0,0] +  rotation_matrix[1,0] * rotation_matrix[1,0])
                    singular = sy < 1e-6 # Controlla per "gimbal lock"

                    if not singular:
                        roll = np.arctan2(rotation_matrix[2,1], rotation_matrix[2,2])
                        pitch = np.arctan2(-rotation_matrix[2,0], sy)
                        yaw = np.arctan2(rotation_matrix[1,0], rotation_matrix[0,0])
                    else:
                        roll = np.arctan2(-rotation_matrix[1,2], rotation_matrix[1,1])
                        pitch = np.arctan2(-rotation_matrix[2,0], sy)
                        yaw = 0 

                    # Scrive l'ID del marker sull'immagine video (in giallo-verde)
                    # Posiziona il testo sopra il centro del marker
                    center_x = int(corners[i][0][0][0] + (corners[i][0][2][0] - corners[i][0][0][0]) / 2)
                    center_y = int(corners[i][0][0][1] + (corners[i][0][2][1] - corners[i][0][0][1]) / 2)
                    text_x = center_x - 30 # Sposta leggermente a sinistra
                    text_y = center_y - 30 # Sposta leggermente in alto

                    cv2.putText(color_image, f"ID: {_id[0]}", (text_x, text_y), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 1, cv2.LINE_AA) # Scala 0.7, Spessore 1


                    # Stampa le informazioni della terna nel terminale
                    print(f"--- Marker ID: {_id[0]} ---")
                    print(f"  Posizione (X, Y, Z): ({x:.4f} m, {y:.4f} m, {z:.4f} m)")
                    print(f"  Distanza dalla Camera (Z): {distance_cm:.2f} cm")
                    print(f"  Orientamento (Roll, Pitch, Yaw): ({np.degrees(roll):.2f}°, {np.degrees(pitch):.2f}°, {np.degrees(yaw):.2f}°)")
                    print("-" * 30)

            # Mostra il frame video con i marker e gli assi
            cv2.imshow('ArUco Pose Estimation (Calibrated)', color_image)

            # Esci dal loop se viene premuto il tasto 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Assicurati di fermare il pipeline della telecamera e chiudere tutte le finestre OpenCV
        pipeline.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    aruco_pose_estimation_calibrated()