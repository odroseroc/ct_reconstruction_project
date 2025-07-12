"""
log_utils.py

Auxilliar functions related with handling of state logs and messages. These allow to customize the behavior of the log (e.g. silence it or redirect it)-

This module is designed to be used as part of other functions or GUIs, where the output messages can be controlled from outside.
"""

def no_op(*args, **kwargs):
    """
    Empty function that does no operation.

    Commonly used as default funtion for 'log_fn' in functions that accept an optional logging argument, allowing state messages to be omitted silently if printinf is not desired.

    Parameters
    ----------
    *args : any type
        Ignored positional arguments.
    **kwargs : any type
        Ignored named arguments.
    """
    pass