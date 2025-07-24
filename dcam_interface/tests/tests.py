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

# Please note: when values are not passed as reference, ctypes will 
# convert to native python types. Thus, the variable to which we assign
# the return of the function DcamGetLastError will be a Python int, not
# a ctype.c_uint32. The values passed as reference will still be ctypes
# variables.

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
    dcam.DcamSetExposureTime(100)
    # dcam.DcamSetTriggerPolarity(DCAM_TRIGPOL_NEGATIVE)

    dcam.DcamGetBitPerPixel(ct.byref(nBitSize))
    print(f'Bit per pixel: {nBitSize.value}')

    dcam.DcamGetImageSize(ct.byref(nWidth), ct.byref(nHeight))
    print(f'Image size: {nWidth.value} x {nHeight.value}')

    nImageSize = nWidth.value*nHeight.value

    pDataBuff = (ct.c_uint16 * nImageSize)() # Array of c_uint16, equivalente a WORD

    dcam.DcamCapture(pDataBuff, ct.sizeof(pDataBuff))
    iterations = 0
    print('Capturing image')
    sleep_time_sec = 10
    for i in range(0,sleep_time_sec,2):
        dcam.DcamWait(ct.byref(dwRetStatus),5)
        print(f'{WAITSTATUS_DICT[dwRetStatus.value]}')
        time.sleep(2)
    

    # while True:
    #     dcam.DcamWait(ct.byref(dwRetStatus),5)
    #     iterations += 1
    #     if dwRetStatus.value == DCAM_WAITSTATUS_COMPLETED or iterations > 1000:
    #         break
    #     else:
    #         dcam.DcamClose()
    #         dcam.DcamUninitialize()
    #         return

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


# ============================================================================
if __name__ == "__main__":
    print(f'Current working directory: {os.getcwd()}')
    # Initialization
    dcam.DcamInitialize()
    dcam.DcamOpen()
    dcam.DcamSetDriveMode(DCAM_CCDDRVMODE_OPERATION, 3000)

    dwErrCode = ct.c_uint32() # Variable to store error codes. Equivalent to Windows DOWRD

    # Check connection
    nState = ct.c_int()

    if not dcam.DcamGetDeviceState(ct.byref(nState)):
        dwErrCode = dcam.DcamGetLastError()

    DEVSTATE_DICT = { DCAM_DEVSTATE_NON: 'Non-connection, No device found',
                    DCAM_DEVSTATE_DEVICE: 'Non-connection, Device found',
                    DCAM_DEVSTATE_NODEVICE: 'Connection, No device found',
                    DCAM_DEVSTATE_CONNECT: 'Connection, Device found',
                    DCAM_DEVSTATE_BOOT: 'Connection, Device found (during boot)' }

    print(f'Device Status: {DEVSTATE_DICT[nState.value]}')
    print(f'Error Code: {dwErrCode}')

    # Get CCD drive mode
    nMode = ct.c_int()

    if not dcam.DcamGetDriveMode(ct.byref(nMode)):
        dwErrCode = dcam.DcamGetLastError()

    CCDMODE_DICT = {DCAM_CCDDRVMODE_IDLE: 'Idle',
                    DCAM_CCDDRVMODE_OPERATION: 'Operation',
                    DCAM_CCDDRVMODE_STANDBY: 'Standby'}

    print(f'CCD Drive Mode: {nMode.value}: {CCDMODE_DICT[nMode.value]}')
    print(f'Error Code: {dwErrCode}')

    # Get information
    CCDTYPE_DICT = {DCAM_CCD_TYPE0: '1508 x 1002 (1500 x 1000) S8981 S10810',
                    DCAM_CCD_TYPE1: '1708 x 1202 (1700 x 1200) S8985 S10811',
                    DCAM_CCD_TYPE2: ' 608 x  402 ( 600 x  400) S7368-01'}
    nType = ct.c_int()
    if not dcam.DcamGetCCDType(ct.byref(nType)):
        dwErrCode = dcam.DcamGetLastError()
    print(f'CCD sensor type: {nType.value}: {CCDTYPE_DICT[nType.value]}')

    # Dictionaries to translate constants
    WAITSTATUS_DICT = {DCAM_WAITSTATUS_UNCOMPLETED: 'Image acquisition is not complete.',
                    DCAM_WAITSTATUS_COMPLETED: 'Image acquisition is complete.'}
    capture_img()

    dcam.DcamStop()
    dcam.DcamClose()
    dcam.DcamUninitialize()
