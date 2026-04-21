import importlib.util
import os
import re

class DataProcessor:
    def __init__(self):
        self.last_line = ""
        self.repeat_count = 1
        
        # Questa Regex è il cuore dell'estrazione.
        # Cattura pattern come: "Temperatura: 25.5 C", "Pressione=1000", "Volt: -5.2V"
        # Gruppo 1: Nome (lettere, numeri, spazi, _, -)
        # Gruppo 2: Valore numerico (anche con virgola e segno negativo)
        # Gruppo 3: Unità di misura (opzionale, lettere o %)
        self.pattern = re.compile(r"([a-zA-Z0-9_\-\s]+)[:=]\s*([+-]?\d*\.?\d+)\s*([a-zA-Z%]+)?")

    def process_line(self, raw_line):
        raw_line = raw_line.strip()
        
        # --- LOGICA DISTILLATORE ---
        if raw_line == self.last_line and raw_line != "":
            self.repeat_count += 1
            is_repeat = True
        else:
            self.last_line = raw_line
            self.repeat_count = 1
            is_repeat = False

        # --- LOGICA PARSING ---
        parsed_data = None
        match = self.pattern.search(raw_line)
        
        if match:
            parsed_data = {
                "name": match.group(1).strip(),
                "value": float(match.group(2)),
                "unit": match.group(3).strip() if match.group(3) else ""
            }

        return {
            "raw": raw_line,
            "parsed": parsed_data,
            "is_repeat": is_repeat,
            "repeat_count": self.repeat_count
        }