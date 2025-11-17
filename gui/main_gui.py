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

# Imports handled by lazy import in development phase
# from motor import MotorController
# from xrsource import XRSController

# ====== GUI for X-ray source, rotating stage and camera control ====== #
DEFAULT_DLLPATH = r'C:\Windows\Microsoft.NET\assembly\GAC_64\Newport.SMC100.CommandInterface\v4.0_2.0.0.3__d9d722840772240b\Newport.SMC100.CommandInterface.dll'

class StatusIndicators:
    """
    Administer logical flags of a device and its indicator labels.
    """
    def __init__(self, parent_frame, flags_dict, columns=3):
        """
        parent_frame : Frame where indicators are located
        flags_dict   : dictionary {'FLAG_NAME': bool}
        columns      : number of columns in the grid
        """
        self.parent = parent_frame
        self.flags = flags_dict
        self.columns = columns
        self.widgets = {}   # {'FLAG_NAME': Label}
        self.blinking = {} # { "FLAG" : {"state":bool, "job":after_id} }

        self._build()

    # -----------------------------------------------------------
    def _build(self):
        """Build labels based on the glags dict's keys."""
        for i, key in enumerate(self.flags.keys()):
            row = i // self.columns
            col = i % self.columns

            lbl = tk.Label(
                self.parent,
                text=f" {key} ",
                bg="gray20",
                fg="white",
                width=12
            )
            lbl.grid(row=row, column=col, padx=5, pady=4)
            self.widgets[key] = lbl

    # -----------------------------------------------------------
    def update(self):
        """Update colors according to each flag."""
        for key, widget in self.widgets.items():
            value = self.flags.get(key, False)

            widget.config(bg="green" if value else "red")

    # -----------------------------------------------------------
    def reset(self):
        """Turns OFF all visual indicators."""
        for widget in self.widgets.values():
            widget.config(bg="gray20")

    # -----------------------------------------------------------
    def blink(self, key, color_on="red", color_off="green", interval=500):
        """
        Hace parpadear un indicador específico.
        key : nombre del indicador
        interval : tiempo en ms
        """
        if key not in self.widgets:
            return

        # Si ya está parpadeando, no lo iniciamos de nuevo
        if self.blinking[key]["state"]:
            return

        self.blinking[key]["state"] = True

        def _toggle():
            # Si fue detenido mientras estaba en cola
            if not self.blinking[key]["state"]:
                return

            widget = self.widgets[key]
            current_bg = widget.cget("bg")
            new_bg = color_off if current_bg == color_on else color_on
            widget.config(bg=new_bg)

            # programar el próximo parpadeo
            job = widget.after(interval, _toggle)
            self.blinking[key]["job"] = job

        _toggle()

    # -----------------------------------------------------------
    def stop_blink(self, key):
        """Detiene el parpadeo y devuelve el color normal según la flag."""
        if key not in self.widgets:
            return

        info = self.blinking[key]

        if info["job"] is not None:
            self.widgets[key].after_cancel(info["job"])

        info["state"] = False
        info["job"] = None

        # restaurar color según flag
        val = self.flags.get(key, False)
        self.widgets[key].config(bg="green" if val else "red")


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

        ########## Status flags #########
        # --- X-ray source ---
        self.xrs_indicator_flags = {'X_RAY': False, # True if X-rays can be emitted, but not currently emitting
                          'WARMUP': False,  # Only true if warmup is complete
                          'PREHEAT': True,  # True if no preheat is ongoing
                          'OVER': True,  # True if the source is NOT in STS 4: Overload protection
                          'INTERLOCK': False,  # True if interlock is closed
                          'ERROR': True,  # True if there is NO error
                                    }
        self.xrs_emitting_flag = False
        self.xrs_values = {'volt': 0,
                           'curr': 0,
                           'focus': 0 # 0:small, 1:medium, 2:large
                           }

        ########## Left panel: Control tabs + log console ##########
        left_frame = tk.Frame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.rowconfigure(0, weight=0)
        left_frame.rowconfigure(1, weight=3)
        left_frame.rowconfigure(2, weight=6)
        left_frame.columnconfigure(0, weight=1)

        # --- Global X-ray indicator ---
        self.xrs_emitting_indicator = tk.Label(
            left_frame,
            text="X-RAY OFF",
            bg="gray20",
            fg="white",
            font=("Arial", 14, "bold"),
            relief="sunken",
            width=20,
            height=2
        )
        self.xrs_emitting_indicator.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self._blink_state = False

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
        # self.after(500, self.toggle_rx_indicator)

        ########## Devices ##########
        self.xrs = None
        self.cam = None
        self.cam_devmgr = None
        self.motor = None
        self.streaming = False

        # Try to initialize devices with default values
        self.init_xrs()

        self.after(200, self.update_status_loop)

    # --End __init__

    # ===============================================================
    #    Status loop
    # ===============================================================

    def update_status_loop(self):
        '''Update the states of indicators and buttons'''
        self.update_xrs_status()
        self.update_motor_status()
        self.update_camera_status()
        self.after(100, self.update_status_loop)

    # ---- Update modules ----
    def poll_xrs_status(self):
        # Check interlock status
        interlock = self.xrs.get_interlock_status()
        match interlock:
            case "SIN 0":
                self.xrs_indicator_flags['INTERLOCK'] = False
            case "SIN 1":
                self.xrs_indicator_flags['INTERLOCK'] = True

        status = self.xrs.get_status
        match status:
            case "STS 0":  # Awaiting warmup
                self.xrs_indicator_flags['X_RAY'] = False
                self.xrs_indicator_flags['WARMUP'] = False
                self.xrs_indicator_flags['OVER'] = True
                self.xrs_indicator_flags['PREHEAT'] = True
                self.xrs_indicator_flags['ERROR'] = True
                self.xrs_emitting_flag = False
            case "STS 1":  # Warm-up in progress
                self.xrs_indicator_flags['X_RAY'] = False
                self.xrs_indicator_flags['WARMUP'] = False
                self.xrs_indicator_flags['OVER'] = True
                self.xrs_indicator_flags['PREHEAT'] = True
                self.xrs_indicator_flags['ERROR'] = True
                self.xrs_emitting_flag = True
            case "STS 2": # Ready to emit X-rays
                self.xrs_indicator_flags['X_RAY'] = True
                self.xrs_indicator_flags['WARMUP'] = True
                self.xrs_indicator_flags['OVER'] = True
                self.xrs_indicator_flags['PREHEAT'] = True
                self.xrs_indicator_flags['ERROR'] = True
                self.xrs_emitting_flag = False
            case "STS 3":  # Emitting X-rays
                self.xrs_indicator_flags['X_RAY'] = False
                self.xrs_indicator_flags['WARMUP'] = False
                self.xrs_indicator_flags['OVER'] = True
                self.xrs_indicator_flags['PREHEAT'] = True
                self.xrs_indicator_flags['ERROR'] = True
                self.xrs_emitting_flag = True
            case "STS 4": # Overload protection activated
                self.xrs_indicator_flags['X_RAY'] = False
                self.xrs_indicator_flags['WARMUP'] = False
                self.xrs_indicator_flags['OVER'] = False
                self.xrs_indicator_flags['PREHEAT'] = True
                self.xrs_indicator_flags['ERROR'] = True
                self.xrs_emitting_flag = False

    def blink_emitting_indicator(self):
        """Make the global X-ray indicator blink when X-rays are ON."""
        if self.xrs_emitting_flag:
            self._blink_state = not self._blink_state
            color = "red" if self._blink_state else "green"
            self.xrs_emitting_indicator.config(bg=color)
            self.after(500, self.blink_emitting_indicator)
        else:
            return

    def update_xrs_status(self):
        if not self.xrs:
            self.btn_xon.config(state=tk.DISABLED)
            self.btn_xon.config(state=tk.DISABLED)
            self.xrs_emitting_indicator.config(text="X-Ray Off", bg="gray20")
            for lbl, widget in self.xrs_indicators.items():
                widget.config(bg="gray")
            return
        # If X-ray source is instantiated:
        # Update indicators panel
        self.xrs_indicators.update()
        if not self.xrs_indicator_flags["WARMUP"]:
            self.xrs_indicators.blink("WARMUP")
        else:
            self.xrs_indicators.stop_blink("WARMUP")
        # Handle emission indicators
        if self.xrs_emitting_flag:
            self.xrs_emitting_indicator.config(text="X-Ray ON", bg="red")
            # Blink indicators
            self.blink_emitting_indicator()
            self.xrs_indicators.blink("X_RAY")
        else:
            self.xrs_emitting_indicator.config(text="X-Ray OFF", bg="gray20")
            self.xrs_indicators.stop_blink("X_RAY")
        # Update voltage and current values and indicators
        volt = int(self.volt_entry.get())
        curr = int(self.curr_entry.get())
        focus = self.combo_focus.current()
        if self.xrs_values["volt"] != volt:
            self.xrs.set_voltage(volt)
            self.xrs_values["volt"] = volt
        if self.xrs_values["curr"] != curr:
            self.xrs.set_current(curr)
            self.xrs_values["curr"] = curr
        if self.xrs_values["focus"] != focus:
            self.xrs.set_focal_spot_mode(focus)
            self.xrs_values["focus"] = focus

        act_volt = self.xrs.get_voltage()
        act_curr = self.xrs.get_current()
        self.volt_indicator.config(text=act_volt)
        self.curr_indicator.config(text=act_curr)


    def update_motor_status(self):
        pass

    def update_camera_status(self):
        pass

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
            from xrsource import XRSController
            self.xrs = XRSController(port=port)
        except Exception as e:
            self.xrs = None
            return e
        finally:
            if self.xrs:
                self.log_msg(f"X-Ray source initialized in port {port}\n")
                self.xrs.set_emission_mode(mode=3) # Start the source in continuous mode
                self.xrs.set_auto_off_time(seconds=30)
                self.xrs.set_focal_spot_mode(mode=2)
                self.xrs.show_status(log_fn=self.log_msg)
        return 0

    def init_motor(self):
        port = self.motor_port_entry.get().strip()
        dll = self.motor_dll_entry.get().strip()
        try:
            from motor.motor_controller import MotorController
            self.motor = MotorController(dll_path=dll ,port=port, log_fn=self.log_msg)
        except Execption as e:
            self.motor = None
            return e
        finally:
            if self.motor:
                self.log_msg(f"Motor initialized in port {port}\n")
                status = self.motor.get_positioner_status()
                self.motor.show_positioner_status(statusCode=status, log_fn=self.log_msg)

    # ==============================================================
    #    Proxy functions
    # ==============================================================

    # ---- X-ray Source ----
    def xon(self):
        if not self.xrs:
            return
        status = self.xrs.get_status()
        match status:
            case "STS 0":
                self.xrs.start_warmup()
            case "STS 2":
                self.xrs.xon()
            case _:
                pass

    def xoff(self):
        if not self.xrs:
            return
        self.xrs.xoff()

    def connect_xrs(self):
        e = self.init_xrs()
        if e:
            tk.messagebox.showerror(title="X-Ray init error",
                                    message=f"Failed to initialize X-ray source:\n {e}")

    # ---- Motor ----
    def connect_motor(self):
        e = self.init_motor()
        if e:
            tk.messagebox.showerror(title="Motor init error",
                                    message=f"Failed to initialize rotating stage:\n {e}")



    # ---- Close ----
    def on_close(self):
        if self.xrs:
            self.xrs.close()
        if self.motor:
            self.motor.close()
        self.root.destroy()

    ########## WINDOW ##########
    # ============================================================
    #   Tab 1: X-ray source
    # ============================================================
    def build_xrsource_tab(self):
        f = self.tab_xrsource
        f.columnconfigure(0, weight=1)

        # --- Voltage / Corriente ---
        frame_vc = ttk.Frame(f)
        frame_vc.grid(row=1, column=0, pady=10)

        self.volt_indicator, self.volt_entry = self._build_act_set_box(frame_vc, "Tube Voltage", "kV", 0)
        self.curr_indicator, self.curr_entry = self._build_act_set_box(frame_vc, "Tube Current", "µA", 1)

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
        self.combo_focus.current(2)
        self.combo_focus.current(0)
        self.combo_focus.grid(row=0, column=1, padx=5)

        # --- Indicadores verdes/rojos ---
        frame_ind = ttk.Frame(f)
        frame_ind.grid(row=4, column=0, pady=10)
        self.xrs_indicators = StatusIndicators(
            parent_frame=frame_ind,
            flags_dict=self.xrs_indicator_flags,
            columns=3
        )

        # --- Port ---
        xrs_port_frame = ttk.Frame(f)
        xrs_port_frame.grid(row=5, column=0, pady=10, sticky="w")
        ttk.Label(xrs_port_frame, text="Serial Port:").grid(row=0, column=0)
        self.xrs_port_entry = ttk.Entry(xrs_port_frame, width=10)
        self.xrs_port_entry.insert(0, "COM4")
        self.xrs_port_entry.grid(row=0, column=1, padx=5)
        ttk.Button(xrs_port_frame, text="Connect", command=self.connect_xrs).grid(row=0, column=2, padx=5)

    # Helper function to create voltage and curren indicators and setters
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
        set_field = tk.Spinbox(lf, from_=0, to=limit, increment=1, font=("Arial", 16), justify="right", width=7).grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        # tk.Entry(lf, width=6, font=("Arial", 14), justify="right").grid(row=1, column=1)
        # tk.Label(lf, text=unit).grid(row=1, column=2, sticky="w")
        return act_field, set_field

    # ============================================================
    #   Pestaña 2: Motor Control
    # ============================================================
    def build_motor_tab(self):
        f = self.tab_motor
        f.columnconfigure(0, weight=1)

        # Current position
        pos_frame = ttk.Frame(f)
        pos_frame.grid(row=1, column=0, pady=10)
        ttk.Label(pos_frame, text="Position (°):", foreground="blue").grid(row=0, column=0)
        self.motor_pos_indicator = tk.Label(pos_frame, text="0.00", bg="black", fg="red", width=10, font=("Arial", 14), anchor="e").grid(row=0, column=1, padx=5)

        # Motion arrows
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

        # Motor indicators
        ind_frame = ttk.Frame(f)
        ind_frame.grid(row=4, column=0, pady=10)
        labels = ["REFERENCED", "READY", "MOVING"]
        self.motor_inds = {}
        for i, lbl in enumerate(labels):
            box = tk.Label(ind_frame, text=f" {lbl} ", bg="green", fg="white", width=12)
            box.grid(row=0, column=i, padx=5, pady=3)
            self.motor_inds[lbl] = box

        # Port and DLL
        motor_port_frame = ttk.Frame(f)
        motor_port_frame.grid(row=5, column=0, pady=10, sticky="w")
        # DLL field
        ttk.Label(motor_port_frame, text="Motor DLL:").grid(row=0, column=0)
        self.motor_dll_entry = ttk.Entry(motor_port_frame, width=30)
        self.motor_dll_entry.insert(0, DEFAULT_DLLPATH)
        self.motor_dll_entry.grid(row=0, column=1, padx=5, columnspan=2, pady=5)
        self.btn_motor_dll = ttk.Button(motor_port_frame, text="Browse...").grid(row=0, column=3, padx=5)
        # Port field
        ttk.Label(motor_port_frame, text="Motor Port:").grid(row=1, column=0)
        self.motor_port_entry = ttk.Entry(motor_port_frame, width=10)
        self.motor_port_entry.insert(0, "COM6")
        self.motor_port_entry.grid(row=1, column=1, padx=5,sticky="w")
        self.btn_motor_port = ttk.Button(motor_port_frame, text="Connect").grid(row=1, column=2, padx=5, sticky="w")

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
        current_color = self.xrs_emitting_indicator.cget("bg")
        self.xrs_emitting_indicator.config(bg=color if current_color != color else color)
        self.after(500, self.toggle_rx_indicator)



if __name__ == "__main__":
    app = TomographyGUI()
    app.mainloop()