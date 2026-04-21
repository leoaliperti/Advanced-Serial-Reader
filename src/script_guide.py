import customtkinter as ctk

class ScriptGuideWindow(ctk.CTkToplevel):
    def __init__(self, master, app_instance, **kwargs):
        super().__init__(master, **kwargs)
        
        self.app_instance = app_instance 
        self.title("Script Guide")
        self.geometry("900x600")
        
        # Facciamo in modo che la riga e colonna 0 occupino tutto lo spazio
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.setup_ui()

    def setup_ui(self):
        # Creiamo una textbox che occuperà tutta la finestra
        self.textbox = ctk.CTkTextbox(self, wrap="word", font=("Arial", 14))
        self.textbox.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # --- CONFIGURAZIONE DEGLI STILI (TAGS) ---
        # Definiamo i colori e i font per i vari elementi della guida
        # --- CONFIGURAZIONE DEGLI STILI (TAGS) ---
        # TRUCCO: Usiamo ._textbox per accedere al componente nativo e bypassare il blocco
        self.textbox._textbox.tag_config("h1", font=("Arial", 24, "bold"), foreground="#007bff") # Titolo blu
        self.textbox._textbox.tag_config("h2", font=("Arial", 18, "bold"), foreground="#28a745") # Sezioni verdi
        self.textbox._textbox.tag_config("code_title", font=("Consolas", 15, "bold"), foreground="#ffc107") # Codice giallo
        self.textbox._textbox.tag_config("code_block", font=("Consolas", 14), foreground="#d4d4d4") # Blocchi di codice grigio chiaro
        self.textbox._textbox.tag_config("bold", font=("Arial", 14, "bold"))
        self.textbox._textbox.tag_config("normal", font=("Arial", 14))

        # --- INSERIMENTO DEL TESTO FORMATTATO ---
        self._insert_text("📜 Scripting API Reference Guide\n\n", "h1")
        self._insert_text("Welcome to the Advanced Serial Reader scripting environment. The script engine uses standard Python syntax. Below is the complete list of custom built-in functions you can use to automate your workflows, control the serial port, and manage the UI.\n\n", "normal")

        # Sezione: Console
        self._insert_text("🖨️ Console & Output Commands\n\n", "h2")
        self._insert_text("printOut(text: str)\n", "code_title")
        self._insert_text("Prints a message directly to the script's Console Output tab.\n", "normal")
        self._insert_text("Example: ", "bold")
        self._insert_text("printOut(\"Test initialized.\")\n\n", "code_block")

        self._insert_text("timestamp(state: bool)\n", "code_title")
        self._insert_text("Enables or disables automatic timestamps (e.g., [14:30:05]) for all subsequent printOut calls.\n", "normal")
        self._insert_text("Example: ", "bold")
        self._insert_text("timestamp(True)\n\n\n", "code_block")

        # Sezione: Serial
        self._insert_text("🔌 Serial Communication\n\n", "h2")
        self._insert_text("serialWrite(text: str)\n", "code_title")
        self._insert_text("Sends a string command through the active serial port. It automatically appends the line terminator selected in the main interface.\n", "normal")
        self._insert_text("Example: ", "bold")
        self._insert_text("serialWrite(\"START_SENSOR\")\n\n", "code_block")

        self._insert_text("serialRead(timeout_ms: int = 2000) -> str | None\n", "code_title")
        self._insert_text("Waits for an incoming message from the serial port up to the specified timeout (default is 2000 ms). Returns the received string if a message arrives, or None if the timeout is reached.\n", "normal")
        self._insert_text("Example: ", "bold")
        self._insert_text("response = serialRead(5000)\n\n\n", "code_block")

        # Sezione: Timing
        self._insert_text("⏱️ Timing & Control\n\n", "h2")
        self._insert_text("delay(ms: int)\n", "code_title")
        self._insert_text("Pauses the execution of the script for the specified amount of milliseconds. Essential for waiting for sensor responses without freezing the application.\n", "normal")
        self._insert_text("Example: ", "bold")
        self._insert_text("delay(1500)  # Pauses for 1.5 seconds\n\n\n", "code_block")

        # Sezione: Data Visualization
        self._insert_text("📊 Data Visualization\n\n", "h2")
        self._insert_text("showTable(headers: list, matrix_data: list)\n", "code_title")
        self._insert_text("Automatically switches the view to the \"Data Table\" tab and generates a visual grid.\n", "normal")
        self._insert_text("• headers: A list of strings defining the column names.\n", "normal")
        self._insert_text("• matrix_data: A list of lists, where each inner list represents a row of data.\n", "normal")
        self._insert_text("Example:\n", "bold")
        self._insert_text("cols = [\"Time\", \"Temperature\", \"Status\"]\n"
                         "rows = [\n"
                         "    [\"10:00\", 25.5, \"OK\"],\n"
                         "    [\"10:01\", 26.1, \"OK\"]\n"
                         "]\n"
                         "showTable(cols, rows)\n\n\n", "code_block")

        # Sezione: Tipi Supportati
        self._insert_text("🐍 Supported Python Native Types\n\n", "h2")
        self._insert_text("The environment natively supports the following standard Python functions and types to help you cast and manipulate your variables:\n", "normal")
        self._insert_text("• str(), int(), float()\n"
                         "• Booleans (True, False)\n"
                         "• Standard control flows (if, else, for, while)\n\n", "code_block")

        # Rende la textbox in sola lettura per evitare che l'utente modifichi la guida
        self.textbox.configure(state="disabled")

    def _insert_text(self, text, tag):
        """Funzione helper per inserire il testo applicando lo stile corretto."""
        self.textbox.insert("end", text, tag)