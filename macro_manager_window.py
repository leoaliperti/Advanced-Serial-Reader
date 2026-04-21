import customtkinter as ctk
import config

# ==========================================
# --- FINESTRA GESTIONE MACRO ---
# ==========================================
class MacroManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.title("Manage Macros")
        self.geometry("450x400")
        self.attributes("-topmost", True)
        self.app_instance = app_instance

        # Titolo
        ctk.CTkLabel(self, text="Le tue Macro", font=("Arial", 16, "bold")).pack(pady=(15, 5))

        # Lista scorrevole delle macro esistenti
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # Area per aggiungere una nuova macro
        self.add_frame = ctk.CTkFrame(self)
        self.add_frame.pack(fill="x", padx=15, pady=15)
        
        self.name_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Nome Pulsante", width=120)
        self.name_entry.grid(row=0, column=0, padx=5, pady=10)
        
        self.cmd_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Comando (es. RST)", width=180)
        self.cmd_entry.grid(row=0, column=1, padx=5, pady=10)
        
        ctk.CTkButton(self.add_frame, text="Aggiungi", command=self.add_macro, width=80).grid(row=0, column=2, padx=5, pady=10)

        self.refresh_list()

    def refresh_list(self):
        # Pulisce la lista visiva
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        # Ridisegna le macro attuali
        macros = config.settings.get("MACROS", {})
        if not macros:
            ctk.CTkLabel(self.list_frame, text="Nessuna macro presente.", text_color="gray").pack(pady=20)
            return

        for name, cmd in macros.items():
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=name, font=("Arial", 12, "bold"), width=100, anchor="w").pack(side="left", padx=(5, 10))
            ctk.CTkLabel(row, text=cmd, font=("Consolas", 12), text_color="#17a2b8", width=150, anchor="w").pack(side="left")
            ctk.CTkButton(row, text="🗑", width=30, fg_color="#dc3545", hover_color="#c82333", command=lambda n=name: self.delete_macro(n)).pack(side="right", padx=5)

    def add_macro(self):
        name = self.name_entry.get().strip()
        cmd = self.cmd_entry.get().strip()
        
        if name and cmd:
            if "MACROS" not in config.settings: 
                config.settings["MACROS"] = {}
                
            config.settings["MACROS"][name] = cmd
            config.save() # Salva nel file config.json
            
            self.name_entry.delete(0, 'end')
            self.cmd_entry.delete(0, 'end')
            self.refresh_list()
            self.app_instance.refresh_macro_buttons() # Aggiorna la barra laterale principale

    def delete_macro(self, name):
        if name in config.settings["MACROS"]:
            del config.settings["MACROS"][name]
            config.save()
            self.refresh_list()
            self.app_instance.refresh_macro_buttons()
