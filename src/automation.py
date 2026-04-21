import config

class AutomationManager:
    def __init__(self, send_callback):
        # Il send_callback è la funzione send_command() del main.py
        self.send_callback = send_callback

    def check_triggers(self, raw_line):
        """
        Controlla se la riga in ingresso attiva un'automazione.
        Ritorna un messaggio per la UI se l'automazione è scattata.
        """
        # Peschiamo il dizionario delle automazioni dal tuo config
        automations = config.settings.get("AUTOMATIONS", {})
        
        for trigger, action in automations.items():
            # Controllo case-insensitive
            if trigger.lower() in raw_line.lower():
                # Invia il comando in background
                self.send_callback(action)
                return f"AUTO-REPLY TRIGERED: '{trigger}' -> Sent command: '{action}'"
                
        return None