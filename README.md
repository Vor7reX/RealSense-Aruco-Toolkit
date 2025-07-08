# RealSense ArUco Toolkit

Questo progetto fornisce un set di strumenti Python per la generazione, calibrazione e la stima della posa di marcatori ArUco utilizzando telecamere Intel RealSense. È ideale per applicazioni di realtà aumentata, robotica o qualsiasi scenario in cui sia necessaria una localizzazione precisa nello spazio 3D basata su marcatori ArUco.

---

## Funzionalità

* **Generazione di Marcatori ArUco:** Un'interfaccia interattiva per creare marcatori ArUco personalizzati, salvarli come immagini PNG, generare PDF stampabili con dimensioni precise e associare coordinate 3D reali e orientamento in un file YAML.
* **Calibrazione Personalizzata della RealSense:** Uno script dedicato per calibrare la tua telecamera Intel RealSense utilizzando un pattern a scacchiera. Questa calibrazione è cruciale per ottenere misurazioni di posa accurate.
* **Stima della Posa (Intrinseci di Fabbrica):** Un'applicazione live che rileva i marcatori ArUco e stima la loro posa 3D (posizione e orientamento) utilizzando i parametri intrinseci predefiniti della telecamera RealSense. Utile per test rapidi o quando la precisione assoluta non è critica.
* **Stima della Posa (Calibrazione Personalizzata):** Un'applicazione live avanzata che carica i parametri di calibrazione salvati dalla tua telecamera RealSense per fornire stime della posa 3D molto più accurate.

---

## Dipendenze Hardware e Software

* **Hardware:**
    * Telecamera Intel RealSense (serie D, es. D415, D435)
    * Un pattern a scacchiera stampato con dimensioni precise per la calibrazione.
    * I marcatori ArUco stampati per il rilevamento.
* **Software:**
    * Python 3.x
    * Librerie Python elencate in `requirements.txt`.
    * SDK Intel RealSense (lib_realsense2) installato sul tuo sistema (2.55.1).

---

## Installazione

1.  **Clona la Repository:**
    ```bash
    git clone https://github.com/Vor7reX/RealSense-Aruco-Toolkit.git
    cd RealSense-Aruco-Toolkit
    ```

2.  **Installa l'SDK Intel RealSense:**
    Segui le istruzioni ufficiali di Intel per installare il [SDK RealSense](https://github.com/IntelRealSense/librealsense/blob/master/doc/distribution_package.md) per il tuo sistema operativo. Fondamentale perché `pyrealsense2` si basa su di esso.

3.  **Crea un Ambiente Virtuale (Consigliato):**
    ```bash
    python -m venv venv
    # Su Windows:
    .\venv\Scripts\activate
    # Su macOS/Linux:
    source venv/bin/activate
    ```

4.  **Installa le Dipendenze Python:**
    Assicurati di essere nella directory radice del progetto e con l'ambiente virtuale attivato:
    ```bash
    pip install -r requirements.txt
    ```

---

## Utilizzo

### 1. Generare i Marcatori ArUco (`src/generate_marker.py`)

Questo script ti consente di creare marcatori ArUco, associarvi coordinate reali e generare file pronti per la stampa.

* Esegui lo script:
    ```bash
    python src/generate_marker.py
    ```
* Segui le istruzioni a schermo per scegliere il dizionario ArUco, l'ID del marker, la sua dimensione desiderata in centimetri e le sue coordinate 3D reali (X, Y, Z e orientamento Roll, Pitch, Yaw).
* Output:
    * Un'immagine PNG del marker (es. `marker_7X7_250_id_0.png`)
    * Un file PDF del marker centrato su un foglio A4 con la dimensione specificata (es. `marker_7X7_250_id_0_10cm.pdf`).
    * Il file `data/marker_poses.yaml` verrà creato o aggiornato con l'ID del marker e le sue coordinate/orientamento specificati.

### 2. Calibrare la Telecamera RealSense (`src/realsense_calibrate.py`)

La calibrazione è un passo cruciale per ottenere stime della posa accurate.

* **Preparazione:**
    * Stampa un pattern a scacchiera.
    * **Misura con precisione un singolo quadrato del tuo pattern a scacchiera.**
* **Modifica i Parametri:**
    Apri `src/realsense_calibrate.py` e modifica le seguenti costanti:
    ```python
    CHECKERBOARD = (9,6) # <--- Modifica con il numero di angoli interni (righe, colonne) della tua scacchiera
    SQUARE_SIZE = 0.024  # <--- Modifica con la dimensione reale di un lato del quadrato della scacchiera in METRI
    CALIBRATION_FILE = 'data/realsense_custom_calibration.npz' # Assicurati che questo percorso sia corretto
    ```
* Esegui lo script:
    ```bash
    python src/realsense_calibrate.py
    ```
* **Processo di Calibrazione:**
    * Verrà avviato un feed video dalla tua RealSense.
    * Tieni la scacchiera davanti alla telecamera. Quando il pattern viene rilevato correttamente, vedrai delle linee verdi che connettono gli angoli.
    * **Premi 'c'** per catturare un'immagine quando il pattern è ben visibile e stabile. Cattura almeno **15-20 immagini** da diverse angolazioni, distanze e orientamenti rispetto alla telecamera, coprendo l'intero campo visivo.
    * Una volta catturate abbastanza immagini, **premi 's'** per avviare il processo di calibrazione.
    * Se la calibrazione ha successo, i parametri della telecamera (`camera_matrix` e `dist_coeffs`) verranno salvati in `data/realsense_custom_calibration.npz`.

### 3. Stima della Posa con Intrinseci di Fabbrica (`src/aruco_pose_estimation_realsense.py`)

Questo script usa i parametri intrinseci predefiniti della tua RealSense. La precisione può variare.

* **Modifica i Parametri:**
    Apri `src/aruco_pose_estimation_realsense.py` e modifica le seguenti costanti in base ai tuoi marcatori ArUco:
    ```python
    ARUCO_DICT = aruco.DICT_7X7_250 # <--- Modifica con il dizionario ArUco che stai usando
    MARKER_LENGTH = 0.10             # <--- Modifica con la dimensione reale di un lato del tuo marker in METRI
    ```
* Esegui lo script:
    ```bash
    python src/aruco_pose_estimation_realsense.py
    ```
* Il feed video mostrerà i marcatori rilevati con gli assi di posa. Il terminale stamperà le coordinate 3D e l'orientamento di ciascun marker.
* Premi 'q' per uscire.

### 4. Stima della Posa con Calibrazione Personalizzata (`src/aruco_pose_estimation_calibrated.py`)

Questo è lo script raccomandato per la massima precisione, poiché carica i parametri di calibrazione che hai generato.

* **Prerequisito:** Devi aver eseguito con successo `src/realsense_calibrate.py` almeno una volta per generare il file `data/realsense_custom_calibration.npz`.
* **Modifica i Parametri:**
    Apri `src/aruco_pose_estimation_calibrated.py` e modifica le seguenti costanti:
    ```python
    CALIBRATION_FILE = 'data/realsense_custom_calibration.npz' # Assicurati che questo percorso sia corretto
    ARUCO_DICT = aruco.DICT_7X7_250 # <--- Modifica con il dizionario ArUco che stai usando
    MARKER_LENGTH = 0.10             # <--- Modifica con la dimensione reale di un lato del tuo marker in METRI
    ```
* Esegui lo script:
    ```bash
    python src/aruco_pose_estimation_calibrated.py
    ```
* Il feed video mostrerà i marcatori rilevati con gli assi di posa. Il terminale stamperà le coordinate 3D e l'orientamento di ciascun marker.
* Premi 'q' per uscire.

---

## Note Importanti

* **Precisione della Posa:** La precisione delle stime di posa dipende fortemente dalla qualità della calibrazione della telecamera e dalla precisione con cui misuri le dimensioni reali dei tuoi marcatori ArUco e della scacchiera.
* **Condizioni di Illuminazione:** Un'illuminazione uniforme e ben distribuita migliora notevolmente l'affidabilità del rilevamento dei marcatori.
* **Realsense D415/D435:** Gli script sono stati testati principalmente con i modelli RealSense D400-series. Anche se dovrebbero funzionare con altre RealSense o webcam compatibili con OpenCV (modificando il codice per la cattura dei frame), `pyrealsense2` è specifico per le telecamere Intel RealSense.

---

## Licenza

Questo progetto è rilasciato sotto la Licenza MIT. Vedi il file `LICENSE` per maggiori dettagli.
