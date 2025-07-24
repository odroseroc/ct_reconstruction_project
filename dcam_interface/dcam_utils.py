from dcamlib import *
from dcamimg import *
from constants import *
from functools import wraps

def check_status(func):
    """
    Decorator to automate the status check of a DCam function call.
    If the function fails, it raises an exception with the error code and message.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not func(*args, **kwargs):
            dwErrorCode = dcamimg.DcamGetLastError()
            code = dwErrorCode.value if hasattr(dwErrorCode, 'value') else dwErrorCode
            message = RUNSTATUS_DICT.get(code, f"Unrecognized error code: {code}")
            raise Exception(f"DCam function '{func.__name__}' failed with error code {code}: {message}")
        return None
    return wrapper
