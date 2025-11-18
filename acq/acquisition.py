from __future__ import annotations
import datetime

import os
import sys
import gxipy as gx
import time

from dataclasses import dataclass
from pathlib import Path
from core.log_utils import no_op
from acq import AcquisitionStep

DEGS_1REV = 360

@dataclass
class AcquisitionParams:
    step_deg: float = 1
    num_revs: int = 1
    imgs_per_step: int = 5
    start_pos_deg: float = 0
    base_folder: str = "C:\\Users\\\\Desktop\\Acquisition"

class Acquisition:
    def __init__(
            self,
            name: Optional[str] = None,
            xrs: "XRSController",
            motor: "MotorController",
            camera: "gxipy.Device",
            params: AcquisitionParams,
            log_fn = no_op,
    ):
        self.name = name
        self.xrs = xrs
        self.motor = motor
        self.camera = camera
        self.params = params
        self.logger = log_fn

    def write_metadata_header(self, metafile_path, metafile_params):
        with open(metafile_path, "w") as metafile:
            metafile.write('='*50+"\n")
            metafile.write(f"Acquisition {self.name}\nDate: {datetime.datetime.now()}\n")
            metafile.write('='*50+"\n")
            metafile.write("---------- X-ray source parameters: ----------\n")
            metafile.write(f'{"Tube Voltage": <12}   {"Tube current": <12}   {"Focal spot mode": <15} \n')
            metafile.write('-'*47+"\n")
            metafile.write(f'{str(metafile_params["voltage"]) + "kV": >12} {str(metafile_params["current"]) + "µA": >12} {str(metafile_params["focus"]): ^15} \n')
            metafile.write("---------- Camera parameters: ----------\n")
            metafile.write(f'{"Exposure time": <13}   {"Gain": <5}\n')
            metafile.write('\n')
            metafile.write('-' * 21 + "\n")
            metafile.write(
                f'{str(metafile_params["exposure_time"]) + "s": >13}   {str(metafile_params["gain"]) + "dB": >12} \n')
            metafile.write('\n')
            metafile.write("---------- Acquisition parameters: ----------\n")
            metafile.write(f"Start position: {self.params.start_pos_deg: >7.2f} ° \n")
            metafile.write(f"Step:           {self.params.step_deg: >7.2f} º\n")
            metafile.write("=============================================")
            metafile.write("#, degrees, path\n")

    def append_step_metadata(self, metafile_path, idx, acq_step):
        with open(metafile_path, "a") as metafile:
            metafile.write(f"{idx}, {acq_step.angle}, {acq_step.filepath}\n")

    def run(self = no_op):
        self.logger("Starting acquisition...")
        base_folder = Path(self.params.base_folder)
        raw_folder = base_folder / "raw"
        raw_folder.mkdir(parents=True, exist_ok=True)
        meta_path = raw_folder / "meta.txt"
        try:
            voltage = self.xrs.get_preset_voltage()
            current = self.xrs.get_preset_current()
            focus = self.xrs.get_focal_spot_mode()
            focus_modes = ["small", "medium", "large"]
            focus = focus_modes[focus]
            self.motor.move_absolute(self.params.start_pos_deg, log_fn=self.logger)
            self.motor.wait(log_fn=self.logger)
            start_pos = self.motor.get_theoretical_position()
            self.logger(f"Motor position: {start_pos}")
            exposure_time = self.camera.ExposureTime.get()
            gain = self.camera.Gain.get()
            metafile_params = {
                "voltage": voltage,
                "current": current,
                "focus": focus,
                "exposure_time": exposure_time,
                "gain": gain,
            }
            self.write_metadata_header(meta_path, metafile_params)
            steps_per_rev = round(DEGS_1REV / self.params.step_deg, 3)
            current_deg = self.params.start_pos_deg
            for rev in range(self.params.num_revs):
                for step in range(steps_per_rev):
                    pass





        except Exception as e:
            self.logger("Failed to start acquisition: " + str(e))
            self.logger("Acquisition aborted.")
            return







# def acq_sequence(xrsource: XRSController, motor: MotorController, cam, log_fn=no_op):
#     base_dir = Path(acq.directory)
#     raw_dir = base_dir / 'raw'
#     log_fn(f'Creating acquisition directory {raw_dir}')
#     raw_dir.mkdir(parents=True, exist_ok=True)
#     meta_path = base_dir / 'metadata.txt'








