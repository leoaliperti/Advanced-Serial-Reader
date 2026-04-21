import json
import os
import time

def resource_path(relative_path):
    """ Ottiene il percorso assoluto delle risorse, funziona sia in sviluppo che come EXE/APP """
    try:
        # PyInstaller crea una cartella temporanea in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

CONFIG_FILE = resource_path("settings.json")

# Inserisci qui tutte le tue costanti originali. 
# Fungeranno da valori di base se il file JSON non esiste ancora.
DEFAULT_SETTINGS = {
    "WINDOW_TITLE": "Advanced Serial Reader Pro",
    "WINDOW_WIDTH": 1050,
    "WINDOW_HEIGHT": 650,
    "APPEARANCE_MODE": "Dark",
    "COLOR_THEME": "blue",
    "DEFAULT_BAUDRATE": "9600",
    "DEFAULT_MODE": "Split",
    "DEFAULT_FLOW_DELAY_MS": "500",
    "MIN_SAFE_DELAY_MS": 10,
    "FIXED_ONLY_DELAY_MS": 500,
    "MSG_DURATION_MS": 4000,
    "CHECKBOX_TIMESTAMP_DEFAULT": 1,
    "SYSTEM_EVENT_TIMEOUT_S": 5,  # Scompare dopo 5 secondi (oppure scrivi "never")
    "AUTO_RECONNECT_DEFAULT": False,      # Se lo switch Auto-Reconnect deve essere attivo all'avvio
    "AUTO_RECONNECT_DELAY_MS": 3000,      # Millisecondi di attesa prima di tentare la riconnessione automatica
    "MAX_GRAPH_POINTS": 10,                # Numero massimo di punti da visualizzare nel grafico (per ogni dataset)
    "CSV_LOG_DIR": "logs",                # Nome della cartella dove verranno salvati i file CSV
    
    "MACROS": {                           # Comandi rapidi per i pulsanti laterali ("Nome Pulsante": "Comando da inviare")
        "Clear Errors": "CLEAR_ERR",
        "Start Sensor": "START_STREAM",
        "Stop Sensor":  "STOP_STREAM",
        "Reboot":       "RST"
    },
    "CSV_LOG_MODE": "Multi-file",  # Opzioni: "Single Split", "Multi-file", "Single Flat"

    "AUTOMATIONS": {
        "ERROR:": "RESET",
        "PING": "PONG",
        "Calibrazione richiesta": "CALIBRATE_START"
    },

    "COLOR": {
        "CONNECT_BTN": "#28a745",
        "CONNECT_BTN_HOVER": "#218838",
        "DISCONNECT_BTN": "#dc3545",
        "DISCONNECT_BTN_HOVER": "#c82333",
        "SETTINGS_BTN": "#000000",
        "SETTINGS_BTN_HOVER": "#161616",
        "FIXED_MODE_COLOR": "#17a2b8",
        "FLOW_MODE_COLOR": "#28a745"
    }
}

# Questo è il dizionario "vivo" che il tuo programma leggerà e modificherà
settings = DEFAULT_SETTINGS.copy()

def load():
    """Carica i dati dal JSON e aggiorna il dizionario 'settings'."""
    global settings
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded_data = json.load(f)
                # .update() sovrascrive i valori default con quelli del file,
                # ma mantiene intatti i default se nel file manca qualche voce.
                settings.update(loaded_data)
        except Exception as e:
            print(f"Errore nella lettura del file di configurazione: {e}")

def save():
    """Salva lo stato attuale del dizionario 'settings' nel file JSON."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# Chiamiamo load() non appena il file viene importato,
# così 'settings' è già popolato quando il main.py parte.
load()