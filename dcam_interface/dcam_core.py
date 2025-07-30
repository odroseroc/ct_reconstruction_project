"""
dcam_core.py

Core functionality for interacting with the DCAM (Digital Camera) system.

This module provides high-level, user-friendly functions that abstract and simplify
the interaction with the lower-level `dcamlib` and `dcamimg` libraries. It is designed
to serve as the main interface for camera control, image acquisition, and basic processing.

All functions in this module are intended to be used by higher-level scripts or GUIs
that require a clean and Pythonic API to the DCAM system.

Examples
--------
>>> 
>>> 

"""
import ctypes as ct
from core.utils import no_op
from dcam_interface.dcamlib import *
from dcam_interface.dcamimg import *
from dcam_interface.constants import *
from functools import wraps # Auxilliar decorator to preserve identity of decorated functions

def _dcam_check_status(func):
    """
    Decorator to automate the status check of a DCam function call.
    If the function fails, it raises an exception with the error code and message.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        success = func(*args, **kwargs)
        if not success:
            # In the original function, the return value of DcamGetLastError() is a DWORD (uint32), but thanks to the dcamlib.py wrapper, we are able to catch the result of this function as a normal Python int.
            err_code = DcamGetLastError()
            raise RuntimeError(f'{func.__name__} failed with error code: {err_code} - {RUNSTATUS_DICT.get(err_code, f"Unknown error")}')
        return success
    return wrapper

def _make_dcam_voidfn(dll:ctypes.WinDLL, func_name: str):
    """
    Create a function that calls a void function from the DLL and provides automatic status verification via the _dcam_check_status decorator.
    """
    dcam_funct = getattr(dll, func_name)
    @_dcam_check_status
    def decorated_function():
        return dcam_func()

def _make_dcam_getter(dll:ctypes.WinDLL, func_name: str, ctype):
    """
    Create a function that gets a value by calling a DcamGet* function from the DLL and provides automatic 
    """
    pass

#==============================================================
# Re-implementation of the DCam functions to enable automatic execution-status check. Every function is decorated with _dcam_check_status so that they automatically raise RuntimeError with the appropriate error code and message.
#
# All the functions retain the same signature as in the python C-wrappers, but the status check is made automatically. Please refer to the wrappers dcamlib.py and dcamimg.py, and to the DLL manuals for more information.
#==============================================================

dcam_initialize = _make_dcam_voidfn(dcamimg_dll, "DcamInitialize")

dcam_uninitialize = _make_dcam_voidfn(dcamlib_dll, "DcamUninitialize")

dcam_open = _make_dcam_voidfn(dcamlib_dll, "DcamOpen")

dcam_close = _make_dcam_voidfn(dcamlib_dll, "DcamClose")


