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

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from gui.widgets import StatusIndicators, ParamsForm
from core.log_utils import no_op
from acq import AcquisitionParams
# Imports handled by lazy import in development phase
# from motor import MotorController
# from xrsource import XRSController

# ====== GUI for X-ray source, rotating stage and camera control ====== #
DEFAULT_DLLPATH = r'C:\Windows\Microsoft.NET\assembly\GAC_64\Newport.SMC100.CommandInterface\v4.0_2.0.0.3__d9d722840772240b\Newport.SMC100.CommandInterface.dll'
UPDATE_INTERVAL_MS = 200  # Interval to update status

class TomographyGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tomography Control Panel (Mock GUI)")
        self.geometry("1500x900")
        self.configure(bg="#e0e0e0")
        self.master_tick = [0] # Global tick for blinking indicators. Must be a mutable type to be parsed by reference.

        # X-ray source state (global)
        self.rx_on = False

        # --- General laout ---
        self.columnconfigure(0, minsize=350, weight=1)
        self.columnconfigure(1, weight=10)
        self.rowconfigure(0, weight=1)

        # --------- STATUS FLAGS ---------
        # --- X-ray source ---
        self.xrs_indicator_flags = {
            'X_RAY': False, # True if X-rays can be emitted, but not currently emitting
            'WARMUP': False,  # Only true if warmup is complete
            'PREHEAT': True,  # True if no preheat is ongoing
            'OVER': True,  # True if the source is NOT in STS 4: Overload protection
            'INTERLOCK': False,  # True if interlock is closed
            'ERROR': True,  # True if there is NO error
            }
        self.xrs_emitting_flag = False

        self.motor_indicator_flags = {
            'REFERENCED': False, # True if motor is referenced
            'READY': False, # True if motor is ready for motion
            'MOVING': False, # True if motor is NOT moving
            }
        
        ########## Values dicts ##########
        self.xrs_values = {'volt': 0,
                           'curr': 0,
                           'focus': 0 # 0:small, 1:medium, 2:large
                           }

        ########## Left panel: Control tabs + log console ##########
        left_frame = tk.Frame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.rowconfigure(0, weight=0)
        left_frame.rowconfigure(1, weight=3)
        left_frame.rowconfigure(2, weight=10)
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
        self._blink_state = False # Flag to toggle emitting indicator color
        self._blink_started = False # Flag to avoid multiple blink loops

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

        ########## Devices ##########
        self.xrs = None
        self.cam = None
        self.cam_devmgr = None
        self.motor = None
        self.streaming = False

        # Try to initialize devices with default values
        self.init_xrs()
        self.init_motor()

        self.after(200, self.update_status_loop)
        # self.after(2000, self.debug_all)

    # --End __init__

    def debug_all(self):
        self.log_msg("----- DEBUG INFO -----")
        self.log_msg(f"XRS status: {self.xrs.get_status() if self.xrs else 'No XRS connected'}")
        self.log_msg("Debugging all devices...")
        if self.xrs:
            self.xrs.show_status(log_fn=self.log_msg)
            self.log_msg("XRS Indicator Flags:")
            for key in self.xrs_indicator_flags.keys():
                self.log_msg(f"{key}: {self.xrs_indicator_flags[key]}")
            self.log_msg(f"XRS Emitting Flag: {self.xrs_emitting_flag}")
        self.after(4000, self.debug_all)

    # ===============================================================
    #    Status loop
    # ===============================================================

    def update_status_loop(self):
        '''Update the states of indicators and buttons'''
        self.master_tick[0] = (self.master_tick[0] + 1) % 1000
        self.update_xrs_status()
        self.update_motor_status()
        self.update_camera_status()
        self.after(UPDATE_INTERVAL_MS, self.update_status_loop)

    # UPDATE MODULES
    # ---------- X-ray source ----------
    def poll_xrs_status(self):
        # Check interlock status
        interlock = self.xrs.get_interlock_status()
        match interlock:
            case "SIN 0":
                self.xrs_indicator_flags['INTERLOCK'] = True
            case "SIN 1":
                self.xrs_indicator_flags['INTERLOCK'] = False

        status = self.xrs.get_status()
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
                self.xrs_indicator_flags['WARMUP'] = True
                self.xrs_indicator_flags['OVER'] = True
                self.xrs_indicator_flags['PREHEAT'] = True
                self.xrs_indicator_flags['ERROR'] = True
                self.xrs_emitting_flag = True
            case "STS 4": # Overload protection activated
                self.xrs_indicator_flags['X_RAY'] = False
                self.xrs_indicator_flags['WARMUP'] = True
                self.xrs_indicator_flags['OVER'] = False
                self.xrs_indicator_flags['PREHEAT'] = True
                self.xrs_indicator_flags['ERROR'] = True
                self.xrs_emitting_flag = False

    def blink_emitting_indicator(self):
        """Make the global X-ray indicator blink when X-rays are ON."""
        if self.master_tick[0] % 2 == 0:
            current_bg = self.xrs_emitting_indicator.cget("bg")
            new_bg = "red" if current_bg == "green" else "green"
            self.xrs_emitting_indicator.config(bg=new_bg)
        return

    def update_xrs_status(self):
        # ---- NO SOURCE CONNECTED ----
        if not self.xrs:
            self.btn_xon.config(state=tk.DISABLED)
            self.btn_xoff.config(state=tk.DISABLED)
            self.xrs_emitting_indicator.config(text="X-Ray Off", bg="gray20")
            self.xrs_indicators.reset()
            return
        # ---- SOURCE CONNECTED ----
        self.poll_xrs_status()
        # Update indicators
        self.xrs_indicators.update()
        if not self.xrs_indicator_flags["WARMUP"]:
            self.xrs_indicators.blink("WARMUP")
        else:
            self.xrs_indicators.stop_blink("WARMUP")
        # Handle emitting indicators
        if self.xrs_emitting_flag:
            self.xrs_emitting_indicator.config(text="X-Ray ON", bg="red")
            self.blink_emitting_indicator()
            self.xrs_indicators.blink("X_RAY")
        else:
            self.xrs_emitting_indicator.config(text="X-Ray OFF", bg="gray20")
            self.xrs_indicators.stop_blink("X_RAY")
        # Update voltage, current and focus settings
        try:
            volt = int(self.volt_entry.get())
            curr = int(self.curr_entry.get())
        except Exception: # GUI still building or invalid input
            return
        
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

        self.btn_xon.config(state=tk.NORMAL)
        self.btn_xoff.config(state=tk.NORMAL)

    # ---------- Motor ----------
    def poll_motor_status(self):
        positioner_status = self.motor.get_positioner_status()
        self.motor_indicator_flags['REFERENCED'] = not(positioner_status.startswith('0') or positioner_status in ['0F', '10', '11'])
        self.motor_indicator_flags['READY'] = positioner_status in ['32', '33', '34', '35']
        self.motor_indicator_flags['MOVING'] = not(positioner_status in ['28', '1E', '1F']) # Indicator is green (True) if NOT moving

    def update_motor_status(self):
        # ---- NO MOTOR CONNECTED ----
        if not self.motor:
            self.btn_bk_step.config(state=tk.DISABLED)
            self.btn_fw_step.config(state=tk.DISABLED)
            self.position_indicator.config(text="N/A")
            self.motor_indicators.reset()
            return
        # ---- MOTOR CONNECTED ----
        self.poll_motor_status()
        # Update indicators
        self.motor_indicators.update()


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
            if not self.xrs:
                from xrsource import XRSController
                self.xrs = XRSController(port=port)
        except Exception as e:
            self.xrs = None
            return e
        finally:
            if self.xrs:
                self.log_msg(f"X-Ray source initialized in port {port}")
                self.xrs.set_emission_mode(mode=3) # Start the source in continuous mode
                self.xrs.set_auto_off_time(seconds=30)
                self.xrs.set_focal_spot_mode(mode=2)
                self.xrs.show_status(log_fn=self.log_msg)
                volt = int(self.xrs.get_preset_voltage())
                curr = int(self.xrs.get_preset_current())
                self.xrs_values['volt'] = volt
                self.xrs_values['curr'] = curr
                self.volt_entry.delete(0, tk.END)
                self.volt_entry.insert(0, str(volt))
                self.curr_entry.delete(0, tk.END)
                self.curr_entry.insert(0, str(curr))
                self.log_msg("-----------------------------------")
        return 0

    def init_motor(self):
        port = self.motor_port_entry.get().strip()
        dll = self.motor_dll_entry.get().strip()
        try:
            if not self.motor:
                from motor.motor_controller import MotorController
                self.motor = MotorController(dll_path=dll ,port=port, log_fn=no_op)
        except Exception as e:
            self.motor = None
            return e
        finally:
            if self.motor:
                self.log_msg(f"Rotating stage initialized in port {port}")
                status = self.motor.get_positioner_status()
                self.motor.show_positioner_status(statusCode=status, log_fn=self.log_msg)
                self.log_msg("------------------------------------")

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
                self.log_msg("X-Ray source warming up...")
            case "STS 2":
                self.xrs.xon()
                self.log_msg("X-Ray source turned ON.")
                time.sleep(0.5)  # Small delay to allow status update
            case _:
                pass

    def xoff(self):
        if not self.xrs:
            return
        self.xrs.xoff()
        self.log_msg("X-Ray source turned OFF.")

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
    # =============================================================================================
    #   Tab 1: X-ray source
    # =============================================================================================
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
        self.combo_focus.grid(row=0, column=1, padx=5)

        # --- XRS status indicators ---
        frame_ind = ttk.Frame(f)
        frame_ind.grid(row=4, column=0, pady=10)
        self.xrs_indicators = StatusIndicators(
            parent_frame=frame_ind,
            flags_dict=self.xrs_indicator_flags,
            columns=3,
            tick=self.master_tick,
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
        act_field = tk.Label(lf, text="0", bg="black", fg="red", width=6, font=("Arial", 14), anchor="e")
        act_field.grid(row=0, column=1)
        tk.Label(lf, text=unit).grid(row=0, column=2, sticky="w")

        if unit == "kV":
            limit = 130
        else:
            limit = 300

        tk.Label(lf, text="Set", fg="blue").grid(row=1, column=0, sticky="nsew", pady=(0,10))
        set_field = tk.Spinbox(lf, from_=0, to=limit, increment=1, font=("Arial", 16), justify="right", width=7)
        set_field.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        # tk.Entry(lf, width=6, font=("Arial", 14), justify="right").grid(row=1, column=1)
        # tk.Label(lf, text=unit).grid(row=1, column=2, sticky="w")
        return act_field, set_field

    # =============================================================================================
    #   Pestaña 2: Motor Control
    # =============================================================================================
    def build_motor_tab(self):
        f = self.tab_motor
        f.columnconfigure(0, weight=1)

        # Current position
        pos_frame = ttk.Frame(f)
        pos_frame.grid(row=1, column=0, pady=10)
        ttk.Label(pos_frame, text="Position (°):", foreground="blue").grid(row=0, column=0)
        self.position_indicator = tk.Label(pos_frame, text="0.00", bg="black", fg="red", width=10, font=("Arial", 14), anchor="e")
        self.position_indicator.grid(row=0, column=1, padx=5)

        # Motion arrows
        move_frame = ttk.Frame(f)
        move_frame.grid(row=2, column=0, pady=5)
        self.btn_bk_step = tk.Button(move_frame, text="◀", width=4)
        self.btn_bk_step.grid(row=0, column=0, padx=5)
        self.btn_fw_step = tk.Button(move_frame, text="▶", width=4)
        self.btn_fw_step.grid(row=0, column=1, padx=5)

        # STEP y GO TO
        config_frame = ttk.Frame(f)
        config_frame.grid(row=3, column=0, pady=10)
        ttk.Label(config_frame, text="STEP (°):").grid(row=0, column=0)
        self.motor_step_entry = ttk.Entry(config_frame, width=8)
        self.motor_step_entry.grid(row=0, column=1, padx=5)
        ttk.Label(config_frame, text="GO TO (°):").grid(row=1, column=0)
        self.motor_goto_entry = ttk.Entry(config_frame, width=8)
        self.motor_goto_entry.grid(row=1, column=1, padx=5)
        self.btn_motor_go = ttk.Button(config_frame, text="GO")
        self.btn_motor_go.grid(row=1, column=2, padx=5)

        # ---- Motor indicators ----
        ind_frame = ttk.Frame(f)
        ind_frame.grid(row=4, column=0, pady=10)
        self.motor_indicators = StatusIndicators(
            parent_frame=ind_frame,
            flags_dict=self.motor_indicator_flags,
            columns=3,
            tick=self.master_tick,
        )
        

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
        ttk.Button(motor_port_frame, text="Connect", command=self.connect_motor).grid(row=1, column=2, padx=5, sticky="w")

    # ============================================================
    #   Pestaña 3: Cámara y Adquisición
    # ============================================================
    def build_camera_tab(self):
        f = self.tab_camera
        f.columnconfigure(0, weight=1)

        # Camera config
        #TODO: complete this with the appropriate gixpy modules
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

        # Cam buttons
        btn_frame = ttk.Frame(cam_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=5)
        self.btn_cam_init = ttk.Button(btn_frame, text="Init Camera").grid(row=0, column=0, padx=5)
        self.btn_start_live = ttk.Button(btn_frame, text="Start Live").grid(row=0, column=1, padx=5)
        self.btn_stop_live = ttk.Button(btn_frame, text="Stop Live").grid(row=0, column=2, padx=5)

        # Acquisition config
        acq_frame = ttk.LabelFrame(f, text="Acquisition Settings")
        acq_frame.grid(row=2, column=0, pady=5, padx=5, sticky="ew")

        # Create entries dynamically. Uses class ParamsForm defined in .widgets
        self.acq_form = ParamsForm(acq_frame, AcquisitionParams)
        # Adjust entry labels
        self.acq_form.labels['step_deg'].config(text="Step (°) ")
        self.acq_form.labels['num_revs'].config(text="# Revs ")
        self.acq_form.labels['imgs_per_step'].config(text="Images / Step ")
        self.acq_form.labels['start_pos_deg'].config(text="Start Pos (°) ")
        self.acq_form.labels['base_folder'].config(text="Base Folder ")
        self.acq_form.entries['base_folder'].config(width=30)
        self.btn_browse_folder = ttk.Button(acq_frame, text="Browse...")
        self.btn_browse_folder.grid(row=4, column=2, padx=5)
        # Start / stop acquisition buttons
        self.btn_start_aqcisition = ttk.Button(acq_frame, text="Start Acquisition", style="Accent.TButton")
        self.btn_start_aqcisition.grid(row=5, column=1, pady=10)
        self.btn_stop_acquisition = ttk.Button(acq_frame, text="Stop Acquisition", style="Accent.TButton")
        self.btn_stop_acquisition.grid(row=5, column=2, pady=10)

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



if __name__ == "__main__":
    app = TomographyGUI()
    app.mainloop()