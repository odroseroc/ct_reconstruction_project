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

def capture_img(img_nr=1, exposure=1000, padding=0.96, gain=1, offset=10):
    dcam.DcamInitialize()
    dcam.DcamOpen()
    dcam.DcamSetDriveMode(DCAM_CCDDRVMODE_OPERATION, 3000)

    # Variables
    nWidth = ct.c_int()
    nHeight = ct.c_int()
    nBitSize = ct.c_int()
    dwRetStatus = ct.c_uint32(DCAM_WAITSTATUS_UNCOMPLETED)
    # pDataBuff = ct.POINTER()
    dcam.DcamSetDriveMode(DCAM_CCDDRVMODE_STANDBY, 3000)
    dcam.DcamSetGain(gain)
    dcam.DcamSetOffset(offset)
    dcam.DcamSetBinning(DCAM_BINNING_1X1)
    dcam.DcamSetCCDType(DCAM_CCD_TYPE0)
    dcam.DcamSetTriggerMode(DCAM_TRIGMODE_INT)
    dcam.DcamSetExposureTime(exposure)
    # dcam.DcamSetTriggerPolarity(DCAM_TRIGPOL_NEGATIVE) 

    dcam.DcamGetBitPerPixel(ct.byref(nBitSize))
    print(f'Bit per pixel: {nBitSize.value}')

    dcam.DcamGetImageSize(ct.byref(nWidth), ct.byref(nHeight))
    print(f'Image size: {nWidth.value} x {nHeight.value}')

    nImageSize = nWidth.value*nHeight.value

    pDataBuff = (ct.c_uint16 * nImageSize)() # Array of c_uint16, equivalente a WORD

    # X-ray source initialization
    xrs_command("XON")
    time.sleep(3) # Allow time for the x-ray source to stabilize
    response = xrs_command("SAR")
    print("x-ray sorce status values: ", response)

    print(f"Exposing image ({padding} s)... ")
    start_time = time.time()
    dcam.DcamCapture(pDataBuff, ct.sizeof(pDataBuff))
    capture_sent_time = time.time()
    time.sleep(padding)
    # xrs_command("XOF")
    end_time = time.time()
    print('Capturing image...')
    sleep_time_sec = 6
    for i in range(0,sleep_time_sec,2):
        dcam.DcamWait(ct.byref(dwRetStatus),5)
        print(f'{WAITSTATUS_DICT[dwRetStatus.value]}')
        time.sleep(2)
    
    dcam.DcamStop()
    
    print(f'Time to execute capture: {end_time - start_time} seconds')
    print(f'Ended with status: {dwRetStatus.value}')

    im_array = np.ctypeslib.as_array(pDataBuff) 
    im_array = np.reshape(im_array,(nHeight.value,nWidth.value))
    # print(im_array)

    filename_str=fr'.\dcam_interface\tests\test_xr\sample_{img_nr:03d}.tiff'
    pFileName = ct.c_char_p(filename_str.encode('utf-8'))
    dcamimg.DcamImgTiffSave(pFileName,pDataBuff,nWidth,nHeight,16,nBitSize)
    print(f'Saved image to {pFileName.value.decode()}')

    plt.imshow(im_array, cmap='grey')
    plt.show()

    del(pDataBuff)

    dcamcapture_exc_time = capture_sent_time - start_time
    total_exc_time = end_time - start_time

    dcam.DcamClose()
    dcam.DcamUninitialize()

    return dcamcapture_exc_time, total_exc_time

def capture_img_afterglow(img_nr=1, exposure=1000, padding=0.96):
    dcam.DcamInitialize()
    dcam.DcamOpen()
    dcam.DcamSetDriveMode(DCAM_CCDDRVMODE_OPERATION, 3000)

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
    dcam.DcamSetExposureTime(exposure)
    # dcam.DcamSetTriggerPolarity(DCAM_TRIGPOL_NEGATIVE) 

    dcam.DcamGetBitPerPixel(ct.byref(nBitSize))
    print(f'Bit per pixel: {nBitSize.value}')

    dcam.DcamGetImageSize(ct.byref(nWidth), ct.byref(nHeight))
    print(f'Image size: {nWidth.value} x {nHeight.value}')

    nImageSize = nWidth.value*nHeight.value

    pDataBuff = (ct.c_uint16 * nImageSize)() # Array of c_uint16, equivalente a WORD

    # X-ray source initialization
    if not(img_nr%2 == 0 or img_nr%3 == 0):
        xrs_command("XON")
    time.sleep(3) # Allow time for the x-ray source to stabilize
    response = xrs_command("SAR")
    print("x-ray sorce status values: ", response)

    print("Exposing image...")
    start_time = time.time()
    dcam.DcamCapture(pDataBuff, ct.sizeof(pDataBuff))
    capture_sent_time = time.time()
    time.sleep(padding)
    # xrs_command("XOF")
    end_time = time.time()
    print('Capturing image...')
    sleep_time_sec = 6
    for i in range(0,sleep_time_sec,2):
        dcam.DcamWait(ct.byref(dwRetStatus),5)
        print(f'{WAITSTATUS_DICT[dwRetStatus.value]}')
        time.sleep(2)
    
    print(f'Time to execute capture: {end_time - start_time} seconds')
    print(f'Ended with status: {dwRetStatus.value}')

    im_array = np.ctypeslib.as_array(pDataBuff) 
    im_array = np.reshape(im_array,(nHeight.value,nWidth.value))
    print(im_array)

    filename_str=fr'.\dcam_interface\tests\test_xr\sample_{img_nr:03d}.tiff'
    pFileName = ct.c_char_p(filename_str.encode('utf-8'))
    dcamimg.DcamImgTiffSave(pFileName,pDataBuff,nWidth,nHeight,16,nBitSize)
    print(f'Saved image to {pFileName.value.decode()}')

    # plt.imshow(im_array, cmap='grey')
    # plt.show()

    pDataBuff = None

    dcamcapture_exc_time = capture_sent_time - start_time
    total_exc_time = end_time - start_time

    dcam.DcamStop()
    dcam.DcamClose()
    dcam.DcamUninitialize()

    return dcamcapture_exc_time, total_exc_time

# ================= Main program =================
if __name__ == "__main__":

    sample_nr = 2 # number of samples to capture
    exposure = 30000 # exposure time in ms
    padding_diff = 0.14 # difference between exposure time and padding time
    padding = exposure/1000 - padding_diff # padding time in seconds
    gain = 8
    offset = 1
    note = "Test with mamography scintillator (the pink one) in the detector" # Additional information to add to the text file

    xrs_command("AST 60") # Set the X-ray auto-off time
    xrs_command("MOD 3") # set the X-ray source to manual mode
    xrs_command("CFS 2") # set the X-ray source to large focal spot mode
    xrs_command("HIV 80") # Set the high voltage to 70 kV
    xrs_command("CUR 300") # Set the current to 300 uA
    presets = xrs_command("SVI") # Check the X-ray source settings
    print("X-ray source presets: ", presets)

    with open(".\\dcam_interface\\tests\\test_xr\\capture_data.txt", "w") as f:
        f.write("Sample X-ray images capture data\n\n")
        f.write(f"Exposure time: {exposure} ms,  Padding time: {padding} s\n\n")
        f.write("Note: The padding time is the time the X-ray source stays on after executing dcam.DcamCapture().\n padding_time = exposure time(s) - padding_time(s). \n")
        f.write("Capture time is the time taken by dcam.DcamCapture() to execute.\n")
        f.write("Total time is the total time taken from sending the capture command to the end of the capture.\n")
        f.write(f"****{note}\n\n")
        f.write(f"Gain setting: {gain}, Offset setting: {offset}\n\n")
        f.write("sample_nr    Capture_time(s)    Total_time(s)\n")

    for i in range(1, sample_nr+1):
        capture_time, total_time = capture_img(i, exposure=exposure, padding=padding, gain=gain, offset=offset)
        # capture_time, total_time = capture_img_afterglow(i, exposure=exposure, padding=padding)

        with open(".\\dcam_interface\\tests\\test_xr\\capture_data.txt", "a") as f:
            f.write(f"{i:3d}\t\t {capture_time:.4f}\t\t {total_time:.4f}\n")
        time.sleep(3) # let ccd reset charge between captures
    
    xrs_command("XOF")
    ser.close()