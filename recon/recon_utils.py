import numpy as np
import matplotlib.pyplot as plt
from skimage.transform import radon
from scipy.ndimage import rotate
from collections.abc  import Callable
from core.log_utils import no_op

def sinogram_from_slice(slice: np.ndarray, max_angle: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Creates a sinogram from the image of a slice. The sinogram has the same size as the original image. Primarily used to test the reconstruction algorithms in this project.

    Parameters
    ----------
    slice: np.ndarray
        Matrix of size (m,n) containing the image of a single slice.
    max_angle: float
        Maximum angle (in degrees) of the sampled projections. To create the sinogram, the slice is sampled to generate projections at evenly-distributed angles ranging from 0 degrees through max_angle.
	
    Return
    ------
    sinogram: np.ndarray
        Matrix of size (m,n) containing the sinogram generated from the slice. Each column (n) corresponds to a single projection at a given angle.
    angles: np.ndarray
        Array of shape (n_angles,) containing the angles (in degrees) at which projections were taken.

    Note
    ----
    If the input image is not square, the number of detectors will correspond to the number of rows in the input image.
	"""
    angles = np.linspace(0., max_angle, max(slice.shape), endpoint=False)
    sinogram = radon(slice, theta=angles, circle=True)
    return sinogram, angles

def single_backprojection(sinogram: np.ndarray, angles: np.ndarray, position: int, log_fn: Callable[[str], None] = print) -> np.ndarray:
    """
    Returns the backprojection (at the correct angle) of a single projection from a sinogram

    Parameters
    ----------
    sinogram : np.ndarray
        Matrix of size (n,m) containing the sinogram
    angles : np.ndarray
        Array containing the angles corresponding to each projection
    position : int
        The position of the pixel column within the sinogram containing the 
        desired projection.
    log_fn: Callable, optional
        Function to show status messages. Must accept a string. By default it uses print.

    Returns
    -------
    np.ndarray
    	2D array of the same shape as the original slice image, representing the backprojection of a single projection at its original angle.
    """

    zeroDeg_backprojection = np.zeros(sinogram.shape) # The backprojection is first generated as if it comes from the 0° projection, then rotated at the correct angle
    angle = angles[position]
    zeroDeg_backprojection[:] = sinogram[:, position][np.newaxis, :]
    log_fn(f'Backprojecting position {position} at {angle:.3f}°')
    return rotate(zeroDeg_backprojection, angle, reshape=False, mode='nearest')

def backprojection(sinogram: "array_like", angles: "array_like") -> np.array:
    """
    Returns the backprojection summation image of a sinogram

    Parameters
    ----------
    sinogram : array_like
        Matrix of size (n,m) containing the sinogram
    angles : array_like
        Array containing the angles corresponding to each projection

    Returns
    -------
    np.array
        The backprojection summation (no filter)
    """

    backprojection_sum = np.zeros(sinogram.shape)
    for position in range(angles.size):
        bp = single_backprojection(sinogram, angles, position, log_fn=no_op)
        backprojection_sum += bp
    return backprojection_sum


