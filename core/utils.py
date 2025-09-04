"""
Various utilities used in several modules.
"""
import numpy as np
from typing import Callable
from imaging.img_utils import import_images
from functools import wraps

def resolve_input_images(func: Callable) -> Callable:
    """
	Decorator that transforms an argument input_imgs into a list of np.ndarray.
	Allows input_img to be a list of arrays, a glob expression or a list of
	path-like strings.

	The decorated funtion must have input_imgs as its first argument
    """
	@wraps(func)
    def wrapper(input_imgs, *args, **kwargs):
	    match input_imgs:
	        case str() | [str(), *_]:
	            imgs = import_images(input_imgs)
	        case [np.ndarray(imgs)]:
	            imgs = input_imgs
	        case _:
	            raise TypeError('Input images must be provided as a list of arrays or path-like strings.')
	    return func(imgs, *args, **kwargs)
	return wrapper