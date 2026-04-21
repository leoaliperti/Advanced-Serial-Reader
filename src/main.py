import os
import sys

# --- FIX AVVIO LENTO MATPLOTLIB ---
# Creiamo una cartellina nascosta fissa nel computer per salvare la cache
cache_dir = os.path.join(os.path.expanduser('~'), '.AdvancedSerialReader_cache')
os.makedirs(cache_dir, exist_ok=True)
os.environ['MPLCONFIGDIR'] = cache_dir
# ------

# --- IMPORTAZIONI LIBRERIE STANDARD E TERZE PARTI ---
import customtkinter as ctk
import serial.tools.list_ports
import serial
import threading
import queue
import time
from datetime import datetime
import csv

# --- IMPORTAZIONI DEI TUOI MODULI VECCHI ---
import config
from settings_window import SettingsWindow
from macro_manager_window import MacroManagerWindow
from script_window import ScriptManagerWindow

# --- IMPORTAZIONI DEI NUOVI MODULI ---
from data_processor import DataProcessor
from automation import AutomationManager
from graph_module import LiveGraph

# Opzioni fisse
BAUDRATE_OPTIONS = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]
MODE_OPTIONS = ["Fixed", "Flow", "Split"]
TERMINATOR_OPTIONS = ["\\n (LF)", "\\r\\n (CRLF)", "None"]

ctk.set_appearance_mode(config.settings["APPEARANCE_MODE"])
ctk.set_default_color_theme(config.settings["COLOR_THEME"])

def resource_path(relative_path):
    """ Ottiene il percorso assoluto delle risorse, funziona sia in sviluppo che come EXE/APP """
    try:
        # PyInstaller crea una cartella temporanea in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ==========================================
# --- CLASSE PRINCIPALE DELL'APPLICAZIONE ---
# ==========================================
class SerialMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- VARIABILI DI STATO ---
        self.serial_port = None
        self.is_reading = False       
        self.read_thread = None       
        self.data_queue = queue.Queue() 
        self.buffer_str = ""
        self.fixed_data = {}
        self.system_event_timestamp = None
        
        self.current_terminator_name = "\\n (LF)"
        self.terminator_char = '\n'
        
        # Variabili Logging CSV
        self.csv_files = {}     
        self.csv_writers = {}   
        self.log_session_id = "" 
        self.current_log_dir = None
        
        # Nuovi Moduli
        self.data_processor = DataProcessor()
        self.automation = AutomationManager(self.send_command)
        
        # Setup UI
        self.title(config.settings["WINDOW_TITLE"])
        self.geometry(f"{config.settings['WINDOW_WIDTH']}x{config.settings['WINDOW_HEIGHT']}")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Gestione Icona
        if sys.platform.startswith("win"):
            # Per Windows usiamo il file .ico
            icon_ico_path = resource_path('assets/icon.ico')
            self.after(200, lambda: self.iconbitmap(icon_ico_path))
        else:
            # Per macOS e Linux forziamo il .png
            icon_path = resource_path('assets/icon.png')
            try:
                from PIL import Image, ImageTk 
                pil_image = Image.open(icon_path)
                tk_icon = ImageTk.PhotoImage(pil_image)
                # Il "True" serve per forzare l'icona su tutte le finestre e nel Dock!
                self.iconphoto(True, tk_icon) 
            except Exception as e:
                print(f"Errore caricamento icona: {e}")

        self.setup_ui()
        self.update_port_menu()
        self.change_terminal_layout(config.settings["DEFAULT_MODE"])
        
        self.process_queue()

    def setup_ui(self):
        # ==========================================
        # 1. SIDEBAR (Sinistra)
        # ==========================================
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="TOOLS", font=("Arial", 16, "bold")).pack(pady=(20, 10))

        self.auto_reconnect_var = ctk.BooleanVar(value=config.settings.get("AUTO_RECONNECT_DEFAULT", False))
        ctk.CTkSwitch(self.sidebar_frame, text="Auto-Reconnect", variable=self.auto_reconnect_var).pack(pady=10, padx=20, anchor="w")

        self.hex_view_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(self.sidebar_frame, text="Hex View", variable=self.hex_view_var, command=self.clear_buffer).pack(pady=10, padx=20, anchor="w")

        self.logging_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(self.sidebar_frame, text="Log to CSV", variable=self.logging_var, command=self.toggle_logging).pack(pady=10, padx=20, anchor="w")

        ctk.CTkButton(self.sidebar_frame, text="📜 Script Manager", command=self.open_script_manager).pack(pady=10, padx=20, fill="x")

        self.macro_header_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.macro_header_frame.pack(pady=(30, 5), padx=20, fill="x")
        

        ctk.CTkLabel(self.macro_header_frame, text="MACROS", font=("Arial", 14, "bold")).pack(side="left")
        ctk.CTkButton(self.macro_header_frame, text="⚙️", width=30, height=24, fg_color="transparent", border_width=1, command=self.open_macro_manager).pack(side="right")

        self.macros_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.macros_container.pack(fill="x")
        self.refresh_macro_buttons()

        # ==========================================
        # 2. MAIN AREA (Destra)
        # ==========================================
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- PANNELLO CONTROLLI (Top) ---
        self.control_frame = ctk.CTkFrame(self.main_frame)
        self.control_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.control_frame.grid_columnconfigure((0,1,2,3,4,5,6), weight=1)

        ctk.CTkLabel(self.control_frame, text="COM Port:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=(10, 5), sticky="e")
        self.port_menu = ctk.CTkOptionMenu(self.control_frame, dynamic_resizing=False, command=self.update_placeholder)
        self.port_menu.grid(row=0, column=1, padx=5, pady=(10, 5), sticky="w")
        ctk.CTkButton(self.control_frame, text="↻ Refresh", width=80, command=self.update_port_menu, fg_color="transparent", border_width=1).grid(row=0, column=2, padx=5, pady=(10, 5), sticky="w")

        ctk.CTkLabel(self.control_frame, text="Baud Rate:", font=("Arial", 12, "bold")).grid(row=0, column=3, padx=5, pady=(10, 5), sticky="e")
        self.baud_menu = ctk.CTkOptionMenu(self.control_frame, values=BAUDRATE_OPTIONS, dynamic_resizing=False)
        self.baud_menu.set(config.settings["DEFAULT_BAUDRATE"])
        self.baud_menu.grid(row=0, column=4, padx=5, pady=(10, 5), sticky="w")

        ctk.CTkLabel(self.control_frame, text="Mode:", font=("Arial", 12, "bold")).grid(row=0, column=5, padx=5, pady=(10, 5), sticky="e")
        self.mode_menu = ctk.CTkOptionMenu(self.control_frame, values=MODE_OPTIONS, command=self.change_terminal_layout, dynamic_resizing=False)
        self.mode_menu.set(config.settings["DEFAULT_MODE"])
        self.mode_menu.grid(row=0, column=6, padx=5, pady=(10, 5), sticky="w")

        ctk.CTkLabel(self.control_frame, text="Delay (ms):", font=("Arial", 12, "bold")).grid(row=1, column=0, padx=5, pady=(5, 10), sticky="e")
        self.delay_entry = ctk.CTkEntry(self.control_frame, width=100)
        self.delay_entry.insert(0, config.settings["DEFAULT_FLOW_DELAY_MS"])
        self.delay_entry.grid(row=1, column=1, padx=5, pady=(5, 10), sticky="w")

        self.checkbox_timestamp = ctk.CTkCheckBox(self.control_frame, text="Timestamp")
        self.checkbox_timestamp.grid(row=1, column=2, padx=10, pady=(5, 10), sticky="w")
        if config.settings["CHECKBOX_TIMESTAMP_DEFAULT"]: self.checkbox_timestamp.select()

        self.btn_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.btn_frame.grid(row=1, column=3, columnspan=4, sticky="ew")
        ctk.CTkButton(self.btn_frame, text="Connect", fg_color=config.settings["COLOR"]["CONNECT_BTN"], hover_color=config.settings["COLOR"]["CONNECT_BTN_HOVER"], command=self.connect_serial).pack(side="left", padx=5)
        ctk.CTkButton(self.btn_frame, text="Disconnect", fg_color=config.settings["COLOR"]["DISCONNECT_BTN"], hover_color=config.settings["COLOR"]["DISCONNECT_BTN_HOVER"], command=self.disconnect_serial).pack(side="left", padx=5)
        ctk.CTkButton(self.btn_frame, text="Clear", fg_color="gray", hover_color="darkgray", command=self.clear_terminals).pack(side="left", padx=5)
        ctk.CTkButton(self.btn_frame, text="⚙️", width=40, fg_color=config.settings["COLOR"]["SETTINGS_BTN"], hover_color=config.settings["COLOR"]["SETTINGS_BTN_HOVER"], command=self.open_settings).pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(self.control_frame, text="Waiting for connection...", font=("Arial", 12, "italic"))
        self.status_label.grid(row=2, column=0, columnspan=7, pady=(0, 5))
        
        # --- ZONA TABS (Center) ---
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=1, column=0, sticky="nsew")
        self.tabview.add("Terminals")
        self.tabview.add("Live Graph")

        # Inizializza il modulo Grafico nel tab
        self.live_graph = LiveGraph(self.tabview.tab("Live Graph"), max_points=config.settings["MAX_GRAPH_POINTS"])
        self.live_graph.pack(fill="both", expand=True)

        # Tab Terminals
        self.terminals_container = ctk.CTkFrame(self.tabview.tab("Terminals"), fg_color="transparent")
        self.terminals_container.pack(fill="both", expand=True)
        self.terminals_container.grid_rowconfigure(1, weight=1)

        self.filter_entry = ctk.CTkEntry(self.terminals_container, placeholder_text="🔍 Filter Flow Data (Regex or Text)...", height=30)
        self.filter_entry.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5))

        self.fixed_frame = ctk.CTkFrame(self.terminals_container)
        self.fixed_frame.grid_rowconfigure(1, weight=1)
        self.fixed_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.fixed_frame, text="● FIXED MODE", font=("Consolas", 14, "bold"), text_color=config.settings["COLOR"]["FIXED_MODE_COLOR"]).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.fixed_textbox = ctk.CTkTextbox(self.fixed_frame, font=("Consolas", 14), activate_scrollbars=True)
        self.fixed_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.flow_frame = ctk.CTkFrame(self.terminals_container)
        self.flow_frame.grid_rowconfigure(1, weight=1)
        self.flow_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.flow_frame, text="≈ FLOW MODE", font=("Consolas", 14, "bold"), text_color=config.settings["COLOR"]["FLOW_MODE_COLOR"]).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.flow_textbox = ctk.CTkTextbox(self.flow_frame, font=("Consolas", 14), activate_scrollbars=True)
        self.flow_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # --- ZONA INPUT (Bottom) ---
        self.input_frame = ctk.CTkFrame(self.main_frame)
        self.input_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type a command...", font=("Consolas", 14))
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=10)
        self.input_entry.bind("<Return>", self.send_command)

        self.send_btn = ctk.CTkButton(self.input_frame, text="Send", width=80, fg_color="#007bff", hover_color="#0056b3", command=self.send_command)
        self.send_btn.grid(row=0, column=1, padx=(5, 10), pady=10)

    # ==========================================
    # --- LOGICA CODA E DATI ---
    # ==========================================
    def process_queue(self):
        try: 
            delay_ms = int(self.delay_entry.get()) if int(self.delay_entry.get()) >= config.settings["MIN_SAFE_DELAY_MS"] else config.settings["MIN_SAFE_DELAY_MS"]
        except ValueError: 
            delay_ms = int(config.settings["DEFAULT_FLOW_DELAY_MS"])
        
        mode = self.mode_menu.get()
        filter_text = self.filter_entry.get().lower()
        lines_processed = False
        graph_needs_update = False
        
        while not self.data_queue.empty():
            raw_line = self.data_queue.get_nowait()
            lines_processed = True
            
            ts_str_ui = datetime.now().strftime("[%H:%M:%S] ")
            ts_str_csv = datetime.now().strftime("%H:%M:%S.%f")[:-3] 
            timestamp_ui = ts_str_ui if self.checkbox_timestamp.get() == 1 else ""

            # 1. Processa la riga (Cervello Dati)
            data = self.data_processor.process_line(raw_line)
            
            # 2. Automazione (Trigger)
            trigger_msg = self.automation.check_triggers(data["raw"])
            if trigger_msg and mode in ["Flow", "Split"]:
                self.flow_textbox.insert(ctk.END, f"{timestamp_ui}⚡ {trigger_msg}\n")
            
            # 3. Grafico
            if data["parsed"]:
                self.live_graph.add_data(
                    data["parsed"]["name"], 
                    data["parsed"]["value"], 
                    data["parsed"]["unit"]
                )
                graph_needs_update = True

            # 4. Logica Salvataggio CSV Avanzata
            if self.logging_var.get():
                log_mode = config.settings.get("CSV_LOG_MODE", "Single Split")
                
                key = data["parsed"]["name"] if data["parsed"] else "[System/Event]"
                val = f"{data['parsed']['value']} {data['parsed']['unit']}".strip() if data["parsed"] else data["raw"]

                if log_mode == "Single Split":
                    self.csv_writers['main'].writerow([ts_str_csv, key, val, "RX"])
                elif log_mode == "Single Flat":
                    self.csv_writers['main'].writerow([ts_str_csv, data["raw"], "RX"])
                elif log_mode == "Multi-file":
                    safe_key = "".join(x for x in key if x.isalnum() or x in " _-")
                    if not safe_key: safe_key = "Unknown"
                    
                    if safe_key not in self.csv_writers:
                        filename = os.path.join(self.current_log_dir, f"log_{self.log_session_id}_{safe_key}.csv")
                        f = open(filename, 'a', newline='', encoding='utf-8')
                        w = csv.writer(f)
                        w.writerow(["Timestamp", "Value", "Direction"]) 
                        self.csv_files[safe_key] = f
                        self.csv_writers[safe_key] = w
                    
                    self.csv_writers[safe_key].writerow([ts_str_csv, val, "RX"])

            # 5. UI: Flow Mode & Distillatore
            if mode in ["Flow", "Split"]:
                if filter_text == "" or filter_text in data["raw"].lower():
                    if data["is_repeat"]:
                        # Distillatore: rimuove l'ultima riga e la rimpiazza con il contatore
                        self.flow_textbox.delete("end-2l", "end-1c")
                        self.flow_textbox.insert(ctk.END, f"{timestamp_ui}{data['raw']} (x{data['repeat_count']})\n")
                    else:
                        self.flow_textbox.insert(ctk.END, f"{timestamp_ui}{data['raw']}\n")
                    self.flow_textbox.see(ctk.END)

            # 6. UI: Fixed Mode
            if mode in ["Fixed", "Split"]:
                if data["parsed"]:
                    self.fixed_data[data["parsed"]["name"]] = f"{timestamp_ui}{data['parsed']['value']} {data['parsed']['unit']}"
                else:
                    self.fixed_data["[System/Event]"] = f"{timestamp_ui}{data['raw']}"
                    self.system_event_timestamp = time.time()

        # Controllo scadenza [System/Event]
        timeout_setting = config.settings.get("SYSTEM_EVENT_TIMEOUT_S", "never")
        if timeout_setting != "never" and self.system_event_timestamp is not None:
            if time.time() - self.system_event_timestamp >= int(timeout_setting):
                if "[System/Event]" in self.fixed_data:
                    del self.fixed_data["[System/Event]"] 
                self.system_event_timestamp = None 
                lines_processed = True 

        # Aggiornamento UI Terminali a fine ciclo
        if lines_processed and mode in ["Fixed", "Split"]:
            self.fixed_textbox.delete("1.0", ctk.END)
            for key, val in self.fixed_data.items():
                self.fixed_textbox.insert(ctk.END, f"{key}: {val}\n")

        if graph_needs_update:
            self.live_graph.update_plot()

        self.after(delay_ms, self.process_queue)

    # ==========================================
    # --- METODI UI E SETTINGS ---
    # ==========================================
    def toggle_logging(self):
        if self.logging_var.get():
            home_dir = os.path.expanduser('~')
            log_dir = os.path.join(home_dir, "Documents", "Advanced Serial Reader", "log")
            os.makedirs(log_dir, exist_ok=True)
            
            self.log_session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.current_log_dir = log_dir
            mode = config.settings.get("CSV_LOG_MODE", "Single Split")

            try:
                if mode in ["Single Split", "Single Flat"]:
                    filename = os.path.join(log_dir, f"log_{self.log_session_id}.csv")
                    f = open(filename, 'a', newline='', encoding='utf-8')
                    w = csv.writer(f)
                    
                    if mode == "Single Split":
                        w.writerow(["Timestamp", "Sensor/Event", "Value", "Direction"])
                    else:
                        w.writerow(["Timestamp", "Data", "Direction"])
                        
                    self.csv_files['main'] = f
                    self.csv_writers['main'] = w
                    self.show_status(f"Log avviato: {mode}", "#17a2b8")
                
                elif mode == "Multi-file":
                    self.show_status("Log Multi-file avviato in Documenti.", "#17a2b8")

            except Exception as e:
                self.show_status(f"Errore creazione Log: {e}", "red")
                self.logging_var.set(False)
        else:
            for f in self.csv_files.values():
                f.close()
            self.csv_files.clear()
            self.csv_writers.clear()
            self.show_status("Logging fermato.", "orange")

    def clear_buffer(self):
        self.buffer_str = ""

    def send_macro(self, command):
        self.input_entry.delete(0, ctk.END)
        self.input_entry.insert(0, command)
        self.send_command()

    def refresh_macro_buttons(self):
        for widget in self.macros_container.winfo_children():
            widget.destroy()
        for macro_name, macro_cmd in config.settings.get("MACROS", {}).items():
            btn = ctk.CTkButton(
                self.macros_container, text=macro_name, 
                command=lambda cmd=macro_cmd: self.send_macro(cmd), 
                fg_color="#444444", hover_color="#666666"
            )
            btn.pack(pady=5, padx=20, fill="x")

    def open_macro_manager(self):
        MacroManagerWindow(self, app_instance=self)

    def open_script_manager(self):
        ScriptManagerWindow(self, app_instance=self)

    def show_status(self, text, color="green"):
        self.status_label.configure(text=text, text_color=color)
        self.after(config.settings["MSG_DURATION_MS"], lambda: self.status_label.configure(text=""))

    def update_port_menu(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if ports:
            self.port_menu.configure(values=ports)
            self.port_menu.set(ports[0])
            self.update_placeholder(ports[0])
        else:
            self.port_menu.configure(values=["No ports found"])
            self.port_menu.set("No ports found")
            self.update_placeholder("No ports")

    def update_placeholder(self, port_name):
        if port_name and "No ports" not in port_name:
            self.input_entry.configure(placeholder_text=f"Press Enter to send to {port_name}...")
        else:
            self.input_entry.configure(placeholder_text="No port connected...")

    def clear_terminals(self):
        self.fixed_data.clear()
        self.fixed_textbox.delete("1.0", ctk.END)
        self.flow_textbox.delete("1.0", ctk.END)

    def change_terminal_layout(self, selected_mode=None):
        mode = self.mode_menu.get()
        self.fixed_frame.grid_remove()
        self.flow_frame.grid_remove()
        
        if mode == "Fixed":
            self.fixed_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            self.terminals_container.grid_columnconfigure(0, weight=1)
            self.terminals_container.grid_columnconfigure(1, weight=0)
        elif mode == "Flow":
            self.flow_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            self.terminals_container.grid_columnconfigure(0, weight=1)
            self.terminals_container.grid_columnconfigure(1, weight=0)
        elif mode == "Split":
            self.fixed_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)
            self.flow_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)
            self.terminals_container.grid_columnconfigure(0, weight=1)
            self.terminals_container.grid_columnconfigure(1, weight=1)

    def open_settings(self):
        SettingsWindow(self, on_update_callback=self.apply_theme_updates, app_instance=self)

    def apply_theme_updates(self):
        ctk.set_appearance_mode(config.settings["APPEARANCE_MODE"])
        ctk.set_default_color_theme(config.settings["COLOR_THEME"])
        self.baud_menu.set(config.settings["DEFAULT_BAUDRATE"])

    # ==========================================
    # --- SERIALE E COMUNICAZIONE ---
    # ==========================================
    def connect_serial(self, silent=False):
        port = self.port_menu.get()
        baudrate = self.baud_menu.get()
        
        self.disconnect_serial(silent=True)
        if not silent: self.clear_terminals()
        self.buffer_str = ""

        if port and "No ports" not in port:
            try:
                self.serial_port = serial.Serial(port, int(baudrate), timeout=0.1)
                self.show_status(f"Connected -> {port} | {baudrate} baud")
                self.is_reading = True
                self.read_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
                self.read_thread.start()
            except serial.SerialException as e:
                self.show_status(f"Connection Error: {e}", "red")
        else:
            self.show_status("Invalid port selected.", "red")

    def disconnect_serial(self, silent=False):
        self.is_reading = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            if not silent: self.show_status("Disconnected.", "orange")

    def serial_read_loop(self):
        while self.is_reading and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    raw_bytes = self.serial_port.read(self.serial_port.in_waiting)
                    
                    if self.hex_view_var.get():
                        hex_str = raw_bytes.hex(' ').upper()
                        self.data_queue.put(f"[HEX] {hex_str}")
                        continue
                        
                    raw_data = raw_bytes.decode('utf-8', errors='ignore')
                    self.buffer_str += raw_data
                    
                    if len(self.buffer_str) > 4096:
                        self.buffer_str = ""
                        continue
                    
                    while '\n' in self.buffer_str:
                        full_line, self.buffer_str = self.buffer_str.split('\n', 1)
                        full_line = full_line.strip()
                        if full_line:
                            self.data_queue.put(full_line)
                            
            except serial.SerialException:
                self.is_reading = False
                if self.auto_reconnect_var.get():
                    self.after(0, lambda: self.show_status("Connection Lost. Reconnecting in 3s...", "red"))
                    delay = config.settings.get("AUTO_RECONNECT_DELAY_MS", 3000)
                    self.after(delay, lambda: self.connect_serial(silent=True))
                break

    def send_command(self, event=None):
        command = self.input_entry.get()
        if self.serial_port and self.serial_port.is_open:
            if command.strip(): 
                try:
                    payload = command + self.terminator_char
                    self.serial_port.write(payload.encode('utf-8'))
                    self.input_entry.delete(0, ctk.END)
                    
                    if self.mode_menu.get() in ["Flow", "Split"]:
                        ts = datetime.now().strftime("[%H:%M:%S] ") if self.checkbox_timestamp.get() == 1 else ""
                        self.flow_textbox.insert(ctk.END, f"{ts}>> SENT: {command}\n")
                        self.flow_textbox.see(ctk.END)
                        
                    if self.logging_var.get():
                        log_mode = config.settings.get("CSV_LOG_MODE", "Single Split")
                        ts_csv = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        
                        if log_mode == "Single Split":
                            self.csv_writers['main'].writerow([ts_csv, "[TX_Command]", command, "TX"])
                        elif log_mode == "Single Flat":
                            self.csv_writers['main'].writerow([ts_csv, f">> SENT: {command}", "TX"])
                        elif log_mode == "Multi-file":
                            if "TX_Commands" not in self.csv_writers:
                                filename = os.path.join(self.current_log_dir, f"log_{self.log_session_id}_TX_Commands.csv")
                                f = open(filename, 'a', newline='', encoding='utf-8')
                                w = csv.writer(f)
                                w.writerow(["Timestamp", "Command", "Direction"])
                                self.csv_files["TX_Commands"] = f
                                self.csv_writers["TX_Commands"] = w
                            self.csv_writers["TX_Commands"].writerow([ts_csv, command, "TX"])
                        
                except serial.SerialException as e:
                    self.show_status(f"Send Error: {e}", "red")
        else:
            self.show_status("Connect to a port first.", "orange")

if __name__ == "__main__":
    app = SerialMonitorApp()
    app.mainloop()