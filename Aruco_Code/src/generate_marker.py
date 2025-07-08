# Dipendenze necessarie:
# pip install opencv-contrib-python
# pip install numpy
# pip install pyyaml
# pip install reportlab
#pip install fpdf

import cv2
import numpy as np 
import os
import yaml
import sys # Utilizzato per sys.exit() per terminare il programma

# Importa le classi necessarie dalla libreria ReportLab per la generazione di PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- Costanti per i Colori del Terminale (ANSI Escape Codes) ---
# Queste costanti vengono utilizzate per formattare l'output nel terminale
# rendendolo più leggibile e visivamente accattivante.
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_RED = "\033[91m"

# Mappa dai nomi leggibili dei dizionari ArUco agli ID numerici di OpenCV.
# Questo facilita la selezione del dizionario da parte dell'utente.
ARUCO_DICTIONARIES = {
    "4X4_50": cv2.aruco.DICT_4X4_50, "4X4_100": cv2.aruco.DICT_4X4_100,
    "4X4_250": cv2.aruco.DICT_4X4_250, "4X4_1000": cv2.aruco.DICT_4X4_1000,
    "5X5_50": cv2.aruco.DICT_5X5_50, "5X5_100": cv2.aruco.DICT_5X5_100,
    "5X5_250": cv2.aruco.DICT_5X5_250, "5X5_1000": cv2.aruco.DICT_5X5_1000,
    "6X6_50": cv2.aruco.DICT_6X6_50, "6X6_100": cv2.aruco.DICT_6X6_100,
    "6X6_250": cv2.aruco.DICT_6X6_250, "6X6_1000": cv2.aruco.DICT_6X6_1000,
    "7X7_50": cv2.aruco.DICT_7X7_50, "7X7_100": cv2.aruco.DICT_7X7_100,
    "7X7_250": cv2.aruco.DICT_7X7_250, "7X7_1000": cv2.aruco.DICT_7X7_1000,
    "ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
}

# --- Funzioni di Utilità ---

def clear_screen():
    """
    Pulisce lo schermo del terminale.
    Comando specifico per Windows ('cls') o per Unix/Linux/macOS ('clear').
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def get_max_marker_id(aruco_dict_id):
    """
    Restituisce il numero massimo di marker supportato per un dato dizionario ArUco.
    
    Args:
        aruco_dict_id (int): L'ID numerico del dizionario ArUco (es. cv2.aruco.DICT_7X7_250).
        
    Returns:
        int: Il numero massimo di ID marker disponibili per quel dizionario.
             Restituisce 1024 per DICT_ARUCO_ORIGINAL o il numero estratto dal nome.
    """
    if aruco_dict_id == cv2.aruco.DICT_ARUCO_ORIGINAL:
        return 1024 # Il dizionario originale ha un massimo di 1024 marker
    
    for name, id_val in ARUCO_DICTIONARIES.items():
        if id_val == aruco_dict_id:
            try:
                # Estrae il numero massimo di marker dal nome del dizionario (es. "4X4_250" -> 250)
                return int(name.split('_')[-1])
            except ValueError:
                return 0 # In caso di errore di parsing, restituisce 0

def print_header(title):
    """
    Stampa un'intestazione formattata nel terminale per i menu e le sezioni.
    
    Args:
        title (str): Il testo del titolo da visualizzare nell'intestazione.
    """
    clear_screen() # Pulisce lo schermo prima di stampare l'intestazione
    print(f"{COLOR_BOLD}{COLOR_BLUE}###############################################{COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_BLUE}# {title.center(43)} #{COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_BLUE}###############################################{COLOR_RESET}\n")

def generate_pdf_with_marker(png_filepath, pdf_filepath, marker_width_cm, marker_info):
    """
    Genera un file PDF in formato A4 contenente l'immagine del marker PNG
    centrata e scalata. Aggiunge una riga di testo come intestazione in alto,
    piccola e centrata, con ID, Dizionario e Dimensione.
    
    Args:
        png_filepath (str): Percorso del file PNG del marker generato.
        pdf_filepath (str): Percorso completo dove salvare il file PDF.
        marker_width_cm (float): Larghezza desiderata del marker in centimetri nel PDF.
        marker_info (dict): Dizionario contenente le informazioni del marker.
                                Deve includere 'id', 'dictionary', 'size_cm'.
        
    Returns:
        bool: True se il PDF è stato generato con successo, False altrimenti.
    """
    try:
        c = canvas.Canvas(pdf_filepath, pagesize=A4)
        
        page_width, page_height = A4
        
        marker_width_points = marker_width_cm * cm
        marker_height_points = marker_width_points
        
        x_image_center = (page_width - marker_width_points) / 2
        y_image_center = (page_height - marker_height_points) / 2
        
        marker_image = ImageReader(png_filepath)
        
        c.drawImage(marker_image, x_image_center, y_image_center, 
                    width=marker_width_points, height=marker_height_points)
        
       
        
        # Formatta il testo con le informazioni richieste
        text = (f"ID: {marker_info['id']} | Dizionario: {marker_info['dictionary']} | Dim.: {marker_info['size_cm']:.1f}cm | "
                f"Pos (x,y,z): ({marker_info['x']:.2f}, {marker_info['y']:.2f}, {marker_info['z']:.2f})m | "
                f"Rot (r,p,y): ({marker_info['roll_deg']:.1f}°, {marker_info['pitch_deg']:.1f}°, {marker_info['yaw_deg']:.1f}°)")
        
        ### CORREZIONE: Dimensione del font ridotta per un'intestazione discreta
        font_size = 10
        c.setFont("Helvetica", font_size)
        
        # Calcola la larghezza del testo per poterlo centrare
        text_width = c.stringWidth(text, "Helvetica", font_size)

        top_margin_points = 2 * cm
        y_text = page_height - top_margin_points - font_size
        x_text = (page_width - text_width) / 2
        # Disegna il testo nella posizione calcolata
        c.drawString(x_text, y_text, text)
        c.save() # Salva il file PDF
        return True
    except Exception as e:
        print(f"{COLOR_RED}Errore durante la generazione del PDF: {e}{COLOR_RESET}")
        return False

# --- Funzione Principale per la Generazione Interattiva ---

def generate_aruco_marker_interactive():
    """
    Guida l'utente attraverso un processo interattivo per generare un marcatore ArUco,
    salvarlo come PNG e PDF, e registrarne la posa in un file YAML.
    """
    print_header("Generatore di Marcatori ArUco")

    # Definisce la directory 'data' relativa alla posizione dello script corrente.
    # Questo assicura che i file vengono salvati in 'src/data/' se lo script è in 'src/'.
    script_dir = os.path.dirname(__file__)
    data_dir = os.path.join(script_dir, "data")

    # Assicurati che la directory 'data' esista. Se non c'è, la crea.
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"{COLOR_YELLOW}Creata la directory '{data_dir}/' per i file generati.{COLOR_RESET}\n")

    # 1. Scelta del Dizionario ArUco
    print(f"{COLOR_BOLD}1. Selezione del Dizionario ArUco:{COLOR_RESET}")
    print(f"{COLOR_YELLOW}Dizionari disponibili:{COLOR_RESET}")
    dict_names = list(ARUCO_DICTIONARIES.keys())
    for i, name in enumerate(dict_names):
        print(f"  {COLOR_GREEN}{i+1}. {name}{COLOR_RESET}")
    
    selected_dict_name = ""
    aruco_dict_id = None
    while True:
        try:
            choice = input(f"{COLOR_BOLD}Inserisci il numero o il nome del dizionario (es. 1 o 6X6_250): {COLOR_RESET}").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(dict_names):
                selected_dict_name = dict_names[int(choice) - 1]
                aruco_dict_id = ARUCO_DICTIONARIES[selected_dict_name]
                break
            elif choice.upper() in ARUCO_DICTIONARIES:
                selected_dict_name = choice.upper()
                aruco_dict_id = ARUCO_DICTIONARIES[selected_dict_name]
                break
            else:
                print(f"{COLOR_RED}Errore: Scelta non valida. Riprova.{COLOR_RESET}")
        except Exception:
            print(f"{COLOR_RED}Errore: Input non valido. Riprova.{COLOR_RESET}")

    aruco_dict_obj = cv2.aruco.getPredefinedDictionary(aruco_dict_id)
    max_id = get_max_marker_id(aruco_dict_id)
    print(f"{COLOR_GREEN}Dizionario selezionato: {selected_dict_name} (Max ID: {max_id - 1}){COLOR_RESET}\n")

    # 2. Inserimento ID Marcatore
    print(f"{COLOR_BOLD}2. Inserimento ID Marcatore:{COLOR_RESET}")
    while True:
        try:
            marker_id = int(input(f"  Inserisci l'ID del marcatore da generare ({COLOR_YELLOW}0 - {max_id - 1}{COLOR_RESET}): "))
            if 0 <= marker_id < max_id:
                break
            else:
                print(f"{COLOR_RED}  Errore: L'ID deve essere tra 0 e {max_id - 1} per il dizionario {selected_dict_name}. Riprova.{COLOR_RESET}")
        except ValueError:
            print(f"{COLOR_RED}  Errore: Inserisci un numero intero valido.{COLOR_RESET}")
    print(f"{COLOR_GREEN}  ID marcatore: {marker_id}{COLOR_RESET}\n")

    # 3. Dimensione Desiderata del Marcatore (per PNG e PDF)
    print(f"{COLOR_BOLD}3. Dimensione del Marcatore Finale:{COLOR_RESET}")
    while True:
        try:
            size_cm = float(input(f"  Inserisci la dimensione del lato del marcatore in cm ({COLOR_YELLOW}es. 5 per 5x5 cm{COLOR_RESET}): "))
            if size_cm > 0:
                # Per la generazione del PNG, usiamo una dimensione fissa in pixel di buona qualità (es. 1000x1000px).
                # La dimensione fisica verrà gestita dal PDF al momento della stampa.
                image_size_pixels_for_png = 1000 
                print(f"{COLOR_YELLOW}  Genererò un'immagine PNG di {image_size_pixels_for_png}x{image_size_pixels_for_png} pixel.{COLOR_RESET}")
                break
            else:
                print(f"{COLOR_RED}  Errore: La dimensione deve essere un numero positivo.{COLOR_RESET}")
        except ValueError:
            print(f"{COLOR_RED}  Errore: Inserisci un numero valido.{COLOR_RESET}")
    print(f"{COLOR_GREEN}  Dimensione desiderata: {size_cm} cm{COLOR_RESET}\n")

    # 4. Inserimento Coordinate XYZ (Posizione Reale)
    print(f"{COLOR_BOLD}4. Inserimento Coordinate 3D (Posizione Reale):{COLOR_RESET}")
    print(f"{COLOR_YELLOW}  Queste coordinate verranno associate al marcatore nel file YAML.{COLOR_RESET}")
    while True:
        try:
            coord_x = float(input("  Coordinata X (metri, es. 1.5): "))
            coord_y = float(input("  Coordinata Y (metri, es. 0.8): "))
            coord_z = float(input("  Coordinata Z (metri, es. 2.1): "))
            break
        except ValueError:
            print(f"{COLOR_RED}  Errore: Inserisci un numero valido.{COLOR_RESET}")
    print(f"{COLOR_GREEN}  Posizione: X={coord_x:.2f}m, Y={coord_y:.2f}m, Z={coord_z:.2f}m{COLOR_RESET}\n")

    # 5. Inserimento Orientamento (Roll, Pitch, Yaw)
    print(f"{COLOR_BOLD}5. Inserimento Orientamento (Rotazione in Gradi):{COLOR_RESET}")
    print(f"{COLOR_YELLOW}  Questi angoli verranno associati al marcatore nel file YAML.{COLOR_RESET}")
    while True:
        try:
            roll = float(input("  Angolo Roll (rotazione X, gradi, es. 0 o 90): "))
            pitch = float(input("  Angolo Pitch (rotazione Y, gradi, es. 0 o -45): "))
            yaw = float(input("  Angolo Yaw (rotazione Z, gradi, es. 0 o 180): "))
            break
        except ValueError:
            print(f"{COLOR_RED}  Errore: Inserisci un numero valido.{COLOR_RESET}")
    print(f"{COLOR_GREEN}  Orientamento: Roll={roll:.1f}°, Pitch={pitch:.1f}°, Yaw={yaw:.1f}°{COLOR_RESET}\n")

    # --- Generazione e Salvataggio dei File ---
    border_bits = 1 # Numero di bordi neri attorno al marker (standard ArUco)
    
    # Nomi dei file di output con il percorso alla directory 'data/'
    png_filename = os.path.join(data_dir, f"marker_{selected_dict_name}_id_{marker_id}.png")
    pdf_filename = os.path.join(data_dir, f"marker_{selected_dict_name}_id_{marker_id}_{int(size_cm)}cm.pdf")
    yaml_filename = os.path.join(data_dir, "marker_poses.yaml")

    # Genera l'immagine del marcatore utilizzando OpenCV (sempre ad alta risoluzione per qualità)
    print(f"{COLOR_BOLD}Generazione immagine PNG in corso...{COLOR_RESET}")
    marker_image = np.zeros((image_size_pixels_for_png, image_size_pixels_for_png), dtype=np.uint8)
    cv2.aruco.generateImageMarker(aruco_dict_obj, marker_id, image_size_pixels_for_png, marker_image, border_bits)

    cv2.imwrite(png_filename, marker_image) # Salva l'immagine PNG
    print(f"{COLOR_GREEN}✓ Immagine PNG salvata come '{png_filename}'{COLOR_RESET}")

    # Prepara le informazioni del marker per il PDF (solo quelle necessarie per la riga di testo)
    marker_info_for_pdf = {
        'id': marker_id,
        'dictionary': selected_dict_name,
        'size_cm': size_cm,
        # Le coordinate XYZ e RPY non sono più necessarie per la stampa sul PDF
        # ma sono mantenute nel dizionario per coerenza con la chiamata alla funzione.
        'x': coord_x,
        'y': coord_y,
        'z': coord_z,
        'roll_deg': roll,
        'pitch_deg': pitch,
        'yaw_deg': yaw
    }

    # Genera il PDF con il marker centrato e della dimensione desiderata, includendo la riga di testo
    print(f"{COLOR_BOLD}Generazione PDF in corso...{COLOR_RESET}")
    if generate_pdf_with_marker(png_filename, pdf_filename, size_cm, marker_info_for_pdf):
        print(f"{COLOR_GREEN}✓ PDF con marcatore {size_cm}cm x {size_cm}cm salvato come '{pdf_filename}'{COLOR_RESET}")
    else:
        print(f"{COLOR_RED}X Errore nella generazione del PDF.{COLOR_RESET}")

    # Prepara i dati della posa e li salva/aggiorna nel file YAML
    new_pose_data = {
        str(marker_id): { # L'ID del marker come chiave stringa
            'x': coord_x,
            'y': coord_y,
            'z': coord_z,
            'roll_deg': roll,
            'pitch_deg': pitch,
            'yaw_deg': yaw,
            'dictionary': selected_dict_name,
            'size_cm': size_cm # La dimensione desiderata per il marcatore reale
        }
    }

    # Carica i dati esistenti dal file YAML, se presente, altrimenti inizializza un dizionario vuoto
    if os.path.exists(yaml_filename):
        with open(yaml_filename, 'r') as f:
            data = yaml.safe_load(f) or {} # Usa or {} per gestire un file YAML vuoto
    else:
        data = {} # Se il file non esiste, inizia con un dizionario vuoto

    data.update(new_pose_data) # Aggiorna o aggiunge i dati del nuovo marker

    # Salva i dati aggiornati nel file YAML
    with open(yaml_filename, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    print(f"{COLOR_GREEN}✓ Coordinate e orientamento salvati in '{yaml_filename}'{COLOR_RESET}\n")
    
    print(f"{COLOR_BOLD}{COLOR_GREEN}Marcatore generato con successo! Controlla i file PNG e PDF nella cartella '{data_dir}/'.{COLOR_RESET}")

def main_menu():
    """
    Funzione principale che gestisce il menu interattivo del programma.
    Permette all'utente di scegliere tra la generazione di un marker o l'uscita.
    """
    while True:
        print_header("Menu Principale - Generatore ArUco")
        print(f"{COLOR_BOLD}Seleziona un'opzione:{COLOR_RESET}")
        print(f"  {COLOR_GREEN}1. Genera un nuovo Marcatore ArUco{COLOR_RESET}")
        print(f"  {COLOR_RED}2. Esci{COLOR_RESET}")

        choice = input(f"\n{COLOR_BOLD}La tua scelta: {COLOR_RESET}").strip()

        if choice == '1':
            generate_aruco_marker_interactive()
            input(f"\n{COLOR_YELLOW}Premi INVIO per tornare al menu principale...{COLOR_RESET}")
        elif choice == '2':
            print(f"{COLOR_BLUE}Arrivederci!{COLOR_RESET}")
            sys.exit() # Termina il programma
        else:
            print(f"{COLOR_RED}Scelta non valida. Riprova.{COLOR_RESET}")
            input(f"{COLOR_YELLOW}Premi INVIO per continuare...{COLOR_RESET}")

if __name__ == "__main__":
    # Questo blocco assicura che main_menu() venga chiamato solo quando lo script
    # viene eseguito direttamente (non quando viene importato come modulo).
    main_menu()
