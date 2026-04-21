import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.style as style
import matplotlib.ticker as ticker

class LiveGraph(ctk.CTkFrame):
    def __init__(self, master, max_points=100, **kwargs):
        super().__init__(master, **kwargs)
        
        self.max_points = max_points
        self.is_paused = False
        self.datasets = {} # Conterrà i dati. Es: {"Temperatura": ([x], [y]), "Pressione": ([x], [y])}
        self.counter = 0

        # --- SETUP UI ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.top_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.btn_pause = ctk.CTkButton(self.top_frame, text="⏸ Pause", width=80, fg_color="#ffc107", hover_color="#e0a800", text_color="black", command=self.toggle_pause)
        self.btn_pause.pack(side="left", padx=5)

        self.btn_clear = ctk.CTkButton(self.top_frame, text="🗑 Clear", width=80, fg_color="#dc3545", hover_color="#c82333", command=self.clear_graph)
        self.btn_clear.pack(side="left", padx=5)

        # --- SETUP MATPLOTLIB ---
        # Tema scuro di default per integrarsi bene con customtkinter
        style.use("dark_background") 
        self.figure, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.figure.patch.set_facecolor('#2b2b2b') # Colore background per matchare CTk
        self.ax.set_facecolor('#2b2b2b')
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side="top", fill="both", expand=True)

        # Toolbar nativa di matplotlib (Zoom, Save, Pan)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side="bottom", fill="x")

    def add_data(self, name, value, unit=""):
        if self.is_paused:
            return

        label_name = f"{name} ({unit})" if unit else name

        if label_name not in self.datasets:
            self.datasets[label_name] = ([], []) # (Lista X, Lista Y)

        x_data, y_data = self.datasets[label_name]
        
        x_data.append(self.counter)
        y_data.append(value)

        # Mantieni solo gli ultimi 'max_points'
        if len(x_data) > self.max_points:
            x_data.pop(0)
            y_data.pop(0)

        self.counter += 1

    def update_plot(self):
        if self.is_paused:
            return

        self.ax.clear()
        
        has_data = False
        for label_name, (x_data, y_data) in self.datasets.items():
            if len(x_data) > 0:
                # --- MODIFICA 1: LINEA E PUNTINI ---
                # linewidth: spessore della linea (es. 0.8 è sottile, 2.0 è spessa)
                # markersize: dimensione del pallino del dato (es. 2 o 3 è piccolo)
                self.ax.plot(x_data, y_data, marker='.', markersize=3, linestyle='-', linewidth=0.8, label=label_name)
                has_data = True

        if has_data:
            self.ax.legend(loc='upper left', fontsize=8) 
            self.ax.grid(True, linestyle='--', alpha=0.3)
            
            # --- MODIFICA: Forza solo numeri interi sull'asse X ---
            self.ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
            
            # --- MODIFICA: Fissa dinamicamente i limiti della finestra ---
            # Trova l'X più alto attualmente tracciato
            current_x_max = max([x[-1] for x, y in self.datasets.values() if len(x) > 0])
            
            # Imposta la scala X in modo che sia sempre larga "max_points"
            # (Ad esempio, se siamo a 150 e max_points è 10, la scala andrà da 140 a 150)
            x_min = max(0, current_x_max - self.max_points)
            self.ax.set_xlim(x_min, current_x_max)

        else:
            self.ax.text(0.5, 0.5, "Waiting for data...", ha='center', va='center', color="gray", transform=self.ax.transAxes)

        # Dimensioni font per le scale
        self.ax.tick_params(axis='both', labelsize=8) 

        self.canvas.draw()

        # --- MODIFICA 3: FONT SCALE/ASSI ---
        # labelsize cambia la grandezza dei numeri su entrambi gli assi
        self.ax.tick_params(axis='both', labelsize=5) 

        self.canvas.draw()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.configure(text="▶ Resume", fg_color="#28a745", hover_color="#218838")
        else:
            self.btn_pause.configure(text="⏸ Pause", fg_color="#ffc107", hover_color="#e0a800")

    def clear_graph(self):
        self.datasets.clear()
        self.counter = 0
        self.update_plot()