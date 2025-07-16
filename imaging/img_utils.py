import numpy as np
from skimage import io
from pathlib import Path
import glob
from typing import Union, List, Tuple
from collections.abc  import Callable

def import_images(paths: Union[List[str], str], log_fn: Callable = print) -> list[np.ndarray]:
    """
    Imports a list of images and loads them as NumPy arrays.
    
    Parameters
    ----------
    files : list of strings or string
        Can be a list of path-like strings , a single path-like string or a glob-like argument indicating the path of the files to be imported

    Returns
    -------
    List[np.ndarray]
        List of images loaded as arrays.
    """

    if isinstance(paths, str):
        paths = glob.glob(paths)

    paths = [Path(path) for path in paths] # Convert always to posix path for compatibility
    imgs = [io.imread(path) for path in paths]
    log_fn('Imported %d images'%len(paths))
    return [io.imread(path) for path in paths]

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

def normalize_to_mean(imgs: Union[np.ndarray, List[np.ndarray]]) -> List[np.ndarray]:
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