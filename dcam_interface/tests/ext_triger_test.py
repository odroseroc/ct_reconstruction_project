import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import ctypes as ct
import numpy as np
import time
import matplotlib.pyplot as plt
from dcam_interface.dcamlib import *
from dcam_interface.dcamimg import *
from dcam_interface.constants import *
from dcam_interface.dcam_utils import check_status

@check_status
def dcamgetstate():
    nState = ct.c_int()
    dcam.DcamGetDeviceState(ct.byref(nState))
    return nState.value

dcam.DcamInitialize()
dcam.DcamOpen()
dcam.DcamSetDriveMode(DCAM_CCDDRVMODE_OPERATION, 3000)

print(dcamgetstate()) # check_status esta mal implementada si espero usarla como en este ejemplo. Deberia estar decorando a la funcion interna.

dcam.DcamStop()
dcam.DcamClose()
dcam.DcamUninitialize()