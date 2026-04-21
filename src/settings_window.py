import customtkinter as ctk
import config

BAUDRATE_OPTIONS = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]
MODE_OPTIONS = ["Fixed", "Flow", "Split"]
TERMINATOR_OPTIONS = ["\\n (LF)", "\\r\\n (CRLF)", "None"]

# ==========================================
# --- FINESTRA DELLE IMPOSTAZIONI ---
# (Rimasta identica alla precedente)
# ==========================================
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_update_callback, app_instance):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("400x650")
        self.attributes("-topmost", True)
        self.on_update_callback = on_update_callback
        self.app_instance = app_instance

        ctk.CTkLabel(self, text="Application Theme:").pack(pady=(15, 0))
        self.appearance_menu = ctk.CTkOptionMenu(self, values=["Dark", "Light", "System"])
        self.appearance_menu.set(config.settings["APPEARANCE_MODE"])
        self.appearance_menu.pack()

        ctk.CTkLabel(self, text="Default Baudrate:").pack(pady=(15, 0))
        self.baudrate_menu = ctk.CTkOptionMenu(self, values=BAUDRATE_OPTIONS)
        self.baudrate_menu.set(config.settings["DEFAULT_BAUDRATE"])
        self.baudrate_menu.pack()

        # Timeout per eventi di sistema (Fixed)
        ctk.CTkLabel(self, text="System/Event Timeout (s) never or a number:").pack(pady=(15, 0))
        self.timeout_entry = ctk.CTkEntry(self)
        self.timeout_entry.insert(0, str(config.settings["SYSTEM_EVENT_TIMEOUT_S"]))
        self.timeout_entry.pack()
        
        ctk.CTkLabel(self, text="Line Terminator (Send):").pack(pady=(15, 0))
        self.terminator_menu = ctk.CTkOptionMenu(self, values=TERMINATOR_OPTIONS)
        self.terminator_menu.set(self.app_instance.current_terminator_name)
        self.terminator_menu.pack()

        ctk.CTkLabel(self, text="Default Flow Delay (ms):").pack(pady=(15, 0))
        self.delay_entry = ctk.CTkEntry(self)
        self.delay_entry.insert(0, str(config.settings["DEFAULT_FLOW_DELAY_MS"]))
        self.delay_entry.pack()

        self.checkbox_timestamp_default = ctk.CTkCheckBox(self, text="Enable Timestamp by Default")
        self.checkbox_timestamp_default.pack(pady=(15, 0))
        if config.settings["CHECKBOX_TIMESTAMP_DEFAULT"] == 1: self.checkbox_timestamp_default.select()

        ctk.CTkLabel(self, text="Default Flow Mode:").pack(pady=(15, 0))
        self.mode_menu = ctk.CTkOptionMenu(self, values=MODE_OPTIONS)
        self.mode_menu.set(config.settings["DEFAULT_MODE"])
        self.mode_menu.pack()

        ctk.CTkLabel(self, text="Salvataggio CSV:").pack(pady=(15, 0))
        self.csv_log_mode_menu = ctk.CTkOptionMenu(self, values=["Single Split", "Multi-file", "Single Flat"])
        self.csv_log_mode_menu.set(config.settings["CSV_LOG_MODE"])
        self.csv_log_mode_menu.pack()

        ctk.CTkButton(self, text="Save & Apply", command=self.save_settings).pack(pady=30)

    def save_settings(self):
        config.settings["APPEARANCE_MODE"] = self.appearance_menu.get()
        config.settings["DEFAULT_BAUDRATE"] = self.baudrate_menu.get()
        config.settings["CHECKBOX_TIMESTAMP_DEFAULT"] = 1 if self.checkbox_timestamp_default.get() == 1 else 0
        config.settings["DEFAULT_MODE"] = self.mode_menu.get()
        config.settings["SYSTEM_EVENT_TIMEOUT_S"] = self.timeout_entry.get() if self.timeout_entry.get().isdigit() else "never"
        config.settings["CSV_LOG_MODE"] = self.csv_log_mode_menu.get()

        if self.delay_entry.get().isdigit():
            config.settings["DEFAULT_FLOW_DELAY_MS"] = int(self.delay_entry.get())

        self.app_instance.current_terminator_name = self.terminator_menu.get()
        if self.terminator_menu.get() == "\\n (LF)": self.app_instance.terminator_char = '\n'
        elif self.terminator_menu.get() == "\\r\\n (CRLF)": self.app_instance.terminator_char = '\r\n'
        else: self.app_instance.terminator_char = ''

        config.save()
        self.on_update_callback()
        self.destroy()
