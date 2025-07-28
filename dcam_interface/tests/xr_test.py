import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import serial
import ctypes as ct
import numpy as np
import time
import matplotlib.pyplot as plt
from dcam_interface.dcamlib import *
from dcam_interface.dcamimg import *
from dcam_interface.constants import *
from xrsource.xrs_resources import ser, xrs_command

def capture_img():
    # Variables
    nWidth = ct.c_int()
    nHeight = ct.c_int()
    nBitSize = ct.c_int()
    dwRetStatus = ct.c_uint32(DCAM_WAITSTATUS_UNCOMPLETED)
    # pDataBuff = ct.POINTER()
    dcam.DcamSetDriveMode(DCAM_CCDDRVMODE_STANDBY, 3000)
    dcam.DcamSetGain(1)
    dcam.DcamSetOffset(10)
    dcam.DcamSetBinning(DCAM_BINNING_1X1)
    dcam.DcamSetCCDType(DCAM_CCD_TYPE0)
    dcam.DcamSetTriggerMode(DCAM_TRIGMODE_INT)
    dcam.DcamSetExposureTime(1000)
    # dcam.DcamSetTriggerPolarity(DCAM_TRIGPOL_NEGATIVE)

    dcam.DcamGetBitPerPixel(ct.byref(nBitSize))
    print(f'Bit per pixel: {nBitSize.value}')

    dcam.DcamGetImageSize(ct.byref(nWidth), ct.byref(nHeight))
    print(f'Image size: {nWidth.value} x {nHeight.value}')

    nImageSize = nWidth.value*nHeight.value

    pDataBuff = (ct.c_uint16 * nImageSize)() # Array of c_uint16, equivalente a WORD

    # X-ray source initialization
    xrs_command("XON")
    time.sleep(2) # Allow time for the x-ray source to stabilize
    response = xrs_command("SAR")
    print("x-ray sorce status values: ", response)

    start_time = time.time()
    dcam.DcamCapture(pDataBuff, ct.sizeof(pDataBuff))
    time.sleep(0.96)
    end_time = time.time()
    xrs_command("XOF")
    iterations = 0
    print('Capturing image')
    sleep_time_sec = 10
    for i in range(0,sleep_time_sec,2):
        dcam.DcamWait(ct.byref(dwRetStatus),5)
        print(f'{WAITSTATUS_DICT[dwRetStatus.value]}')
        time.sleep(2)
    
    print(f'Time to execute capture: {end_time - start_time} seconds')
    print(f'Ended with status: {dwRetStatus.value}')

    im_array = np.ctypeslib.as_array(pDataBuff) 
    im_array = np.reshape(im_array,(nHeight.value,nWidth.value))
    print(im_array)

    pFileName = ct.c_char_p(rb".\dcam_interface\tests\Sample.tiff")
    dcamimg.DcamImgTiffSave(pFileName,pDataBuff,nWidth,nHeight,16,nBitSize)
    print(f'Saved image to {pFileName.value.decode()}')

    plt.imshow(im_array, cmap='grey')
    plt.show()

    pDataBuff = None

    return

if __name__ == "__main__":

    dcam.DcamInitialize()
    dcam.DcamOpen()
    dcam.DcamSetDriveMode(DCAM_CCDDRVMODE_OPERATION, 3000)

    xrs_command("AST 5")

    capture_img()

    dcam.DcamStop()
    dcam.DcamClose()
    dcam.DcamUninitialize()
    ser.close()