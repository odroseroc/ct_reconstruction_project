"""
Python translation of Hamamatsu's DCamImg C API headers.

This file provides Python bindings to the DCamImg.dll
dynamic library using ctypes. It is based directly on the original
C headers provided by Hamamatsu for their camera/control modules.

Author: [Oscar Rosero]
Date: [2025-07-23]

Note:
This is not original software; it is a direct interface translation 
for use with Hamamatsu hardware such as the C10819-04 control module 
and S10810 sensor unit. All rights to the original C API belong to 
Hamamatsu Photonics.

This code is provided without warranty and is intended for research,
testing, or integration purposes only.
"""

import ctypes

dcamimg = ctypes.WinDLL("DCamImg.dll")

# Alias for frequently used tyes
c_int = ctypes.c_int
c_void_p = ctypes.c_void_p
c_char_p = ctypes.c_char_p
c_uint32 = ctypes.c_uint32  # DWORD
c_bool = ctypes.c_int  # BOOL is int in Windows

#######################################/
#
#   DCamImg.h
#
#    Summary
#	Header file for the DLL file that handles the operation over TIFF and 
#  bitmap Images. DLL includes functions used to get the information of 
#	TIFF image, also loading and saving of TIFF image and saving of bitmap.
#
#		Saving in TIFF has two options. First, saving 16 bits grayscale
#	image. Second one is saving 16 bits image into 8 bits image after 
#	undergoing conversion by the method selected by user.
#
#		Saving bitmap is through conversion of 16 bits image to 8 bits image.
# 
#		To save 16 bits image you can use TIFFImgSave. In which you can
#	also pass a parameter which gives the significant bits(i.e bits useful)
#	among the 16 bits.
#
#		To save 8 bits image TIFF data undergoes an conversion. 
#	This DLL supports only 16 bits grayscale image that will be stored 
#	as 8 bits, grayscale image.
#
#		Bitmap image conversion from 16 bits to 8 bits is similar to that of
#	TIFF image.
#
#		Conversion is carried by one of the following type.
#	1)AUTO : In this the max and min among all the pixels are searched.
#		 Then max value will be mapped to max value a 8 bits varaible
#		 can represent. And min will be mapped to min i.e 0. All other
#		 intermidiate values are to be mapped between 0 and 255.
#	2)FIXED: It is similar to AUTO only with one difference. The min and
#		 max is passed by user.
#	3)SHIFT: In this the shifting is done on the pixel value by the shift
#		 number given by user and lower 8 bits of the resultant is used
#		 as pixel value. Shifting is right shift.

#
#    Created on
#      2003 March   02	 @ Acty systems, Hamamatsu. 
#  
#   @Last updated on
#		2003 July	 01	 @ Acty systems, Hamamatsu.
# @	
#    Functions used
#	1)DcamImgBmpSave8
#	2)DcamImgTiffGetInfo
#	3)DcamImgTiffLoad	   
#	4)DcamImgTiffSave
#	5)DcamImgTiffSave8	   
#
#    Note
#	DLL supports 8bits image converted from 16 bits.
#	Saving of 16 bits image in case of TIFF.
#	This DLL supports only grayscale images.
#  Pay attention to TOP BOTTOM approach of TIFF and BOTTOM UP of bitmap.
#
#######################################/

########################################
#   Convert Type
DCAM_IMG_SAVECNVTYPE_AUTO	= 0		# Auto
DCAM_IMG_SAVECNVTYPE_FIXED	= 1		# Fixed
DCAM_IMG_SAVECNVTYPE_SHIFT	= 2		# Set bit shift

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

# ============================================================================
# ¡ DcamImgBmpSave8
# ---------------------------------------------------------------------------
# < Argument >		lpszFileName : BMP file name.
#					pBuffer		 : Buffer to hold the image bits.
#					nWidth		 : To hold the width of the image.
#					nHeight		 : To hold the height of the image.
#					nConvType	 : Saving type.
#									DCAM_IMG_SAVECNVTYPE_AUTO
#									DCAM_IMG_SAVECNVTYPE_FIXED
#									DCAM_IMG_SAVECNVTYPE_SHIFT
#					nMinVal		 : Maximum value
#					nMaxVal		 : Minimum value
#					nShift		 : 
#
# < Return value > TRUE if the file is properly saved, else returns FALSE.
#
# < Contents >	
#
# ============================================================================
dcamimg.DcamImgBmpSave8.argtypes = [c_char_p, c_void_p, c_int, c_int, c_int, c_int, c_int, c_int]
dcamimg.DcamImgBmpSave8.restype = c_bool

# ============================================================================
#@@ @DcamImgTiffGetInfo
#-----------------------------------------------------------------------------
#
#    < Purpose	>   To get the TIFF image info.
#
#    < Arguments >	LPCTSTR lpszFileName : TIFF file name.
#					INT*	pWidth	     : To hold the width of the image.
#					INT*	pHeight	     : To hold the height of the image.
#					INT*	pBitsPerPixel: To hold the bits per pixel.
#					INT*	pBitsUsed	 : To hold the bits used(can be less than
#											bits per pixel).
#
#    < Returns >	BOOL : TRUE the information is gathered else returns FALSE.
#
#    < Note >      Nothing
# ============================================================================
dcamimg.DcamImgTiffGetInfo.argtypes = [c_char_p, ctypes.POINTER(c_int), ctypes.POINTER(c_int), ctypes.POINTER(c_int), ctypes.POINTER(c_int)]
dcamimg.DcamImgTiffGetInfo.restype = c_bool

# ============================================================================
#@@ @DcamImgTiffLoad
#-----------------------------------------------------------------------------
#
#    < Purpose >   To load the TIFF image.
#
#    < Arguments > LPCTSTR lpszFileName : TIFF file name.
#					PVOID	pBuffer	     : Buffer to hold the image bits.
#					INT		nBufferLength: Length of the buffer.
#
#    < Returns >	TRUE if the image is properly loaded.
#
#    < Note >      Nothing
# ============================================================================
dcamimg.DcamImgTiffLoad.argtypes = [c_char_p, c_void_p, c_int]
dcamimg.DcamImgTiffLoad.restype = c_bool

# ============================================================================
#@@ @DcamImgTiffSave
#-----------------------------------------------------------------------------
#
#    < Purpose >      To save the TIFF image.
#
#    < Arguments >     LPCTSTR lpszFileName : TIFF file name.
#						PVOID	pBuffer	     : Image bits(pixel values).
#						INT		nWidth	     : To hold the width of the image.
#						INT		nHeight	     : To hold the height of the image.
#						INT		nBitsPerPixel: To hold the bits per pixel
#						INT		nBitsUsed    : Bits used by image.
#											   (may be less than bits per 
#												pixel.)
#	
#
#    < Returns >	TRUE if file is properly saved, else returns FALSE.
#
#    < Note >      Note that images in TIFF files are saved in Top Bottom 
#					order.
# ===========================================================================
dcamimg.DcamImgTiffSave.argtypes = [c_char_p, c_void_p, c_int, c_int, c_int, c_int]
dcamimg.DcamImgTiffSave.restype = c_bool

# ============================================================================
#@@ @DcamImgTiffSave8
#-----------------------------------------------------------------------------
#
#    < Purpose >  To save the TIFF image.
#
#    < Arguments >LPCTSTR lpszFileName : TIFF file name.
#				   PVOID	pBuffer	     : Image bits(pixel values).	
#				   INT		nWidth	     : To hold the width of the image.
#				   INT		nHeight	     : To hold the height of the image.
#				   INT		nConvType    : Type of conversion
#											0 DCAM_IMG_SAVECNVTYPE_AUTO
#											1 DCAM_IMG_SAVECNVTYPE_FIXED
#											2 DCAM_IMG_SAVECNVTYPE_SHIFT
#				   INT		nMinVal	     : Minimum pixel value to be in converted
#									       data ignored in AUTO and SHIFT.	
#				   INT		nMaxVal	     : Maximum pixel value to be in converted
#									       data ignored in AUTO and SHIFT.
#				   INT		nShift	     : Number of bits shifts to be done.
#									       Used only with 
#										   DCAM_IMG_SAVECNVTYPE_SHIFT.
#
#    Returns:	TRUE if file is properly saved, else returns FALSE.
#
#    Note:     1) Conversion for AUTO and FIXED type is only from 16 to 8 bits.
#				2)  Note that images in TIFF files are saved in Top Bottom 
#					order.
#				 
# ============================================================================
dcamimg.DcamImgTiffSave8.argtypes = [c_char_p, c_void_p, c_int, c_int, c_int, c_int, c_int, c_int]
dcamimg.DcamImgTiffSave8.restype = c_bool

# ============================================================================
# ¡ DcamImgGetLastError
# ---------------------------------------------------------------------------
# < Argument >		None
#
# < Return value > Error code.
#
# < Contents >	
#
# ============================================================================
dcamimg.DcamImgGetLastError.argtypes = []
dcamimg.DcamImgGetLastError.restype = c_uint32
