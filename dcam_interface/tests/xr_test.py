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
    dcamlib_dll.DcamSetDriveMode(DCAM_CCDDRVMODE_STANDBY, 3000)
    dcamlib_dll.DcamSetGain(1)
    dcamlib_dll.DcamSetOffset(10)
    dcamlib_dll.DcamSetBinning(DCAM_BINNING_1X1)
    dcamlib_dll.DcamSetCCDType(DCAM_CCD_TYPE0)
    dcamlib_dll.DcamSetTriggerMode(DCAM_TRIGMODE_INT)
    dcamlib_dll.DcamSetExposureTime(1000)
    # dcam.DcamSetTriggerPolarity(DCAM_TRIGPOL_NEGATIVE)

    dcamlib_dll.DcamGetBitPerPixel(ct.byref(nBitSize))
    print(f'Bit per pixel: {nBitSize.value}')

    dcamlib_dll.DcamGetImageSize(ct.byref(nWidth), ct.byref(nHeight))
    print(f'Image size: {nWidth.value} x {nHeight.value}')

    nImageSize = nWidth.value*nHeight.value

    pDataBuff = (ct.c_uint16 * nImageSize)() # Array of c_uint16, equivalente a WORD

    # X-ray source initialization
    xrs_command("XON")
    time.sleep(2) # Allow time for the x-ray source to stabilize
    response = xrs_command("SAR")
    print("x-ray sorce status values: ", response)

    start_time = time.time()
    dcamlib_dll.DcamCapture(pDataBuff, ct.sizeof(pDataBuff))
    time.sleep(0.96)
    end_time = time.time()
    xrs_command("XOF")
    iterations = 0
    print('Capturing image')
    sleep_time_sec = 10
    for i in range(0,sleep_time_sec,2):
        dcamlib_dll.DcamWait(ct.byref(dwRetStatus),5)
        print(f'{WAITSTATUS_DICT[dwRetStatus.value]}')
        time.sleep(2)
    
    print(f'Time to execute capture: {end_time - start_time} seconds')
    print(f'Ended with status: {dwRetStatus.value}')

    im_array = np.ctypeslib.as_array(pDataBuff) 
    im_array = np.reshape(im_array,(nHeight.value,nWidth.value))
    print(im_array)

    pFileName = ct.c_char_p(rb".\dcam_interface\tests\Sample.tiff")
    dcamimg_dll.DcamImgTiffSave(pFileName,pDataBuff,nWidth,nHeight,16,nBitSize)
    print(f'Saved image to {pFileName.value.decode()}')

    plt.imshow(im_array, cmap='grey')
    plt.show()

    pDataBuff = None

    return

if __name__ == "__main__":

    dcamlib_dll.DcamInitialize()
    dcamlib_dll.DcamOpen()
    dcamlib_dll.DcamSetDriveMode(DCAM_CCDDRVMODE_OPERATION, 3000)

    xrs_command("AST 5")

    capture_img()

    dcamlib_dll.DcamStop()
    dcamlib_dll.DcamClose()
    dcamlib_dll.DcamUninitialize()
    ser.close()