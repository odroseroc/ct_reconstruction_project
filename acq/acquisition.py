from __future__ import annotations
import datetime

import time
import numpy as np
import tifffile as tff
import os

from dataclasses import dataclass
from pathlib import Path
from core.log_utils import no_op
from .acqindex import AcquisitionStep, AcquisitionIndex

DEGS_1REV = 360

@dataclass
class AcquisitionParams:
    name: str = "new_acquisition"
    step_deg: float = 1
    num_revs: int = 1
    imgs_per_step: int = 5
    start_pos_deg: float = -180
    base_folder: str = "C:\\Users\\Desktop\\Acquisition"

class Acquisition:
    def __init__(
            self,
            xrs: "XRSController" = None,
            motor: "MotorController" = None,
            cam: "gxipy.Device" = None,
            params: AcquisitionParams = None,
            log_fn = no_op,
            on_step_completed = None,
    ):
        self.xrs = xrs
        self.motor = motor
        self.cam = cam
        self.params = params
        self.logger = log_fn
        self.on_step_completed = on_step_completed

        self.name = self.params.name
        self.step_deg = float(self.params.step_deg)
        self.num_revs = int(self.params.num_revs)
        self.imgs_per_step = int(self.params.imgs_per_step)
        self.start_pos_deg = float(self.params.start_pos_deg)
        self.base_folder = Path(self.params.base_folder)
        self.raw_folder = self.base_folder / "raw"
        self.meta_path = self.raw_folder / "meta.txt"

    def write_metadata_header(self, metafile_path, header_params):
        with open(metafile_path, "w") as metafile:
            metafile.write('='*50+"\n")
            metafile.write(f"Acquisition {self.name}\nDate: {datetime.datetime.now()}\n")
            metafile.write('='*50+"\n")
            metafile.write("\n---------- X-ray source parameters: ----------\n")
            metafile.write(f'{"Tube Voltage": <12}    {"Tube current": <12}    {"Focal spot mode": <15} \n')
            metafile.write('-'*49+"\n")
            metafile.write(f'{str(header_params["voltage"]) + "kV": >12}    {str(header_params["current"]) + "µA": >12}    {str(header_params["focus"]): ^15} \n')
            metafile.write("\n---------- Camera parameters: ----------\n")
            metafile.write(f'{"Exposure time": <13}     {"Gain": <8}\n')
            metafile.write('-' * 25 + "\n")
            metafile.write(
                f'{str(header_params["exposure_time"]) + " s": >13}     {str(header_params["gain"]) + " dB": >8} \n')
            metafile.write("\n---------- Acquisition parameters: ----------\n")
            metafile.write(f"Start position: {self.start_pos_deg: >7.2f} ° \n")
            metafile.write(f"Step:           {self.step_deg: >7.2f} º\n")
            metafile.write("\n=============================================\n")
            metafile.write("#, degrees, path\n")

    def append_step_metadata(self, metafile_path, idx, acq_step):
        with open(metafile_path, "a") as metafile:
            metafile.write(f"{idx}, {acq_step.angle}, {acq_step.filepath}\n")

    def run(self = no_op):
        self.logger("[Acquisition] Starting acquisition...")

        try:
            os.makedirs(self.raw_folder, exist_ok=True)
            acq_steps = []
            voltage = self.xrs.get_preset_voltage()
            time.sleep(0.2)
            current = self.xrs.get_preset_current()
            time.sleep(0.2)
            focus = self.xrs.get_focal_spot_mode()
            focus_modes = ["small", "medium", "large"]
            focus = focus_modes[focus]
            self.motor.move_absolute(self.start_pos_deg, log_fn=self.logger)
            self.motor.wait(log_fn=self.logger)
            start_pos = self.motor.get_theoretical_position()
            self.logger(f"[Acquisition] Motor position: {start_pos} °")
            exposure_time = self.cam.ExposureTime.get()
            gain = self.cam.Gain.get()
            self.xrs.xon()
            self.logger("[Acquisition] X-ray source turned ON.")
            time.sleep(3)  # wait for x-ray source to stabilize
            self.logger(f"[Acquisition] X-ray voltage: {voltage} kV, current: {current} µA.")
            meta_header_params = {
                "voltage": voltage,
                "current": current,
                "focus": focus,
                "exposure_time": exposure_time/1e6,
                "gain": gain,
            }
            self.write_metadata_header(self.meta_path, meta_header_params)
            steps_per_rev = round(DEGS_1REV / self.step_deg)
            current_pos = self.start_pos_deg
            total_steps = self.num_revs * steps_per_rev
            self.logger("[Acquisition] Starting loop...")
            for rev in range(self.num_revs):
                for step in range(steps_per_rev):
                    step_nr = (rev * steps_per_rev) + step
                    current_pos = (rev * DEGS_1REV) + self.motor.get_theoretical_position()
                    self.logger("--------------------------------------------")
                    self.logger(f"[Acquisition] Step {step_nr} of {total_steps} at position {current_pos} °.")
                    # Acquisition of image mean from self.imgs_per_step frames
                    self.logger(f"[Acquisition] Capturing {self.imgs_per_step} images...")
                    img_stack = [self.cam.data_stream[0].get_image(timeout=20000).get_numpy_array() for _ in range(self.imgs_per_step)]
                    img_stack = np.stack(img_stack, axis=0)
                    mean_img = np.mean(img_stack, axis=0).astype(img_stack.dtype)
                    img_fname = self.raw_folder / f"Im_raw{step:03d}.tif"
                    tff.imwrite(img_fname, mean_img)
                    acq_step = AcquisitionStep(angle=current_pos, filepath=img_fname)
                    acq_steps.append(acq_step)
                    self.append_step_metadata(
                        metafile_path=self.meta_path,
                        idx= step_nr,
                        acq_step=acq_step
                    )
                    self.logger(f"[Acquisition] Saved image at {img_fname}")
                    # If implemented, send callback to GUI to update visualization
                    if self.on_step_completed:
                        try:
                            self.on_step_completed(mean_img)
                        except:
                            pass
                    if step_nr < total_steps:
                        self.motor.move_relative(self.step_deg)
                        self.motor.wait()
                self.xrs.xoff()
                self.logger("[Acquisition] Acquisition complete. Returning motor to initial position...")
                self.motor.move_absolute(self.start_pos_deg)
                self.motor.wait()
                self.logger(f"[Acquisition] Acquisition finished.")
                return AcquisitionIndex.from_list(acq_steps, self.meta_path, self.base_folder)

        except Exception as e:
            self.xrs.xoff()
            self.logger(f"[Acquisition] ERROR: {type(e).__name__}: {e}")
            raise e








