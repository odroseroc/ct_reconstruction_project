"""
constans.py
===========
===========
This module defines constants used in the DCamLIB and DCamIMG libraries interface.
It includes constants for device states, CCD types, drive modes, and error codes.
These constants are used to interact with the Hamamatsu digital X-ray imaging units.

This module includes dictionaries for all the constants, which map integer values to human-readable strings.

This code is not original software; it is a direct interface translation
for use with Hamamatsu hardware such as the C10819-04 control module and S10810 sensor unit.
All rights to the original C API belong to Hamamatsu Photonics. The code is provided
without warranty and is intended for research, testing, or integration purposes only.

Author: [Oscar Rosero]
Date: [2025-07-23] 
"""

#==============================================================================
# CONSTANTS DECLARATION - DCAMLIB
#==============================================================================

###############################################################################
# [The number of bits per pixel] 
# Note: In DCamLibM2 this constants are prefixed wih DCAM, rather than DCAMLIB
DCAMLIB_BITPIXEL_8 = 8     #  8 Bit
DCAMLIB_BITPIXEL_10 = 10   # 10 Bit
DCAMLIB_BITPIXEL_12 = 12   # 12 Bit
# DCAM_BITPIXEL_16 = 16   # 16 Bit  **Does not appear in DCamLib manual

BITPIXEL_DICT = {
    DCAMLIB_BITPIXEL_8: '8 Bit', 
    DCAMLIB_BITPIXEL_10: '10 Bit',
    DCAMLIB_BITPIXEL_12: '12 Bit'
}

###############################################################################
# [Image acq]
DCAM_WAITSTATUS_COMPLETED = 0   # Image acq is complete.
DCAM_WAITSTATUS_UNCOMPLETED = 1 # Image acq is not complete.

WAITSTATUS_DICT = {
    DCAM_WAITSTATUS_COMPLETED: 'Image acq is complete.',
    DCAM_WAITSTATUS_UNCOMPLETED: 'Image acq is not complete.'
}

DCAM_WAIT_INFINITE = -1         # Wait until image acq is complete.

###############################################################################
# [Device state]
# Note: This has been modified from DCamLibM2, where 'unit' is used instead of device
DCAM_DEVSTATE_NON     = 0     # Non-connection, No device found
DCAM_DEVSTATE_DEVICE    = 1     # Non-connection, device found
DCAM_DEVSTATE_NODEVICE  = 2     # Connection, No device found
DCAM_DEVSTATE_CONNECT = 3     # Connection, device found
DCAM_DEVSTATE_BOOT    = 4     # Connection, device found(during the boot process)

DEVSTATE_DICT = {
    DCAM_DEVSTATE_NON: 'Non-connection, No device found',
    DCAM_DEVSTATE_DEVICE: 'Non-connection, Device found',
    DCAM_DEVSTATE_NODEVICE: 'Connection, No device found',
    DCAM_DEVSTATE_CONNECT: 'Connection, Device found',
    DCAM_DEVSTATE_BOOT: 'Connection, Device found (during boot)'
}

###############################################################################
# [CCD drive mode]
# Note: In DCamLibM2 the term 'Sensor drive mode' is used. The constants are called DCAM_DRVMODE_* and the OPERATION state does not exist.
DCAM_CCDDRVMODE_IDLE = 0   # Idle / Sleep
DCAM_CCDDRVMODE_STANDBY = 1    # Standby
DCAM_CCDDRVMODE_OPERATION = 1 # Operation * In he manual for DCamLib it is specified that Operation and Standby are te same modes.

CCDMODE_DICT = {
    DCAM_CCDDRVMODE_IDLE: 'Idle',
    DCAM_CCDDRVMODE_STANDBY: 'Standby',
#    DCAM_CCDDRVMODE_OPERATION: 'Operation'
}

###############################################################################
# [Bining type]
DCAM_BINNING_1X1 = 0     # 1x1
DCAM_BINNING_2X2 = 1     # 2x2

BINNING_DICT = {
    DCAM_BINNING_1X1: '1x1',
    DCAM_BINNING_2X2: '2x2'
}

###############################################################################
# [Trigger mode]
DCAM_TRIGMODE_INT        = 0     # Internal Mode
DCAM_TRIGMODE_EXT_LEVEL1 = 2     # External Trigger Level Mode
DCAM_TRIGMODE_EXT_EDGE1  = 4     # External Trigger Edge Mode

TRIGMODE_DICT = {
    DCAM_TRIGMODE_INT: 'Internal Mode',
    DCAM_TRIGMODE_EXT_LEVEL1: 'External Trigger Level Mode',
    DCAM_TRIGMODE_EXT_EDGE1: 'External Trigger Edge Mode'
}

# Constants not defined in DCamLibM2
# TODO: Map these constants and include to dict once verified.
DCAM_TRIGMODE_EXT_START = 0
DCAM_TRIGMODE_EXT_EDGE = 0
DCAM_TRIGMODE_EXT_EDGE2 = 0
DCAM_TRIGMODE_EXT_LEVEL2 = 0

###############################################################################
# [Trigger polarity]
DCAM_TRIGPOL_POSITIVE = 0     # Positive polarity
DCAM_TRIGPOL_NEGATIVE = 1     # Negative polarity

TRIGPOL_DICT = {
    DCAM_TRIGPOL_POSITIVE: 'Positive trigger polarity', 
    DCAM_TRIGPOL_NEGATIVE: 'Negative trigger polarity'
}

###############################################################################
# [CCD type] (In DCamLibM2 the constants defining the reslution of the camera are refered to as 'Model number' and called DCAM_MODEL_NUMBER0*. The actual values of the new constants are not available in the manual of DCamLib, so they are assumed from the old values)
DCAM_CCD_TYPE0 = 0     # 1508 x 1002   ( 1500 x 1000 ) S8981 S10810
DCAM_CCD_TYPE1 = 1     # 1708 x 1202   ( 1700 x 1200 ) S8985 S10811
DCAM_CCD_TYPE2 = 2     #  608 x  402   (  600 x  400 ) S7368-01
# DCAM_MODEL_NUMBER04 = 3     # 1758 x 1202   ( 1706 x 1200 ) (N/A in DCamLib)

CCDTYPE_DICT = {
    DCAM_CCD_TYPE0: '1508 x 1002 (1500 x 1000) S8981 S10810',
    DCAM_CCD_TYPE1: '1708 x 1202 (1700 x 1200) S8985 S10811',
    DCAM_CCD_TYPE2: ' 608 x  402 ( 600 x  400) S7368-01'
}

###############################################################################
# [Camera Information] 
# Note: In DCamLIBM2 this is referred as 'Unit information type'. 
# Constants are called DCAM_UNITINF_* in DCamLIBM2.
DCAM_CAMINF_TYPE           = 0     # Unit type
DCAM_CAMINF_SERIALNO       = 1     # Serial number of unit
DCAM_CAMINF_VERSION        = 2     # Unit version
# DCAM_UNTINF_SENSOR_LNO_SNO = 3     # Lot No. and Serial No. of Snesor (N/A)

CAMINF_DICT = {
    DCAM_CAMINF_TYPE: 'Unit type',
    DCAM_CAMINF_SERIALNO: 'Serial number of unit',
    DCAM_CAMINF_VERSION: 'Unit version'
}

##############################################################################
# [USB transfer rate type]
DCAM_TRANSRATE_USB11 = 0     # USB 1.1 standard
DCAM_TRANSRATE_USB20 = 1     # USB 2.0 standard

TRANSRATE_DICT = {
    DCAM_TRANSRATE_USB11: 'USB 1.1 standard',
    DCAM_TRANSRATE_USB20: 'USB 2.0 standard'
}

##############################################################################
##############################################################################
##############################################################################
# Run Status ( DCamCode )
dcCode_Success          =   0      # Ended successfully
dcCode_Unknown          =   1      # An unknown error has occurred
dcCode_NoInit           =   2      # Library is not initialized
dcCode_AlreadyInit      =   3      # Already used by other
dcCode_NoDriver         =   4      # No driver was found
dcCode_NoMemory         =   5      # Memory is insufficient
dcCode_NotConnected     =   6      # Not connected

dcCode_InvalidParam     =   9      # Invalid Argument

dcCode_UnitAnomaly      = 100      # Unit anomaly

dcCode_Overrun          = 110      # Overrun error
dcCode_Timeout          = 111      # Timeout error

dcCode_AlreadyStart     = 120      # Already start

dcCode_TransRate_USB11  = 121      # USB version 1.1 
dcCode_InvalidCamC10819 = 122      #Camera is not of type C10819

RUNSTATUS_DICT = {
    dcCode_Success: 'Ended successfully',
    dcCode_Unknown: 'An unknown error has occurred',
    dcCode_NoInit: 'Library is not initialized',
    dcCode_AlreadyInit: 'Already used by other',
    dcCode_NoDriver: 'No driver was found',
    dcCode_NoMemory: 'Memory is insufficient',
    dcCode_NotConnected: 'Not connected',
    dcCode_InvalidParam: 'Invalid Argument',
    dcCode_UnitAnomaly: 'Unit anomaly',
    dcCode_Overrun: 'Overrun error',
    dcCode_Timeout: 'Timeout error',
    dcCode_AlreadyStart: 'Already start',
    dcCode_TransRate_USB11: 'USB version 1.1',
    dcCode_InvalidCamC10819: 'Camera is not of type C10819'
}
##############################################################################
##############################################################################


#==============================================================================
# CONSTANTS DECLARATION - DCAMIMG
#==============================================================================

########################################
#   Convert Type
DCAM_IMG_SAVECNVTYPE_AUTO	= 0		# Auto
DCAM_IMG_SAVECNVTYPE_FIXED	= 1		# Fixed
DCAM_IMG_SAVECNVTYPE_SHIFT	= 2		# Set bit shift

CONVERTTYPE_DICT = {
    DCAM_IMG_SAVECNVTYPE_AUTO: 'Auto',
    DCAM_IMG_SAVECNVTYPE_FIXED: 'Fixed',
    DCAM_IMG_SAVECNVTYPE_SHIFT: 'Set bit shift'
}

########################################
#   Error Code
Code_Success				= 0		# Ended successfully
Code_Unknown				= 1		# An unknown error has occurred
Code_InvalidFileName		= 2		# Invalid Filename
Code_InvalidParam			= 3		# Invalid Argument
Code_ErrorFileOpen			= 4     # Error while opening file.
Code_ErrorFileRead			= 5     # Error while reading file.
Code_ErrorMemory			= 6		# Memory Error.
Code_ErrorFileLoad			= 7		# Error file loading
Code_ErrorFileSave			= 8		# Error file saving

IMGERRCODE_DICT = {
    Code_Success: 'Ended successfully',
    Code_Unknown: 'An unknown error has occurred',
    Code_InvalidFileName: 'Invalid Filename',
    Code_InvalidParam: 'Invalid Argument',
    Code_ErrorFileOpen: 'Error while opening file.',
    Code_ErrorFileRead: 'Error while reading file.',
    Code_ErrorMemory: 'Memory Error.',
    Code_ErrorFileLoad: 'Error file loading',
    Code_ErrorFileSave: 'Error file saving'
}