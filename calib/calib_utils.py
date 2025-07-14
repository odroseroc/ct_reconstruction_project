import numpy as np
from skimage import io
from collections.abc  import Callable
from pathlib import Path
from typing import Union, List, Tuple
from imaging.img_utils import *

def create_master_dark(input_files: List[Path],
                       output_file: Union[str, Path] = './masterdark.tiff',
                       log_fn: Callable[[str],None] = print) -> np.ndarray:
    """
    Creates a master dark frame from a list of given images and exports it as
    an image.

    Also returns the master dark as an array which can be directly used in other scripts.

    Parameters
    ----------
    input_files: list[Path]
        List of paths to the dark frames from which the master wil be created.
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
    
    darkFrames = import_images(input_files)
    output_file = Path(output_file)
    log_fn("Creating master dark frame from "+str(len(darkFrames))+" uploaded images")
    master_dark = median_by_pixel(darkFrames)
    io.imsave(output_file, master_dark, check_contrast=False)
    log_fn("Master dark frame saved in "+str(output_file))
    return master_dark
