import customtkinter as ctk
import threading
import time
from datetime import datetime
import os
from tkinter import ttk
from tkinter import filedialog
from script_guide import ScriptGuideWindow


class ScriptManagerWindow(ctk.CTkToplevel):
    def __init__(self, master, app_instance, **kwargs):
        super().__init__(master, **kwargs)
        
        self.app_instance = app_instance # Riferimento al main.py per usare la porta seriale
        self.title("Script Manager")
        self.geometry("900x600")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)

        # Variabili di stato dello script
        self.script_thread = None
        self.is_running = False
        self.use_timestamp = False

        self.setup_ui()

    def setup_ui(self):
        # --- TOP BAR (Controlli) ---
        self.top_frame = ctk.CTkFrame(self, height=50, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # -- RUN
        self.btn_run = ctk.CTkButton(self.top_frame, text="▶ Run Script", fg_color="#28a745", hover_color="#218838", command=self.start_script)
        self.btn_run.pack(side="left", padx=5)

        # -- STOP
        self.btn_stop = ctk.CTkButton(self.top_frame, text="⏹ Stop", fg_color="#dc3545", hover_color="#c82333", state="disabled", command=self.stop_script)
        self.btn_stop.pack(side="left", padx=5)

        # -- SAVE
        self.btn_save = ctk.CTkButton(self.top_frame, text="💾 Save", fg_color="#007bff", hover_color="#0056b3", command=self.save_script)
        self.btn_save.pack(side="left", padx=5)

        # -- CLEAR
        self.btn_clear = ctk.CTkButton(self.top_frame, text="🗑 Clear Output", fg_color="gray", hover_color="darkgray", command=self.clear_output)
        self.btn_clear.pack(side="right", padx=5)

        # -- GUIDE
        self.btn_guide = ctk.CTkButton(self.top_frame, text="📜 Script Guide", fg_color="#007bff", hover_color="#0056b3", command=self.open_script_guide)
        self.btn_guide.pack(side="right", padx=5)

        # --- SINISTRA: EDITOR SCRIPT ---
        self.editor_frame = ctk.CTkFrame(self)
        self.editor_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        self.editor_frame.grid_rowconfigure(1, weight=1)
        self.editor_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.editor_frame, text="📝 Script Editor (Python syntax)", font=("Arial", 14, "bold")).grid(row=0, column=0, pady=5, sticky="w", padx=10)
        
        self.editor_textbox = ctk.CTkTextbox(self.editor_frame, font=("Consolas", 14), wrap="none")
        self.editor_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Testo di esempio
        default_script = """# --- Esempio di Script ---
timestamp(True)
printOut("Inizio sequenza di test...")

serialWrite("PING")
delay(1000)

risposta = serialRead()
if risposta:
    printOut("Ricevuto: " + risposta)
else:
    printOut("Nessuna risposta.")

printOut("Test completato!")
"""
        self.editor_textbox.insert("1.0", default_script)

        # --- DESTRA: OUTPUT E TABELLE ---
        # Usiamo un Tabview per avere sia la Console che la Tabella
        self.right_tabview = ctk.CTkTabview(self)
        self.right_tabview.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))
        
        self.tab_console = self.right_tabview.add("Console")
        self.tab_table = self.right_tabview.add("Data Table")

        # Configurazione Console Tab
        self.tab_console.grid_rowconfigure(0, weight=1)
        self.tab_console.grid_columnconfigure(0, weight=1)
        self.output_textbox = ctk.CTkTextbox(self.tab_console, font=("Consolas", 14), state="disabled")
        self.output_textbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Configurazione Table Tab
        self.tab_table.grid_rowconfigure(0, weight=1)
        self.tab_table.grid_columnconfigure(0, weight=1)
        
        # Stile della tabella per farla combaciare con il tema scuro
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#333333", foreground="white", font=("Arial", 12, "bold"))
        style.map('Treeview', background=[('selected', '#1f538d')]) # Colore riga selezionata

        self.data_table = ttk.Treeview(self.tab_table, show="headings")
        self.data_table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    # ==========================================
    # --- MOTORE DI SCRIPTING E API ---
    # ==========================================
    def api_printOut(self, text):
        """Stampa un testo nella console di destra."""
        if not self.is_running: return
        ts = datetime.now().strftime("[%H:%M:%S] ") if self.use_timestamp else ""
        msg = f"{ts}{text}\n"
        # Usiamo after() perché non possiamo modificare la UI da un thread secondario
        self.after(0, self._insert_output, msg)

    def _insert_output(self, msg):
        self.output_textbox.configure(state="normal")
        self.output_textbox.insert(ctk.END, msg)
        self.output_textbox.see(ctk.END)
        self.output_textbox.configure(state="disabled")

    def api_timestamp(self, state: bool):
        """Attiva o disattiva i timestamp nell'output."""
        self.use_timestamp = state

    def api_delay(self, ms: int):
        """Mette in pausa lo script per X millisecondi."""
        time.sleep(ms / 1000.0)

    def api_serialWrite(self, text):
        """Invia un comando sulla porta seriale."""
        if self.app_instance.serial_port and self.app_instance.serial_port.is_open:
            # Usa il terminatore selezionato nel main
            terminator = self.app_instance.terminator_char
            payload = str(text) + terminator
            self.app_instance.serial_port.write(payload.encode('utf-8'))
            self.api_printOut(f">> SENT: {text}")
        else:
            self.api_printOut("[ERRORE] Porta seriale non connessa.")

    def api_serialRead(self, timeout_ms=2000):
        """
        Tenta di leggere una riga dalla coda dei dati in arrivo.
        Attende al massimo timeout_ms.
        """
        start_time = time.time()
        while time.time() - start_time < (timeout_ms / 1000.0):
            if not self.is_running: return None
            # Prende i dati dalla coda del main.py
            if not self.app_instance.data_queue.empty():
                line = self.app_instance.data_queue.get_nowait()
                return line
            time.sleep(0.05) # Pausa breve per non bloccare la CPU
        return None
    
    def api_showTable(self, headers, matrix_data):
        """
        Crea e popola la tabella visiva.
        headers: lista di nomi delle colonne (es. ["Tempo", "Valore"])
        matrix_data: lista di liste con i dati (es. [ ["10:00", 25], ["10:01", 26] ])
        """
        if not self.is_running: return

        def update_ui():
            # 1. Cambia automaticamente alla scheda della tabella
            self.right_tabview.set("Data Table")
            
            # 2. Pulisce i dati vecchi
            for item in self.data_table.get_children():
                self.data_table.delete(item)
            
            # 3. Imposta le nuove colonne
            self.data_table["columns"] = headers
            for col in headers:
                self.data_table.heading(col, text=col)
                # Adatta la larghezza e centra il testo
                self.data_table.column(col, width=120, anchor="center") 
                
            # 4. Inserisce le righe (la matrice)
            for row in matrix_data:
                self.data_table.insert("", "end", values=row)

        # Usiamo after() per fare l'aggiornamento grafico in modo sicuro
        self.after(0, update_ui)

    # ==========================================
    # --- GESTIONE ESECUZIONE ---
    # ==========================================
    def start_script(self):
        if self.is_running: return
        
        script_code = self.editor_textbox.get("1.0", ctk.END).strip()
        if not script_code: return

        self.is_running = True
        self.btn_run.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.api_printOut("--- ESECUZIONE SCRIPT AVVIATA ---")

        # Avviamo lo script in un thread per non bloccare l'interfaccia
        self.script_thread = threading.Thread(target=self.run_script_thread, args=(script_code,), daemon=True)
        self.script_thread.start()

    def run_script_thread(self, script_code):
        # Questo dizionario è "l'universo" in cui gira lo script.
        # Definiamo noi quali funzioni sono disponibili.
        script_environment = {
            "printOut": self.api_printOut,
            "timestamp": self.api_timestamp,
            "delay": self.api_delay,
            "serialWrite": self.api_serialWrite,
            "serialRead": self.api_serialRead,
            "showTable": self.api_showTable,
            "True": True,
            "False": False,
            "str": str,
            "int": int,
            "float": float
        }

        try:
            # Esegue il codice Python fornendo solo le funzioni dell'environment
            exec(script_code, {"__builtins__": None}, script_environment)
        except Exception as e:
            self.api_printOut(f"[ERRORE SCRIPT]: {e}")
        finally:
            self.is_running = False
            self.after(0, self.on_script_finish)

    def stop_script(self):
        """Forza l'interruzione impostando il flag a False."""
        self.is_running = False
        self.api_printOut("--- SCRIPT INTERROTTO DALL'UTENTE ---")

    def on_script_finish(self):
        self.api_printOut("--- ESECUZIONE TERMINATA ---\n")
        self.btn_run.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def clear_output(self):
        self.output_textbox.configure(state="normal")
        self.output_textbox.delete("1.0", ctk.END)
        self.output_textbox.configure(state="disabled")

    def open_script_guide(self):
        ScriptGuideWindow(self, app_instance=self)

    def save_script(self):
        # 1. Trova la cartella "Documenti" dell'utente in modo universale
        docs_folder = os.path.expanduser("~/Documents")
        
        # 2. Crea il percorso completo verso la cartella desiderata
        target_folder = os.path.join(docs_folder, "Advanced Serial Reader", "script")
        
        # 3. Assicurati che la cartella esista (se non esiste, la crea in automatico)
        os.makedirs(target_folder, exist_ok=True)
        
        # 4. Apri la finestra di dialogo chiedendo all'utente il nome del file,
        # partendo direttamente dalla cartella che abbiamo appena creato
        filepath = filedialog.asksaveasfilename(
            initialdir=target_folder,
            defaultextension=".py",
            filetypes=[("Python Scripts", "*.py"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Salva Script"
        )
        
        # 5. Se l'utente ha scelto un nome e non ha cliccato "Annulla", salva il file
        if filepath:
            try:
                # Prende tutto il testo dall'editor (dalla riga 1, carattere 0, fino alla fine)
                script_content = self.editor_textbox.get("1.0", "end-1c")
                
                # Scrive il testo nel file
                with open(filepath, "w", encoding="utf-8") as file:
                    file.write(script_content)
                
                # Manda un messaggio di conferma nell'output
                self.api_printOut(f"[SISTEMA] Script salvato con successo in: \n{filepath}")
            
            except Exception as e:
                self.api_printOut(f"[ERRORE SALVATAGGIO]: {e}")