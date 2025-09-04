import numpy as np
from skimage import io
from pathlib import Path
import glob
from typing import Union, List, Tuple
from collections.abc  import Callable
from core.log_utils import no_op
from functools import wraps

def import_images(paths: List[str] | str, 
                  log_fn: Callable[[str], None] = no_op) -> list[np.ndarray]:
    """
    Imports a list of images and loads them as NumPy arrays.
    
    Parameters
    ----------
    files : list of strings or string.
        Can be a list of path-like strings , a single path-like string or a glob-like argument indicating the path of the files to be imported

    Returns
    -------
    List[np.ndarray]
        List of images loaded as arrays.
    """

    if isinstance(paths, str):
        paths = glob.glob(paths)

    if not paths:
        raise FileNotFoundError("No files found matching the given path or pattern.")

    paths = [Path(path) for path in paths] # Convert always to posix path for compatibility
    imgs = [io.imread(path) for path in paths]
    log_fn('Imported %d image(s)'%len(paths))
    return imgs

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

def median_by_pixel(imgs: list[np.ndarray]) -> np.ndarray:
    """
    Determines the median value of a set of images, on a pixel by pixel basis.

    Parameters
    ----------
    imgs: list[np.ndarray]
        The images used to compute the median.

    Return
    ------
    np.ndarray
        An image whose pixels are the median values of the original images.
    """
    if not(all(im.shape==imgs[0].shape for im in imgs)):
        raise Exception('The images have different sizes.')

    original_shape = imgs[0].shape
    imgs_stack = np.vstack([im.reshape((1,-1)) for im in imgs])
    return np.median(imgs_stack, axis=0).reshape(original_shape)

def scale_to_mean(img: np.ndarray,
                  mean_value: float,
                  img_mean: float = None,
                  log_fn: Callable[[str],None] = no_op) -> np.ndarray:
    """
    Scales the values of an image such that its mean becomes mean_value.
    Allows to parse the mean of the image as argument. This avoids repetition
    if the mean of this image has been previously calculated.
    """
    if img_mean == None:
        img_mean = np.mean(img)
    log_fn('Image scaled to mean value '+str(mean_value))
    return img*(mean_value/img_mean)

def normalize_to_mean(imgs: np.ndarray | List[np.ndarray]) -> List[np.ndarray]:
    """
    Normalize one or more images by their mean intensity.

    Each image is divided by its mean pixel value. If the input is a single image, it is automatically wrapped into a list. If the mean of an image is zero, the image is returned unchanged.

    Parameters
    ----------
    imgs : np.ndarray or list of np.ndarray
        A single image or a list of images to normalize. Each image must be a NumPy array.

    Returns
    -------
    normalized_imgs : list of np.ndarray
        The normalized images, with each image divided by its mean.

    Notes
    -----
    If an image has a mean of zero, it is left unchanged to avoid division by zero.
    """
    if isinstance(imgs, np.ndarray):
        imgs = [imgs]
        
    means = [np.mean(img) for img in imgs]
    return [img/mean if mean != 0 else img for img, mean in zip(imgs, means)]