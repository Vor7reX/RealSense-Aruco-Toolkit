# Required dependencies:
# pip install pyrealsense2
# pip install opencv-contrib-python
# pip install numpy

import pyrealsense2 as rs # Libreria per interagire con le telecamere Intel RealSense
import numpy as np        # Libreria per operazioni numeriche
import cv2                # OpenCV per visione artificiale
import glob               # Modulo per la ricerca di file (non direttamente usato nel flusso principale)
import sys                # Utilizzato per sys.exit() per terminare il programma

# --- PARAMETRI DI CALIBRAZIONE (MODIFICA QUESTI VALORI!) ---
# Questi parametri definiscono il pattern a scacchiera utilizzato.

# Numero di angoli interni della scacchiera (righe, colonne).
# Esempio: per una scacchiera 8x6 quadrati, gli angoli interni sono (7, 5).
CHECKERBOARD = (9, 6)  # <-- MODIFICA QUESTO! Inserisci il numero di intersezioni interne.

# Dimensione del lato di un singolo quadrato della scacchiera in METRI.
# Misura questo valore con precisione sul tuo pattern stampato.
SQUARE_SIZE = 0.024    # Esempio: 2.4 cm = 0.024 metri <-- MODIFICA QUESTO CON IL VALORE REALE!

# Criteri di terminazione per l'algoritmo di raffinamento degli angoli della scacchiera.
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Punti oggetto 3D reali della scacchiera.
# Vengono inizializzati in base alla dimensione dei quadrati.
objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2) * SQUARE_SIZE

objpoints = []  # Punti 3D nel mondo reale per ogni immagine catturata.
imgpoints = []  # Punti 2D corrispondenti nell'immagine per ogni immagine.

# Definisce il percorso per il file di calibrazione.
# Utilizziamo os.path.join per garantire la compatibilità tra sistemi operativi.
script_dir = os.path.dirname(__file__) # Ottiene la directory dello script corrente
CALIBRATION_FILE = os.path.join(script_dir, 'data', 'realsense_custom_calibration.npz')

# Configurazione della pipeline della telecamera Intel RealSense.
pipeline = rs.pipeline()
config = rs.config()
# Abilita lo stream di colore a 1280x720 @ 30fps.
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)

print("Avvio della pipeline RealSense per la calibrazione...")
profile = None
try:
    # Avvia lo streaming video.
    profile = pipeline.start(config)
except Exception as e:
    # Gestione errori all'avvio della telecamera.
    print(f"ERRORE: Impossibile avviare la telecamera RealSense. Assicurati che sia connessa e non in uso.")
    print(f"Dettagli errore: {e}")
    sys.exit(1) # Termina il programma.

print("\n--- INIZIO CALIBRAZIONE TELECAMERA ---")
print("Istruzioni:")
print("  1. Mostra la scacchiera alla telecamera da diverse angolazioni e distanze.")
print("  2. Cattura almeno 15-20 immagini premendo 'c' quando il pattern è rilevato (linee verdi).")
print("  3. Premi 's' per salvare la calibrazione e procedere.")
print("  4. Premi 'q' per uscire in qualsiasi momento senza salvare.")

images_captured = 0 # Contatore per le immagini catturate.
try:
    while True:
        # Attende il prossimo set di frame.
        frames = pipeline.wait_for_frames()
        # Ottiene il frame di colore.
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue # Salta se il frame non è disponibile.

        # Converte il frame in un array NumPy e poi in scala di grigi.
        img = np.asanyarray(color_frame.get_data())
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Trova gli angoli della scacchiera.
        ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

        if ret:
            # Se gli angoli sono trovati, raffina le loro posizioni a livello di sub-pixel.
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            # Disegna gli angoli e le connessioni sulla scacchiera.
            cv2.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)

            # Controlla l'input da tastiera per catturare immagini.
            key = cv2.waitKey(1) & 0xFF
            if key == ord('c'):
                objpoints.append(objp)    # Aggiunge i punti 3D.
                imgpoints.append(corners2) # Aggiunge i punti 2D.
                images_captured += 1
                print(f"Immagini catturate: {images_captured}")
                cv2.waitKey(500) # Breve pausa per evitare catture multiple.
        
        # Visualizza informazioni e istruzioni nella finestra video.
        cv2.putText(img, f"Immagini: {images_captured} (C: cattura, S: salva, Q: esci)", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow('Camera Calibration (premi C per catturare)', img)

        # Gestisce gli input da tastiera per uscire o salvare.
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Calibrazione interrotta dall'utente.")
            break # Esce dal loop.
        elif key == ord('s'):
            # Verifica il numero minimo di immagini catturate.
            if images_captured < 10:
                print("ATTENZIONE: Cattura almeno 10 immagini per una calibrazione decente prima di salvare.")
                continue # Continua il loop.
            
            print("\nAvvio del calcolo della calibrazione...")
            try:
                # Esegue l'algoritmo di calibrazione della telecamera.
                ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

                if ret: # Se la calibrazione è riuscita
                    print("RISULTATO CALIBRAZIONE: SUCCESSO!")
                    print("Matrice della telecamera (camera_matrix):\n", mtx)
                    print("Coefficienti di distorsione (dist_coeffs):\n", dist)

                    # Salva i parametri di calibrazione in un file .npz.
                    np.savez(CALIBRATION_FILE, camera_matrix=mtx, dist_coeffs=dist)
                    print(f"\nParametri di calibrazione SALVATI con successo in '{CALIBRATION_FILE}'")
                    print("\nOra puoi eseguire lo script di stima della posa che caricherà questi parametri.")
                    break # Esce dal loop.
                else: # Se la calibrazione è fallita
                    print(f"RISULTATO CALIBRAZIONE: FALLITO! (ret={ret})")
                    print("Errore durante la calibrazione. Riprova con più immagini (almeno 15-20) e migliori angolazioni.")
                    print("Assicurati che la scacchiera sia sempre ben visibile e nitida.")
            except Exception as e:
                print(f"Eccezione durante il calcolo della calibrazione: {e}")
                print("Questo è un errore inaspettato. Controlla la tua installazione o i dati.")

finally:
    # Blocco di pulizia: ferma lo streaming e chiude le finestre.
    pipeline.stop()         # Ferma lo streaming della telecamera.
    cv2.destroyAllWindows() # Chiude tutte le finestre OpenCV.
