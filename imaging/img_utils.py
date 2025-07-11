import numpy as np
from skimage import io

def import_images(files: list[str]) -> list[np.ndarray]:
    """
    Imports a list of image files and returns them as np.ndarray's
    
    Parameters
    ----------
    files : list[str]
        List of paths of the image files

    Returns
    -------
    list[np.ndarray]
        The images as arrays
    """

    return [io.imread(path) for path in files]

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
    imgs = np.vstack([im.reshape((1,-1)) for im in imgs])
    return np.median(imgs, axis=0).reshape(original_shape)