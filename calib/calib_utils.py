import numpy as np
from skimage import io
from collections.abc  import Callable
from pathlib import Path
from typing import Union, List, Tuple
from imaging.img_utils import *
from core.log_utils import no_op

def create_master_dark(input_imgs: list[np.ndarray] | list[str] | str,
                       output_file: Union[str, Path] = './masterdark.tiff',
                       log_fn: Callable[[str],None] = print) -> np.ndarray:
    """
    Creates a master dark frame from a list of given images and exports it as
    an image.

    Also returns the master dark as an array which can be directly used in other scripts.

    Parameters
    ----------
    input_imgs: list of arrays, or list of path-like strings or path-like string
        List of dark frames from which the master dark frame will be created.
        Apart from arrays containing the images, this parameter can also receive
        a list of paths to the image files or a glob argument.
    output_file: str or Path, optional  
        Path where the master dark frame is to be saved. If not given, it will
        be saved as masterdark.tif in the same directory as the original frames.
    log_fn: Callable, optional
        Function to show status messages. Must accept a string. By default it
        is the print function.

    Return
    ------
    np.ndarray
        Array containing the master dark frame.
    """

    # Import images if necessary
    if (isinstance(input_imgs, list) and isinstance(input_imgs[0], str))\
    or isinstance(input_imgs, str):
        input_imgs = import_images(input_imgs)
    
    output_file = Path(output_file)

    log_fn("Creating master dark frame from "+str(len(input_imgs))+" uploaded images")
    masterdark = median_by_pixel(input_imgs)
    io.imsave(output_file, masterdark, check_contrast=False)
    log_fn("Master dark frame saved in "+str(output_file))
    return masterdark

def create_master_flat(input_imgs: list[np.ndarray] | list[str] | str,
                       masterdark: np.ndarray | str,
                       output_file: str = './masterflat.tiff',
                       log_fn: Callable[[str], None] = no_op) -> np.ndarray:
    """
    Creates a master flat frame and saves it to disk.
    The master flat frame is created from a list of flatframes and a master dark
    frame that has to be provided as parmeter to the function.

    Parameters
    ----------
    input_imgs: list of arrays, or list of path-like strings or path-like string
        List of flat frames from which the master flat frame will be created.
        Apart from arrays containing the images, this parameter can also receive
        a list of paths to the image files or a glob argument.
    masterdark: np.ndarray or path-like string
        Master dark frame (or path to it) that is subtracted from each flat
        frame to eliminate dark counts arising from the detector.
    output_file: str, optional
        Path-like string where the master flat frame will be stored in disk. If
        it is not provided, the file image will be saved as masterflat.tiff in
        the current directory.
    log_fn: Callable, optional
        Function to show status messages. Must accept a string. By default it
        is an empty function that does no operation.

    Returns
    -------
    np.ndarray
        The master flat frame (also saved to disk).
    """

    # Import images if necessary
    if (isinstance(input_imgs, list) and isinstance(input_imgs[0], str))\
    or isinstance(input_imgs, str):
        input_imgs = import_images(input_imgs)
    if isinstance(masterdark, str):
        masterdark, = import_images(masterdark)

    output_file = Path(output_file)

    log_fn("Creating master flat frame from "+str(len(input_imgs))+" uploaded images")
    subtracted_imgs = [img - masterdark for img in input_imgs] # subtract masterdark
    means = [np.mean(img) for img in subtracted_imgs]
    scaling_mean = np.amax(means)
    scaled_imgs = [scale_to_mean(img, scaling_mean, mean) for img, mean in zip(subtracted_imgs, means)] # scale all flat frames to a single mean
    masterflat = median_by_pixel(scaled_imgs)
    io.imsave(output_file, masterflat.astype(np.uint8), check_contrast=False)
    log_fn("Master flat frame saved in "+str(output_file))
    return masterflat
