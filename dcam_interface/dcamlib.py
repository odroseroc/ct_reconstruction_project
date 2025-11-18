"""
dcamlib.py
===========
===========
This module provides a ctypes-based interface to the DCamLIB.dll library,
which is used to control Hamamatsu's digital X-ray imaging units, such as
the C10819-04 control module and S10810 sensor unit. It is a direct
translation of the original C API header DCamLIBM2.h, which was designed
for a Windows XP-specific version of the library provided by Hamamatsu.

The C header DCamLib.h was not provided with our hardware, so some
educated assumptions and manual mappings were required for constants that
did not exist in DCamLIBM2 and functions with different names. Where such
assumptions were made, comments are included directly in the code to
indicate the adaptation. Use with care and validate on your specific
hardware.

This module is not original software; it is a direct interface translation
for use with Hamamatsu hardware. All rights to the original C API belong
to Hamamatsu Photonics. This code is provided without warranty and is
intended for research, testing, or integration purposes only.

Author: [Oscar Rosero]
Date: [2025-07-23]

Information and copyright details provided with the original C API:

/*=============================================================================
  Target Name	: Digital X-ray Imaging Unit Control Library DLL
  Target Type	: DLL [DCamLIBM2.dll]
				:	<<< Copyright(c) 2002-2006, HAMAMATSU PHOTONICS K.K. >>>
				:
  Created		: Dec. 24, 2002
  Last Updated	: Jun. 25, 2006
-------------------------------------------------------------------------------

=============================================================================*/
"""

import ctypes

# Load DLL
dcam = ctypes.WinDLL("DCamLIB.dll") # WinDLL used when metod is __stdcall

# Alias for frequently used tyes
c_int = ctypes.c_int
c_char = ctypes.c_char
c_void_p = ctypes.c_void_p
c_char_p = ctypes.c_char_p
c_uint32 = ctypes.c_uint32  # DWORD
c_bool = ctypes.c_int  # BOOL is int in Windows

#============================================================================
# DcamInitialize()
#  Initialize the library.
# ---------------------------------------------------------------------------
# [Argument]
#          None. 
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#          1.  This function must first be run before running other functions.
#          2.  An error is issued if the library has already been initialized.
#          3.  Only one process can use this library.
#============================================================================
dcam.DcamInitialize.argtypes = []
dcam.DcamInitialize.restype = c_bool

#============================================================================
# DcamUninitialize()
#  Unload the library resources and close the device driver.
# ---------------------------------------------------------------------------
# [Argument]
#          None.
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#          Call this function when quitting the program or the DCamLIB library is not needed.
#============================================================================
dcam.DcamUninitialize.argtypes = []
dcam.DcamUninitialize.restype = c_bool

#============================================================================
# DcamOpen()
#  Open the unit.
# ---------------------------------------------------------------------------
# [Argument]
#          None.
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamOpen.argtypes = []
dcam.DcamOpen.restype = c_bool

#============================================================================
# DcamClose()
#  Close the unit.
# ---------------------------------------------------------------------------
# [Argument]
#          None.
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamClose.argtypes = []
dcam.DcamClose.restype = c_bool

#============================================================================
# DcamGetImageSize()
#  Obtain the width and height of image data to acquire from the unit.
# ---------------------------------------------------------------------------
# [Argument]
#          pWidth      : /O: Specify the address of the variable where the image 
#                            width is to be stored. 
#          pHeight     : /O: Specify the address of the variable where the image 
#                             height is to be stored.
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetImageSize.argtypes = [ctypes.POINTER(c_int), ctypes.POINTER(c_int)]
dcam.DcamGetImageSize.restype = c_bool

#============================================================================
# DcamGetBitPerPixel()
#  Obtain the number of bits per pixel.
# ---------------------------------------------------------------------------
# [Argument]
#          pBit        : /O: Specify the address of the variable where the number 
#                            of bits per pixel is to be stored. One of the following 
#                            values is obtained.
#                              DCAM_BITPIXEL_8     : 8 Bit
#                              DCAM_BITPIXEL_10    : 10 Bit
#                              DCAM_BITPIXEL_12    : 12 Bit
#                              DCAM_BITPIXEL_16    : 16 Bit
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetBitPerPixel.argtypes = [ctypes.POINTER(c_int)]
dcam.DcamGetBitPerPixel.restype = c_bool

#============================================================================
# DcamGetFrameBytes()
#  Obtain the total number of bytes per frame.
# ---------------------------------------------------------------------------
# [Argument]
#          pFrameBytes : /O: Specify the address of the variable where the total 
#                            number of bytes per frame is to be stored.
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetFrameBytes.argtypes = [ctypes.POINTER(c_int)]
dcam.DcamGetFrameBytes.restype = c_bool

#============================================================================
# DcamCapture()
#  Start to acquire one image from the unit.
# ---------------------------------------------------------------------------
# [Argument]
#          pImageBuff  : /O: Specify the start address in the buffer where image 
#                            data is to be stored.
#          nBuffSize   :I/ : Specify the buffer size (number of bytes).
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#          1. This function issues an instruction to start image acq.
#             Since image acq is not complete even when this function ends,
#             use the DcamWait function to check whether image acq is complete.
#          2. The necessary buffer size can be obtained with the DcamGetFrameBytes function.
#============================================================================
dcam.DcamCapture.argtypes = [c_void_p, c_int]
dcam.DcamCapture.restype = c_bool

#============================================================================
# DcamCaptureReverseX()
#  Start to acquire one image from the unit.
# ---------------------------------------------------------------------------
# [Argument]
#          pImageBuff  : /O: Specify the start address in the buffer where image 
#                            data is to be stored.
#          nBuffSize   :I/ : Specify the buffer size (number of bytes).
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#          1. This function issues an instruction to start image acq.
#             Since image acq is not complete even when this function ends,
#             use the DcamWait function to check whether image acq is complete.
#          2. The necessary buffer size can be obtained with the DcamGetFrameBytes function.
#============================================================================
dcam.DcamCaptureReverseX.argtypes = [c_void_p, c_int]
dcam.DcamCaptureReverseX.restype = c_bool

#============================================================================
# DcamStop()
#  Stop image acq.
# ---------------------------------------------------------------------------
# [Argument]
#          None. 
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamStop.argtypes = []
dcam.DcamStop.restype = c_bool

#============================================================================
# DcamWait()
#  Wait for image acq to complete.
# ---------------------------------------------------------------------------
# [Argument]
#          pStatus     : /O: Specify the address of the variable where image 
#                            acq end status is to be stored. Whether
#                            image acq is complete or not can be checked
#                            by the value in this variable. 
#                            The value is one of the following:
#                              DCAM_WAITSTATUS_COMPLETED   : Image acq is complete.
#                              DCAM_WAITSTATUS_UNCOMPLETED : Image acq is not complete.
#
#                            This may be set to NULL when "DCAM_WAIT_INFINITE" is 
#                            specified for "nTimeout".
#                              
#          nTimeout    :I/ : Specify the length of timeout in milliseconds.
#                            When "DCAM_WAIT_INFINITE" is specified here, the process 
#                            waits until image acq is finished.
#                            When "0" is specified, control is returned immediately 
#                            after checking the status.
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamWait.argtypes = [ctypes.POINTER(c_uint32), c_int]
dcam.DcamWait.restype = c_bool

#============================================================================
# DcamSetGain()
#  Set the gain.
# ---------------------------------------------------------------------------
# [Argument]
#          nGain       :I/ : Specify the gain value in the range from 1 to 10
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamSetGain.argtypes = [c_int]
dcam.DcamSetGain.restype = c_bool

#============================================================================
# DcamGetGain()
#  Obtain the gain.
# ---------------------------------------------------------------------------
# [Argument]
#          pGain       : /O: Specify the address of the variable where the gain is 
#                            to be stored.
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetGain.argtypes = [ctypes.POINTER(c_int)]
dcam.DcamGetGain.restype = c_bool

#============================================================================
# DcamSetOffset()
#  Set the offset.
# ---------------------------------------------------------------------------
# [Argument]
#          nOffset     :I/ : Specify the offset value in the range from 0 to 255
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamSetOffset.argtypes = [c_int]
dcam.DcamSetOffset.restype = c_bool

#============================================================================
# DcamGetOffset()
#  Obtain the offset.
# ---------------------------------------------------------------------------
# [Argument]
#          pOffset     : /O: Specify the address of the variable where the offset is 
#                            to be stored.
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetOffset.argtypes = [ctypes.POINTER(c_int)]
dcam.DcamGetOffset.restype = c_bool

#============================================================================
# DcamSetDriveMode()
#  Set the sensor drive mode.
# ---------------------------------------------------------------------------
# [Argument]
#          nMode       :I/ : Specify the sensor drive mode. One of the following can. However, Operation and Standby are the same modes be specified. 
#                              DCAM_DRVMODE_IDLE       : Idle / Sleep
#                              DCAM_DRVMODE_STANDBY    : Standby
#							   DCAM_DRVMODE_OPERATION  : Operation
#          nTimeout    :I/ : Specify the length of timeout in milliseconds. 
#                            Please set one or more values.
#                            When "0" is specified, processing is carried out 
#                            by the standard timeout.
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamSetDriveMode.argtypes = [c_int, c_int]
dcam.DcamSetDriveMode.restype = c_bool

#============================================================================
# DcamGetDriveMode()
#  Obtain the sensor drive mode.
# -----------------------------------------------------------------------------
# [Argument]
#          pMode       : /O: Specify the address of the variable where the CCD drive mode is to be stored. One of the following values is obtained. However, Operation and Standby are the same modes be specified.
#                              DCAM_DRVMODE_IDLE       : Idle / Sleep
#                              DCAM_DRVMODE_STANDBY    : Standby
#							   DCAM_DRVMODE_OPERATION  : Operation
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetDriveMode.argtypes = [ctypes.POINTER(c_int)]
dcam.DcamGetDriveMode.restype = c_bool

#============================================================================
# DcamSetBinning()
#  Set the binning.
# ---------------------------------------------------------------------------
# [Argument]
#          nBinning    :I/ : Specify the binning. One of the following can be 
#                            specified. 
#                              DCAM_BINNING_1X1    : Binning 1x1
#                              DCAM_BINNING_2X2    : Binning 2x2
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#          When this function is run, the number of bytes per frame size may change. 
#          Check the frame size with the DcamGetFrameBytes function.
#============================================================================
dcam.DcamSetBinning.argtypes = [c_int]
dcam.DcamSetBinning.restype = c_bool

#============================================================================
# DcamGetBinning()
#  Obtain the binning.
# ---------------------------------------------------------------------------
# [Argument]
#          pBinning    : /O: Specify the address of the variable where the 
#                            currently set 
#                            binning is to be stored. One of the following values 
#                            is obtained.
#                              DCAM_BINNING_1X1    : Binning 1x1
#                              DCAM_BINNING_2X2    : Binning 2x2
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetBinning.argtypes = [ctypes.POINTER(c_int)]
dcam.DcamGetBinning.restype = c_bool

#============================================================================
# DcamSetTriggerMode()
#  Set the trigger mode.
# ---------------------------------------------------------------------------
# [Argument]
#          nMode       :I/ : Specify the trigger mode. One of the following 
#                            can be specified. 
#                              DCAM_TRIGMODE_INT        : Internal Mode
#                              DCAM_TRIGMODE_EXT_EDGE1  : External Trigger Level Mode
#                              DCAM_TRIGMODE_EXT_LEVEL1 : External Trigger Edge Mode
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamSetTriggerMode.argtypes = [c_int]
dcam.DcamSetTriggerMode.restype = c_bool

#============================================================================
# DcamGetTriggerMode()
#  Obtain the trigger mode.
# ---------------------------------------------------------------------------
# [Argument]
#          pMode       : /O: Specify the address of the variable where the 
#                            currently set trigger mode 
#                            is to be stored. One of the following values is obtained.
#                              DCAM_TRIGMODE_INT        : Internal Mode
#                              DCAM_TRIGMODE_EXT_EDGE1  : External Trigger Level Mode
#                              DCAM_TRIGMODE_EXT_LEVEL1 : External Trigger Edge Mode
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetTriggerMode.argtypes = [ctypes.POINTER(c_int)]
dcam.DcamGetTriggerMode.restype = c_bool

#============================================================================
# DcamSetTriggerPolarity()
#  Set the trigger polarity.
# ---------------------------------------------------------------------------
# [Argument]
#          nPolarity   :I/ : Specify the trigger polarity. One of the following 
#                            can be specified. 
#                              DCAM_TRIGPOL_POSITIVE   : Positive
#                              DCAM_TRIGPOL_NEGATIVE   : Negative
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamSetTriggerPolarity.argtypes = [c_int]
dcam.DcamSetTriggerPolarity.restype = c_bool

#============================================================================
# DcamGetTriggerPolarity()
#  Obtain the trigger polarity.
# ---------------------------------------------------------------------------
# [Argument]
#          pPolarity   : /O: Specify the address of the variable where the 
#                            currently set trigger polarity is to be stored. 
#                            One of the following values is obtained.
#                              DCAM_TRIGPOL_POSITIVE   : Positive
#                              DCAM_TRIGPOL_NEGATIVE   : Negative
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetTriggerPolarity.argtypes = [ctypes.POINTER(c_int)]
dcam.DcamGetTriggerPolarity.restype = c_bool

#============================================================================
# DcamSetExposureTime()
#  Set the exposure time.
# ---------------------------------------------------------------------------
# [Argument]
#          nTime       :I/ : Specify an exposure time from 0 to 65535 [msec].
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamSetExposureTime.argtypes = [c_int]
dcam.DcamSetExposureTime.restype = c_bool

#============================================================================
# DcamGetExposureTime()
#  Obtain the exposure time.
# ---------------------------------------------------------------------------
# [Argument]
#          pTime       : /O: Specify the address of the variable where the  
#                            currently setexposure time [msec] is to be stored.
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetExposureTime.argtypes = [ctypes.POINTER(c_int)]
dcam.DcamGetExposureTime.restype = c_bool

#============================================================================
# DcamSetCCDType()
#  Set the type of "Package" model number.
# ---------------------------------------------------------------------------
# [Argument]
#          nType       :I/ : Specify the "Package" model number from among the following types. 
#                              DCAM_CCD_TYPE0 : 1508 x 1002 	( 1500 x 1000 )
#							   DCAM_CCD_TYPE1 : 1708 x 1202 	( 1700 x 1200 )
#						       DCAM_CCD_TYPE2 :   608 x 402 	( 600 x 400 )
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#          When this function is run, the number of bytes per frame size may change. 
#          Check the frame size with the DcamGetFrameBytes function.
#============================================================================
dcam.DcamSetCCDType.argtypes = [c_int]
dcam.DcamSetCCDType.restype = c_bool

#============================================================================
# DcamGetCCDType()
#  Obtain the type of "Package" model number.
# ---------------------------------------------------------------------------
# [Argument]
#          pType       : /O: Specify the address of the variable where the currently  
#                            set "Package" model number type is to be stored. 
#                            One of the following values is obtained.
#                              DCAM_CCD_TYPE0 : 1508 x 1002 	( 1500 x 1000 )
#							   DCAM_CCD_TYPE1 : 1708 x 1202 	( 1700 x 1200 )
#						       DCAM_CCD_TYPE2 :   608 x 402 	( 600 x 400 )
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetCCDType.argtypes = [ctypes.POINTER(c_int)]
dcam.DcamGetCCDType.restype = c_bool

#============================================================================
# DcamLoadParameters()
#  Load parameters to the unit.
# ---------------------------------------------------------------------------
# [Argument]
#          nTimeout    :I/ : Specify the length of timeout in milliseconds. 
#                            Please set one or more values.
#                            When "0" is specified, processing is carried out 
#                            by the standard timeout.
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamLoadParameters.argtypes = [c_int]
dcam.DcamLoadParameters.restype = c_bool

#============================================================================
# DcamStoreParameters()
#  Store parameters to the unit.
# ---------------------------------------------------------------------------
# [Argument]
#          None.
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamStoreParameters.argtypes = []
dcam.DcamStoreParameters.restype = c_bool

#============================================================================
# DcamGetVersion()
#  Obtain the library version number, in string format.
# ---------------------------------------------------------------------------
# [Argument]
#          szVersion   : /O: Specify the start address in the character string 
#                            buffer where the version of the library is to be stored.
#          nBuffSize   :I/ : Specify the buffer size (number of bytes). 
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetVersion.argtypes = [ctypes.POINTER(c_char), c_int]
dcam.DcamGetVersion.restype = c_bool

#============================================================================
# DcamGetDriverVersion()
#  Obtain the driver version number, in string format.
# ---------------------------------------------------------------------------
# [Argument]
#          szVersion   : /O: Specify the start address in the character string 
#                            buffer where the version of the driver is to be stored.
#          nBuffSize   :I/ : Specify the buffer size (number of bytes). 
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetDriverVersion.argtypes = [ctypes.POINTER(c_char), c_int]
dcam.DcamGetDriverVersion.restype = c_bool

#============================================================================
# DcamGetFirmwareVersion()
#  Obtain the firmware version number, in string format.
# ---------------------------------------------------------------------------
# [Argument]
#          szVersion   : /O: Specify the start address in the character string 
#                            buffer where the version of the firmware is to be stored.
#          nBuffSize   :I/ : Specify the buffer size (number of bytes). 
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetFirmwareVersion.argtypes = [ctypes.POINTER(c_char), c_int]
dcam.DcamGetFirmwareVersion.restype = c_bool

# WARNING! DcamGetCameraInformation in DCamLib apears to have replaced DcamGetUnitInformation from DCamLibM2. Both functions have the same signature in the manual, but at the moment of writing this script, we only had access to DCamLibM2.h, so we cannot be comlete certain of this deffinition.
#============================================================================
# DcamGetCameraInformation()
#  Obtain the unit information, in string format.
# ---------------------------------------------------------------------------
# [Argument]
#          nType       :I/ : Specify the Information Type from among the following types.
#                              DCAM_UNTINF_TYPE            : Unit type
#                              DCAM_UNTINF_SERIALNO        : Serial number of unit
#                              DCAM_UNTINF_VERSION         : Unit version
#                              DCAM_UNTINF_SENSOR_LNO_SNO  : Lot No. and Serial No. of sensor
#          szBuff      : /O: Specify the start address in the character string buffer  
#                            where the information of unit is to be stored.
#          nBuffSize   :I/ : Specify the buffer size (number of bytes). 
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetCameraInformation.argtypes = [c_int, ctypes.POINTER(c_char), c_int]
dcam.DcamGetCameraInformation.restype = c_bool

#============================================================================
# DcamGetTransferRateType()
#  Obtain the USB transfar rate type.
# ---------------------------------------------------------------------------
# [Argument]
#          pType       : /O: Specify the address of the variable where the USB
#                            transfar rate type is to be stored. One of the 
#                            following values is obtained.
#                              DCAM_TRANSRATE_USB11    : USB 1.1 standard
#                              DCAM_TRANSRATE_USB20    : USB 2.0 standard
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetTransferRateType.argtypes = [ctypes.POINTER(c_int)]
dcam.DcamGetTransferRateType.restype = c_bool

# WARNING! DcamGetDeviceState in DCamLib apears to have replaced DcamGetUnitState from DCamLibM2. Both functions have the same signature, but at the moment of writing this script, we only had access to DCamLibM2.h, so we cannot be comlete certain of this deffinition.
#============================================================================
# DcamGetDeviceState()
#  Obtain the type of unit state.
# ---------------------------------------------------------------------------
# [Argument]
#          pState      : /O: Specify the address of the variable where the type 
#                            of unit state is to be stored. One of the 
#                            following values is obtained.
#                              DCAM_UNTSTATE_NON       : Non-connection, No unit found
#                              DCAM_UNTSTATE_UNIT      : Non-connection, Unit found
#                              DCAM_UNTSTATE_NOUNIT    : Connection, No unit found
#                              DCAM_UNTSTATE_CONNECT   : Connection, Unit found
#                              DCAM_UNTSTATE_BOOT      : Connection, Unit found(during the boot process)
# [Return values]
#          If the function succeeds the return value is TRUE (1). 
#          If the function fails the return value is FALSE (0).
#          To obtain detailed error information, use the DcamGetLastError function.
# [Note]
#============================================================================
dcam.DcamGetDeviceState.argtypes = [ctypes.POINTER(c_int)]
dcam.DcamGetDeviceState.restype = c_bool

#============================================================================
# DcamGetLastError()
#  Obtain the last-error code.
# ---------------------------------------------------------------------------
# [Argument]
#          None. 
# [Return values]
#          The latest error code is returned. See the error code table for 
#          descriptions of error codes.
# [Note]
#============================================================================
dcam.DcamGetLastError.argtypes = []
dcam.DcamGetLastError.restype = c_uint32


#====================Function aliases (C-style)==============================
# These aliases allow to call the functions like in the C API, without making
# reference to the dcam ctype object required to load the library.
DcamGetImageSize = dcam.DcamGetImageSize
DcamGetBitPerPixel = dcam.DcamGetBitPerPixel
DcamGetFrameBytes = dcam.DcamGetFrameBytes
DcamCapture = dcam.DcamCapture
DcamCaptureReverseX = dcam.DcamCaptureReverseX
DcamStop = dcam.DcamStop
DcamWait = dcam.DcamWait
DcamSetGain = dcam.DcamSetGain
DcamGetGain = dcam.DcamGetGain
DcamSetOffset = dcam.DcamSetOffset
DcamGetOffset = dcam.DcamGetOffset
DcamSetDriveMode = dcam.DcamSetDriveMode
DcamGetDriveMode = dcam.DcamGetDriveMode
DcamSetBinning = dcam.DcamSetBinning
DcamGetBinning = dcam.DcamGetBinning
DcamSetTriggerMode = dcam.DcamSetTriggerMode
DcamGetTriggerMode = dcam.DcamGetTriggerMode
DcamSetTriggerPolarity = dcam.DcamSetTriggerPolarity
DcamGetTriggerPolarity = dcam.DcamGetTriggerPolarity
DcamSetExposureTime = dcam.DcamSetExposureTime
DcamGetExposureTime = dcam.DcamGetExposureTime
DcamSetCCDType = dcam.DcamSetCCDType
DcamGetCCDType = dcam.DcamGetCCDType
DcamLoadParameters = dcam.DcamLoadParameters
DcamStoreParameters = dcam.DcamStoreParameters
DcamGetVersion = dcam.DcamGetVersion
DcamGetDriverVersion = dcam.DcamGetDriverVersion
DcamGetFirmwareVersion = dcam.DcamGetFirmwareVersion
DcamGetCameraInformation = dcam.DcamGetCameraInformation
DcamGetTransferRateType = dcam.DcamGetTransferRateType
DcamGetDeviceState = dcam.DcamGetDeviceState
DcamGetLastError = dcam.DcamGetLastError