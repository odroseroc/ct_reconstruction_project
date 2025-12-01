import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from unittest import case

import numpy as np
import threading
import time
from PIL import Image, ImageTk
import tifffile as tff
from pathlib import Path

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from gui.widgets import StatusIndicators, ParamsForm
from core.log_utils import no_op
from acq import AcquisitionParams, Acquisition, AcquisitionIndex, AcquisitionStep
# Imports handled by lazy import in development phase
# from motor import MotorController
# from xrsource import XRSController

# ====== GUI for X-ray source, rotating stage and camera control ====== #
DEFAULT_DLLPATH = r'C:\Windows\Microsoft.NET\assembly\GAC_64\Newport.SMC100.CommandInterface\v4.0_2.0.0.3__d9d722840772240b\Newport.SMC100.CommandInterface.dll'
UPDATE_INTERVAL_MS = 200  # Interval to update status

class TomographyGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tomography Control Panel")
        self.geometry("1500x900")
        self.configure(bg="#e0e0e0")
        self.master_tick = [0] # Global tick for blinking indicators. Must be a mutable type to be parsed by reference.

        # --- General layout ---
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
        self.xrs_warmup_started = False
        # --- Motor ---
        self.motor_indicator_flags = {
            'REFERENCED': False, # True if motor is referenced
            'READY': False, # True if motor is ready for motion
            'MOVING': False, # True if motor is NOT moving
            }
        # ---- Camera ----
        self.streaming = False
        # ---- Acquisition ----
        self.acquisition_running = False
        self.acq_no_xrs_counter = 0
        
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
        self.init_camera()

        self.after(UPDATE_INTERVAL_MS, self.update_status_loop)
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
                if self.xrs_warmup_started:
                    self.log_msg("X-Ray source warmup complete.")
                    self.xrs_warmup_started = False
                    self.xrs.set_emission_mode(mode=3) # Set to continuous mode after warmup
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
            self.btn_xon.config(state=tk.DISABLED)
            self.xrs_emitting_indicator.config(text="X-Ray ON", bg="red")
            self.blink_emitting_indicator()
            self.xrs_indicators.blink("X_RAY")
        else:
            self.btn_xon.config(state=tk.NORMAL)
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
        
        if not (self.xrs_indicator_flags["INTERLOCK"] and self.xrs_indicator_flags["ERROR"] and self.xrs_indicator_flags["OVER"]):
            self.btn_xon.config(state=tk.DISABLED)
            self.btn_xoff.config(state=tk.DISABLED)
        else:
            self.btn_xon.config(state=tk.NORMAL)
            self.btn_xoff.config(state=tk.NORMAL)

        if self.acquisition_running:
            self.volt_entry.config(state=tk.DISABLED)
            self.curr_entry.config(state=tk.DISABLED)
            # if not self.xrs_emitting_flag and self.acq_no_xrs_counter == 0:
            #     tk.messagebox.showwarning("Acquisition sequence warning", "X-Ray source has been turned off while running an acquisition.")
            #     self.acq_no_xrs_counter = (self.acq_no_xrs_counter + 1) % 80 # Show warning every 80 ticks
            # else:
            #     self.acq_no_xrs_counter = 0
        else:
            self.volt_entry.config(state=tk.NORMAL)
            self.curr_entry.config(state=tk.NORMAL)

    # ---------- Motor ----------
    def poll_motor_status(self):
        positioner_status = self.motor.get_positioner_status()
        self.motor_indicator_flags['REFERENCED'] = not(positioner_status.startswith('0') or positioner_status in ['0F', '10', '11'])
        self.motor_indicator_flags['READY'] = positioner_status in ['32', '33', '34', '35'] and not self.acquisition_running
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
        if not self.motor_indicator_flags["READY"]:
            self.btn_bk_step.config(state=tk.DISABLED)
            self.btn_fw_step.config(state=tk.DISABLED)
            self.btn_motor_go.config(state=tk.DISABLED)
        else:
            self.btn_bk_step.config(state=tk.NORMAL)
            self.btn_fw_step.config(state=tk.NORMAL)
            self.btn_motor_go.config(state=tk.NORMAL)
        if not self.motor_indicator_flags["MOVING"]:
            self.motor_indicators.blink("MOVING")
            self.btn_bk_step.config(state=tk.DISABLED)
            self.btn_fw_step.config(state=tk.DISABLED)
            self.btn_motor_go.config(state=tk.DISABLED)
        else:
            self.motor_indicators.stop_blink("MOVING")

        if self.acquisition_running:
            self.btn_bk_step.config(state=tk.DISABLED)
            self.btn_fw_step.config(state=tk.DISABLED)
            self.btn_motor_go.config(state=tk.DISABLED)
        # Update position indicator
        try:
            position = self.motor.get_theoretical_position()
        except Exception:
            return
        self.position_indicator.config(text=f"{position:.2f}")


    def update_camera_status(self):
        # ---- NO CAM FOUND ----
        if not self.cam:
            self.btn_cam_apply.config(state=tk.DISABLED)
            self.btn_start_live.config(state=tk.DISABLED)
            self.btn_stop_live.config(state=tk.DISABLED)
            self.btn_cam_close.config(state=tk.DISABLED)
            return
        # ---- CAM FOUND ----
        if not self.cam.stream_on():
            self.btn_cam_apply.config(state=tk.NORMAL)
        else:
            self.btn_cam_apply.config(state=tk.DISABLED)
        self.btn_cam_close.config(state=tk.NORMAL)
        if self.streaming:
            self.btn_start_live.config(state=tk.DISABLED)
            self.btn_stop_live.config(state=tk.NORMAL)
        else:
            self.btn_start_live.config(state=tk.NORMAL)
            self.btn_stop_live.config(state=tk.DISABLED)
            self.live_label.config(image='', text="No Live Preview", fg="white", font=("Arial", 20))

    # ==============================================================
    #    Loger
    # ==============================================================
    def log_msg(self, msg):
        self.log.config(state='normal')
        self.log.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {msg}\n")
        self.log.see(tk.END)
        self.log.config(state='disabled')

    def thread_safe_log(self, msg):
        "Allows the acquisition sequence to write logs in the GUI from a separate thread."
        self.after(0, self.log_msg, msg)

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
                self.log_msg(f"XRS Status = {self.xrs.get_status()}")
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


    def init_camera(self):
        try:
            if not self.cam_devmgr:
                import gxipy as gx
                self.cam_devmgr = gx.DeviceManager()
                num, _ =  self.cam_devmgr.update_device_list()
                if num == 0: raise RuntimeError("No camera found.")
        except Exception as e:
                self.cam_devmgr = None
                return e
        finally:
            if self.cam_devmgr:
                self.cam = self.cam_devmgr.open_device_by_index(1)
                self.cam.RemoveParameterLimit.set(1)
                self.cam.TriggerMode.set(gx.GxSwitchEntry.OFF)
                self.cam.PixelFormat.set(gx.GxPixelFormatEntry.MONO12)
                self.apply_cam_settings()
                self.cam.stream_on()
                self.log_msg(f"Camera initialized")

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
                self.xrs_warmup_started = True
            case "STS 2":
                self.xrs.xon()
                self.log_msg("X-Ray source turned ON.")
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
            
    def move_motor_step(self, direction: int):
        ''' Move motor one step in given direction (+1 or -1) '''
        if not self.motor:
            return
        current_pos = self.motor.get_theoretical_position()
        step_size = float(self.motor_step_entry.get())
        step_size = self.wrap_inclusive_0_180(step_size)
        self.motor_step_entry.delete(0, tk.END)
        self.motor_step_entry.insert(0, str(step_size))
        dist = direction * step_size
        target_pos = current_pos + dist
        self.motor.move_absolute(target_pos)

    def goto_motor(self):
        ''' Move motor to given absolute position '''
        if not self.motor:
            return
        target_pos = float(self.motor_goto_entry.get())
        target_pos = self.wrap_minus180_180_inclusive(target_pos)
        self.motor_goto_entry.delete(0, tk.END)
        self.motor_goto_entry.insert(0, str(target_pos))
        self.motor.move_absolute(target_pos)
    
    # Function to wrap values to the default limits of the motor
    @staticmethod
    def wrap_minus180_180_inclusive(x):
        ''' Wrap angle x to the range (-180, 180]. '''
        v = ((x + 180) % 360) - 180
        if v == -180:
            return 180
        return v
    
    @staticmethod
    def wrap_inclusive_0_180(x):
        value = abs(x) % 180
        # If value is 0 but x was a multiple of 180, return 180 instead of 0.
        if value == 0 and x != 0:
            return 180
        return value

    # ---- Camera ----

    def apply_cam_settings(self):
        exposure = float(self.exposure_entry.get())
        gain = float(self.gain_entry.get())
        self.cam.ExposureTime.set(int(exposure*1e6))
        self.cam.Gain.set(gain)
        self.log_msg(f"Aplied camera settings: {exposure=}, {gain=}")

    def connect_cam(self):
        e = self.init_camera()
        if e:
            tk.messagebox.showerror(title="Camera init error",
                                    message=f"Failed to initialize camera:\n {e}")

    def disable_cam(self):
        self.stop_stream()
        try:
            self.cam.stream_off()
            self.cam.close_device()
        except: pass
        self.cam = None
        self.log_msg("Camera disabled.")

    # ==============================================================
    #    Acquisition
    # ==============================================================
    def run_acquisition(self):
        '''Perform acquisition sequence with the specified parameters.'''
        if not (self.xrs and self.motor and self.cam):
            tk.messagebox.showwarning(title="Not ready", message="Initialize all devices before starting acquisition.")
            return
        self.acquisition_running = True
        try:
            acq_params = self.acq_form.get_params()
            # self.log_msg("[run_acquisition] Starting acquisition with parameters:\n" + str(acq_params))
            self.acq = Acquisition(
                xrs = self.xrs,
                motor = self.motor,
                cam = self.cam,
                params = acq_params,
                log_fn = self.thread_safe_log,
                on_step_completed = self.thread_safe_update_preview,
            )

            # Launch acquisition in a thread
            self.acq_thread = threading.Thread(
                target = self._run_acquisition_thread,
                daemon = True
            )
            self.acq_thread.start()

            self.log_msg("---- Acquisition thread started. ----")
        except Exception as e:
            self.xoff()
            self.acquisition_running = False
            tk.messagebox.showerror(title="Acquisition error", message=f"Failed to start acquisition:\n {type(e).__name__}: {e}")

    def _run_acquisition_thread(self):
        try:
            result = self.acq.run()
        except Exception as e:
            result = e
        finally:
            self.after(0, lambda: self._finish_acquisition(result))

    def _finish_acquisition(self, result):
        self.xoff()
        self.acquisition_running = False
        self.acq = None

        if isinstance(result, Exception):
            self.log_msg(f"Acquisition failed. {type(result).__name__}: {result}")
        else:
            self.log_msg(f"---- Acquisition complete. ----")
            self.log_msg(f"Raw images saved at {Path(result.metadata_file).parent.resolve()}")

    # ==============================================================
    #    Preview
    # ==============================================================

    def update_preview(self, img):
        try:
            if img.dtype != 'uint16': img = img.astype('uint16')
            self.snap_im.set_data(img)
            self.snap_im.set_clim(0, 4096)
            self.canvas.draw_idle()
        except Exception as e:
            self.log_msg(f"Snapshot preview failed: {e}")

    def thread_safe_update_preview(self, img):
        self.after(0, self.update_preview, img)

    def start_stream(self):
        if not self.cam or self.streaming:
            return
        self.cam.stream_on()
        self.streaming = True
        threading.Thread(target=self._live_stream, daemon=True).start()
    
    def _live_stream(self):
        while self.streaming:
            try:
                img = self.cam.data_stream[0].get_image(timeout=10000)
                arr = img.get_numpy_array()
                if arr.dtype=='uint16': arr=(arr>>4).astype('uint8')
                elif arr.dtype!='uint8': arr=arr.astype('uint8')
                pil_img = Image.fromarray(arr, 'L').resize((540,405), Image.NEAREST)
                # pil_img.thumbnail((540,405))
                if not hasattr(self, 'live_image'):
                    self.live_image = ImageTk.PhotoImage(pil_img)
                    self.live_label.after(0, 
                                          lambda: self.live_label.config(image=self.live_image,))
                else:
                    self.live_image.paste(pil_img)
                    self.live_label.after_idle(self.live_label.update)
            except Exception as e:
                self.log_msg(f"Live stream failed. {type(e).__name__}: {e}")
                break
            
    def stop_stream(self):
        self.streaming = False
        if hasattr(self, 'live_image'):
            del self.live_image
        self.live_label.config(image='')  # Limpia la UI
        self.cam.stream_off()

    # ==============================================================
    #    Browsers
    # ==============================================================
    def browse_base_folder(self):
        base_path = filedialog.askdirectory(title="Select base folder for acquisition")
        if base_path:
            self.acq_form.entries['base_folder'].delete(0, tk.END)
            self.acq_form.entries['base_folder'].insert(0, base_path)

    def browse_dll_path(self):
        dll_path = filedialog.askopenfilename(
            title="Select motor DLL file",
            filetypes=[("DLL files", "*.dll"), ("All files", "*.*")]
        )
        if dll_path:
            self.motor_dll_entry.delete(0, tk.END)
            self.motor_dll_entry.insert(0, dll_path)



    # ---- Close ----
    def on_close(self):
        if self.xrs:
            self.xrs.close()
        if self.motor:
            self.motor.close()
        if self.cam:
            self.disable_cam()
        self.destroy()


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
    #   Tab 2: Motor Control
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
        self.btn_bk_step = tk.Button(move_frame, text="◀", width=4, command=lambda: self.move_motor_step(direction=-1))
        self.btn_bk_step.grid(row=0, column=0, padx=5)
        self.btn_fw_step = tk.Button(move_frame, text="▶", width=4, command=lambda: self.move_motor_step(direction=1))
        self.btn_fw_step.grid(row=0, column=1, padx=5)

        # STEP y GO TO
        config_frame = ttk.Frame(f)
        config_frame.grid(row=3, column=0, pady=10)
        ttk.Label(config_frame, text="STEP (°):").grid(row=0, column=0)
        self.motor_step_entry = ttk.Entry(config_frame, width=8)
        self.motor_step_entry.insert(0, "1.0")
        self.motor_step_entry.grid(row=0, column=1, padx=5)
        ttk.Label(config_frame, text="GO TO (°):").grid(row=1, column=0)
        self.motor_goto_entry = ttk.Entry(config_frame, width=8)
        self.motor_goto_entry.insert(0, "0.0")
        self.motor_goto_entry.grid(row=1, column=1, padx=5)
        self.btn_motor_go = ttk.Button(config_frame, text="GO", command=self.goto_motor)
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
        self.btn_motor_dll = ttk.Button(motor_port_frame, text="Browse...", command=self.browse_dll_path).grid(row=0, column=3, padx=5)
        # Port field
        ttk.Label(motor_port_frame, text="Motor Port:").grid(row=1, column=0)
        self.motor_port_entry = ttk.Entry(motor_port_frame, width=10)
        self.motor_port_entry.insert(0, "COM6")
        self.motor_port_entry.grid(row=1, column=1, padx=5,sticky="w")
        ttk.Button(motor_port_frame, text="Connect", command=self.connect_motor).grid(row=1, column=2, padx=5, sticky="w")

    # ============================================================
    #   Tab 3: Camera & Acquisition
    # ============================================================
    def build_camera_tab(self):
        f = self.tab_camera
        f.columnconfigure(0, weight=1)

        # ---- Camera config ----
        cam_frame = ttk.LabelFrame(f, text="Camera Settings")
        cam_frame.grid(row=1, column=0, pady=5, padx=5, sticky="ew")
        # Exposure and gain
        ttk.Label(cam_frame, text="Exposure (s)").grid(row=0, column=0, sticky="e")
        self.exposure_entry = ttk.Entry(cam_frame, width=10, justify="right")
        self.exposure_entry.insert(0, 0.5)
        self.exposure_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        ttk.Label(cam_frame, text="Gain").grid(row=1, column=0, sticky="e")
        self.gain_entry = tk.Spinbox(cam_frame, from_=0, to=27, increment=1, justify="right", width=10)
        self.gain_entry.delete(0, tk.END)
        self.gain_entry.insert(0, '27')
        self.gain_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        # Cam buttons
        btn_frame = ttk.Frame(cam_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=5)
        self.btn_cam_init = ttk.Button(btn_frame, text="Init Camera", command=self.connect_cam)
        self.btn_cam_init.grid(row=0, column=0, padx=5)
        self.btn_cam_apply = ttk.Button(btn_frame, text="Apply settings", command=self.apply_cam_settings)
        self.btn_cam_apply.grid(row=0, column=1, padx=5)
        self.btn_start_live = ttk.Button(btn_frame, text="Start Live", command=self.start_stream)
        self.btn_start_live.grid(row=0, column=2, padx=5)
        self.btn_stop_live = ttk.Button(btn_frame, text="Stop Live", command=self.stop_stream)
        self.btn_stop_live.grid(row=0, column=3, padx=5)
        self.btn_cam_close = ttk.Button(btn_frame, text="Disable Camera", command=self.disable_cam)
        self.btn_cam_close.grid(row=0, column=4, padx=5)

        # ---- Acquisition config ----
        acq_frame = ttk.LabelFrame(f, text="Acquisition Settings")
        acq_frame.grid(row=2, column=0, pady=5, padx=5, sticky="ew")

        # Create entries dynamically. Uses class ParamsForm defined in .widgets
        self.acq_form = ParamsForm(acq_frame, AcquisitionParams)
        # Adjust entry labels
        self.acq_form.labels['name'].config(text="Name ")
        self.acq_form.labels['step_deg'].config(text="Step (°) ")
        self.acq_form.labels['num_revs'].config(text="# Revs ")
        self.acq_form.labels['imgs_per_step'].config(text="Images / Step ")
        self.acq_form.labels['start_pos_deg'].config(text="Start Pos (°) ")
        self.acq_form.labels['base_folder'].config(text="Base Folder ")
        self.acq_form.entries['base_folder'].config(width=50)
        self.btn_browse_folder = ttk.Button(acq_frame, text="Browse...", command=self.browse_base_folder)
        self.btn_browse_folder.grid(row=5, column=2, padx=5)
        # Start / stop acquisition buttons
        self.btn_start_aqcisition = ttk.Button(acq_frame, text="Start Acquisition", style="Accent.TButton", command=self.run_acquisition)
        self.btn_start_aqcisition.grid(row=6, column=1, pady=10)
        self.btn_stop_acquisition = ttk.Button(acq_frame, text="Stop Acquisition", style="Accent.TButton")
        self.btn_stop_acquisition.grid(row=6, column=2, pady=10)

    # ============================================================
    #   Right panel: Live, Snapshot
    # ============================================================
    def build_vis_panel(self, parent):
        live_frame = ttk.LabelFrame(parent, text="Live Preview")
        live_frame.grid(row=0, column=0, sticky="nsew", pady=5)
        self.live_label = tk.Label(live_frame, bg="black")
        self.live_label.config(text="No Live Preview", fg="white", font=("Arial", 20))
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


if __name__ == "__main__":
    app = TomographyGUI()
    app.mainloop()