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
    dcamlib_dll.DcamGetDeviceState(ct.byref(nState))
    return nState.value

dcamlib_dll.DcamInitialize()
dcamlib_dll.DcamOpen()
dcamlib_dll.DcamSetDriveMode(DCAM_CCDDRVMODE_OPERATION, 3000)

print(dcamgetstate()) # check_status esta mal implementada si espero usarla como en este ejemplo. Deberia estar decorando a la funcion interna.

dcamlib_dll.DcamStop()
dcamlib_dll.DcamClose()
dcamlib_dll.DcamUninitialize()