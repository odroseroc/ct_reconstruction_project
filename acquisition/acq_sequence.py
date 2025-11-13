import os
import sys
import gxipy as gx
import time
from dataclasses import dataclass
from pathlib import Path

from recon import AcquisitionIndex
from core.log_utils import no_op
from xrsource import XRSController
from motor import MotorController

@dataclass
class AcquisitionParams:
    directory: str
    revolutions: float
    step: float
    imgs_per_step = 5

def acq_sequence(xrsource: XRSController, motor: MotorController, cam: , log_fn=no_op):
    base_dir = Path(acq.directory)
    raw_dir = base_dir / 'raw'
    log_fn(f'Creating acquisition directory {raw_dir}')
    raw_dir.mkdir(parents=True, exist_ok=True)
    meta_path = base_dir / 'metadata.txt'








