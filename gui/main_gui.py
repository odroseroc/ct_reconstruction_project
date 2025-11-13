import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from unittest import case

from PIL import Image, ImageTk
import numpy as np
import threading
import time
from PIL import Image, ImageTk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from xrsource import XRSController

# ====== Mock GUI para control de RX, Motor y Cámara ====== #

class TomographyGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tomography Control Panel (Mock GUI)")
        self.geometry("1200x900")
        self.configure(bg="#e0e0e0")

        # X-ray source state (global)
        self.rx_on = False

        # --- General laout ---
        self.columnconfigure(0, minsize=350, weight=1)
        self.columnconfigure(1, weight=10)
        self.rowconfigure(0, weight=1)

        ########## Left panel: Control tabs + log console ##########
        left_frame = tk.Frame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.rowconfigure(0, weight=0)
        left_frame.rowconfigure(1, weight=3)
        left_frame.rowconfigure(2, weight=6)
        left_frame.columnconfigure(0, weight=1)

        # --- Global X-ray indicator ---
        self.rx_indicator = tk.Label(
            left_frame,
            text="X-RAY OFF",
            bg="gray20",
            fg="white",
            font=("Arial", 14, "bold"),
            relief="sunken",
            width=20,
            height=2
        )
        self.rx_indicator.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        # Notebook with tabs
        left_notebook = ttk.Notebook(left_frame)
        left_notebook.grid(row=1, column=0, sticky="nsew")

        self.tab_xrsource = ttk.Frame(left_notebook)
        self.tab_motor = ttk.Frame(left_notebook)
        self.tab_camera = ttk.Frame(left_notebook)
        left_notebook.add(self.tab_xrsource, text="X-Ray Source")
        left_notebook.add(self.tab_motor, text="Motor Control")
        left_notebook.add(self.tab_camera, text="Camera & Acquisition")

        # Log below notebook
        log_frame = ttk.LabelFrame(left_frame, text="Log")
        log_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        self.log = scrolledtext.ScrolledText(log_frame, state="normal", height=15)
        self.log.pack(expand=True, fill="both")

        ########## Right panel: visualization ##########
        vis_panel = tk.Frame(self, bg="#f5f5f5")
        vis_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        vis_panel.rowconfigure(0, weight=2)
        vis_panel.rowconfigure(1, weight=2)
        vis_panel.rowconfigure(2, weight=1)
        vis_panel.columnconfigure(0, weight=1)

        # Class attributes to embed matplotlib in the visualization panel
        self.fig = Figure(figsize=(4, 3), dpi=100, layout="constrained")
        self.ax_snap = self.fig.add_subplot(111)
        self.ax_snap.axis("off")
        blank = np.zeros((3036, 4024), dtype='uint16')
        self.snap_im = self.ax_snap.imshow(blank, cmap='gray', vmin=0, vmax=4096, aspect='auto')

        # --- Right panel (live + snapshot + log) ---
        self.build_vis_panel(vis_panel)

        # --- Tabs ---
        self.build_xrsource_tab()
        self.build_motor_tab()
        self.build_camera_tab()

        # Iniciar parpadeo del indicador RX
        self.after(500, self.toggle_rx_indicator)

        ########## Device components ##########
        self.xrs = None
        self.cam = None
        self.cam_devmgr = None
        self.motor = None

        self.streaming = False

    # ============================================================
    #   Tab 1: X-ray source
    # ============================================================
    def build_xrsource_tab(self):
        f = self.tab_xrsource
        f.columnconfigure(0, weight=1)

        # --- Voltage / Corriente ---
        frame_vc = ttk.Frame(f)
        frame_vc.grid(row=1, column=0, pady=10)

        self.volt_indicator, self.volt_setter = self._build_act_set_box(frame_vc, "Tube Voltage", "kV", 0)
        self.curr_indicator, self.curr_setter = self._build_act_set_box(frame_vc, "Tube Current", "µA", 1)

        # --- Botones ON/OFF ---
        frame_btns = ttk.Frame(f)
        frame_btns.grid(row=2, column=0, pady=10)
        self.btn_xon = tk.Button(frame_btns, text="X-Ray ON", bg="#008080", fg="white",
                                 width=12, command=self.xon, state=tk.DISABLED)
        self.btn_xon.grid(row=0, column=0, padx=10)
        self.btn_xoff = tk.Button(frame_btns, text="X-Ray OFF", bg="red", fg="white",
                                  width=12, command=self.xoff, state=tk.DISABLED)
        self.btn_xoff.grid(row=0, column=1, padx=10)

        # --- Focus Mode ---
        frame_focus = ttk.Frame(f)
        frame_focus.grid(row=3, column=0, pady=10)
        ttk.Label(frame_focus, text="Focus Mode:", foreground="blue").grid(row=0, column=0)
        self.combo_focus = ttk.Combobox(frame_focus, values=["Small", "Medium", "Large"], width=10)
        self.combo_focus.current(0)
        self.combo_focus.grid(row=0, column=1, padx=5)

        # --- Indicadores verdes/rojos ---
        frame_ind = ttk.Frame(f)
        frame_ind.grid(row=4, column=0, pady=10)
        self.xrs_indicators = {}
        labels = ["X-RAY", "WARMUP", "PREHEAT", "OVER", "INTERLOCK", "ERROR"]
        for i, lbl in enumerate(labels):
            col = i % 3
            row = i // 3
            box = tk.Label(frame_ind, text=f" {lbl} ", bg="green", fg="white", width=10)
            box.grid(row=row, column=col, padx=5, pady=3)
            self.xrs_indicators[lbl] = box

        # --- Puerto serial ---
        xrs_port_frame = ttk.Frame(f)
        xrs_port_frame.grid(row=5, column=0, pady=10, sticky="ew")
        ttk.Label(xrs_port_frame, text="Serial Port:").grid(row=0, column=0)
        self.xrs_port_entry = ttk.Entry(xrs_port_frame, width=10)
        self.xrs_port_entry.insert(0, "COM4")
        self.xrs_port_entry.grid(row=0, column=1, padx=5)
        ttk.Button(xrs_port_frame, text="Connect", command=self.init_xrs).grid(row=0, column=2, padx=5)

    # Helper function to create boxes Act/Set
    def _build_act_set_box(self, parent, title, unit, col):
        lf = ttk.LabelFrame(parent, text=title, padding=5, relief="ridge")
        lf.grid(row=0, column=col, padx=8, sticky="ew")
        lf.columnconfigure(1, weight=1)
        tk.Label(lf, text="Act", fg="blue").grid(row=0, column=0, sticky="nsew", pady=(0,10))
        act_field = tk.Label(lf, text="0", bg="black", fg="red", width=6, font=("Arial", 14), anchor="e").grid(row=0, column=1)
        tk.Label(lf, text=unit).grid(row=0, column=2, sticky="w")

        if unit == "kV":
            limit = 130
        else:
            limit = 300

        tk.Label(lf, text="Set", fg="blue").grid(row=1, column=0, sticky="nsew", pady=(0,10))
        set_field = tk.Spinbox(lf, from_=0, to=limit, increment=1, font=("Consolas", 16), justify="right", width=7).grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        # tk.Entry(lf, width=6, font=("Arial", 14), justify="right").grid(row=1, column=1)
        # tk.Label(lf, text=unit).grid(row=1, column=2, sticky="w")
        return act_field, set_field

    # ============================================================
    #   Pestaña 2: Motor Control
    # ============================================================
    def build_motor_tab(self):
        f = self.tab_motor
        f.columnconfigure(0, weight=1)

        # Posición actual
        pos_frame = ttk.Frame(f)
        pos_frame.grid(row=1, column=0, pady=10)
        ttk.Label(pos_frame, text="Position (°):", foreground="blue").grid(row=0, column=0)
        self.motor_pos_indicator = tk.Label(pos_frame, text="0.00", bg="black", fg="red", width=10).grid(row=0, column=1, padx=5)

        # Flechas movimiento
        move_frame = ttk.Frame(f)
        move_frame.grid(row=2, column=0, pady=5)
        tk.Button(move_frame, text="◀", width=4).grid(row=0, column=0, padx=5)
        tk.Button(move_frame, text="▶", width=4).grid(row=0, column=1, padx=5)

        # STEP y GO TO
        config_frame = ttk.Frame(f)
        config_frame.grid(row=3, column=0, pady=10)
        ttk.Label(config_frame, text="STEP (°):").grid(row=0, column=0)
        self.motor_step_entry = ttk.Entry(config_frame, width=8).grid(row=0, column=1, padx=5)
        ttk.Label(config_frame, text="GO TO (°):").grid(row=1, column=0)
        self.motor_goto_entry = ttk.Entry(config_frame, width=8).grid(row=1, column=1, padx=5)
        ttk.Button(config_frame, text="GO").grid(row=1, column=2, padx=5)

        # Indicadores motor
        ind_frame = ttk.Frame(f)
        ind_frame.grid(row=4, column=0, pady=10)
        labels = ["REFERENCED", "READY", "MOVING"]
        self.motor_inds = {}
        for i, lbl in enumerate(labels):
            box = tk.Label(ind_frame, text=f" {lbl} ", bg="green", fg="white", width=12)
            box.grid(row=0, column=i, padx=5, pady=3)
            self.motor_inds[lbl] = box

        # Puerto serial motor
        motor_port_frame = ttk.Frame(f)
        motor_port_frame.grid(row=5, column=0, pady=10, sticky="ew")
        ttk.Label(motor_port_frame, text="Motor Port:").grid(row=0, column=0)
        self.motor_port_entry = ttk.Entry(motor_port_frame, width=10)
        self.motor_port_entry.insert(0, "COM6")
        self.motor_port_entry.grid(row=0, column=1, padx=5)
        ttk.Button(motor_port_frame, text="Set").grid(row=0, column=2, padx=5)

    # ============================================================
    #   Pestaña 3: Cámara y Adquisición
    # ============================================================
    def build_camera_tab(self):
        f = self.tab_camera
        f.columnconfigure(0, weight=1)

        # Config cámara (mock)
        cam_frame = ttk.LabelFrame(f, text="Camera Settings")
        cam_frame.grid(row=1, column=0, pady=5, padx=5, sticky="ew")
        for i, (label, default) in enumerate([
            ("Exposure (s)", "0.1"),
            ("Gain", "0"),
            ("Pixel Size (µm)", "3"),
        ]):
            ttk.Label(cam_frame, text=label).grid(row=i, column=0, sticky="e")
            e = ttk.Entry(cam_frame)
            e.insert(0, default)
            e.grid(row=i, column=1, padx=5, pady=2, sticky="w")

        # Botones cámara
        btn_frame = ttk.Frame(cam_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Init Camera").grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Start Live").grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Stop Live").grid(row=0, column=2, padx=5)

        # Config adquisición
        acq_frame = ttk.LabelFrame(f, text="Acquisition Settings")
        acq_frame.grid(row=2, column=0, pady=5, padx=5, sticky="ew")
        labels = ["Step (°)", "# Steps", "Images/Step", "Start Pos (°)", "Base Folder"]
        defaults = ["90", "4", "5", "-180", "C:/Xray/Images"]
        for i, (lbl, val) in enumerate(zip(labels, defaults)):
            ttk.Label(acq_frame, text=lbl).grid(row=i, column=0, sticky="e")
            e = ttk.Entry(acq_frame, width=25)
            e.insert(0, val)
            e.grid(row=i, column=1, sticky="w", pady=2)
        ttk.Button(acq_frame, text="Browse...").grid(row=4, column=2, padx=5)
        ttk.Button(acq_frame, text="Start", style="Accent.TButton").grid(row=5, column=1, pady=10)

    # ============================================================
    #   Panel derecho: Live, Snapshot, Log
    # ============================================================
    def build_vis_panel(self, parent):
        live_frame = ttk.LabelFrame(parent, text="Live Preview")
        live_frame.grid(row=0, column=0, sticky="nsew", pady=5)
        self.live_label = tk.Label(live_frame, bg="black")
        self.live_label.pack(expand=True, fill="both")

        # Sapshot preview (Matplotlib, compact)
        snap_frame = ttk.LabelFrame(parent, text="Last Image")
        snap_frame.grid(row=1, column=0, sticky="nsew", pady=3)
        # Create a very smal figure and canvas
        self.canvas=FigureCanvasTkAgg(self.fig, master=snap_frame)
        toolbar = NavigationToolbar2Tk(canvas=self.canvas)
        toolbar.update()
        widget = self.canvas.get_tk_widget()
        widget.config(width=540, height=405)
        widget.pack()

        # log_frame = ttk.LabelFrame(parent, text="Log")
        # log_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        # self.log = scrolledtext.ScrolledText(log_frame, state="normal", height=10)
        # self.log.pack(expand=True, fill="both")

    # ============================================================
    #   Lógica visual simulada
    # ============================================================
    def toggle_rx(self):
        self.rx_on = not self.rx_on
        self.log.insert(tk.END, f"{time.strftime('%H:%M:%S')} - RX {'ON' if self.rx_on else 'OFF'}\n")
        self.log.see(tk.END)

    def toggle_rx_indicator(self):
        color = "red" if self.rx_on else "gray"
        current_color = self.rx_indicator.cget("bg")
        self.rx_indicator.config(bg=color if current_color != color else color)
        self.after(500, self.toggle_rx_indicator)

    # ==============================================================
    #    Loger
    # ==============================================================
    def log_msg(self, msg):
        self.log.config(state='normal')
        self.log.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {msg}\n")
        self.log.see(tk.END)
        self.log.config(state='disabled')

    # ==============================================================
    #    Devices initializers
    # ==============================================================
    def init_xrs(self):
        port = self.xrs_port_entry.get().strip()
        try:
            self.xrs = XRSController(port=port)
        except Exception as e:
            tk.messagebox.showerror(title="X-Ray init error", message=f"Failed to initialize X-ray source in port {port}:\n {e}")
            self.xrs = None
        finally:
            if self.xrs:
                self.xrs.show_status(log_fn=self.log_msg)



    # ==============================================================
    #    Proxy functions
    # ==============================================================

    # ---- X-ray Source ----
    def xon(self):
        if self.xrs is None:
            pass
        else:
            status = self.xrs.get_status()
            match status:
                case "STS 0":
                    self.xrs.start_warmup()
                case "STS 2":
                    self.xrs.xon()
                case _:
                    pass

    def xoff(self):
        if self.xrs is None:
            pass
        else:
            self.xrs.xoff()


    # ===============================================================
    #    Status functions
    # ===============================================================

    # ---- X-ray Source ----
    def xrs_status(self):
        if self.xrs is None:
            pass
        else:
            pass

if __name__ == "__main__":
    app = TomographyGUI()
    app.mainloop()