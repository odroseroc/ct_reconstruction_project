import os
import sys
import gxipy as gx
import time
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AcquisitionParams:
    step_deg: float
    num_revs: int
    imgs_per_step: int
    start_pos_deg: float
    base_folder: str

def acq_sequence(xrsource: XRSController, motor: MotorController, cam, log_fn=no_op):
    base_dir = Path(acq.directory)
    raw_dir = base_dir / 'raw'
    log_fn(f'Creating acquisition directory {raw_dir}')
    raw_dir.mkdir(parents=True, exist_ok=True)
    meta_path = base_dir / 'metadata.txt'








