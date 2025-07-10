import numpy as np
import matplotlib.pyplot as plt
from skimage.transform import radon
from scipy.ndimage import rotate

def sinogramFromPhantom(phantom: np.ndarray, max_angle: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Creates a sinogram from the image of a phantom. The sinogram has the same size as the original phantom. Primarily used to test the reconstruction algorithms in this project.

    Parameters
    ----------
    sinogram: np.ndarray
        Array of shape (n_detectors, n_angles). Each column corresponds to a projection at a specific angle.
        The number of detectors is typically equal to the height of the input image.
    max_angle: float
        Maximum angle (in degrees) of the sampled projections. To create the sinogram, the phantom is sampled to generate projections at evenly-distributed angles ranging from 0 degrees through max_angle.
	
    Return
    ------
    sinogram: np.ndarray
        Matrix of size (m,n) containing the sinogram generated from the phantom. Each column (n) corresponds to a single projection at a given angle.
    angles: np.ndarray
        Array of shape (n_angles,) containing the angles (in degrees) at which projections were taken.

    Note
    ----
    If the input image is not square, the number of detectors will correspond to the number of rows in the input image.
	"""
	angles = np.linspace(0., max_angle, max(phantom.shape), endpoint=False)
	sinogram = radon(phantom, theta=angles, circle=True)
	return sinogram, angles

def singleBackprojection(sinogram: np.ndarray, angles: np.ndarray, position: int) -> np.ndarray:
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

    Returns
    -------
    np.ndarray
    	2D array of the same shape as the original phantom image, representing the backprojection of a single projection at its original angle.
    """

    zeroDeg_backprojection = np.zeros(sinogram.shape) # The backprojection is first generated as if it comes from the 0° projection, then rotated at the correct angle
    angle = angles[position]
    zeroDeg_backprojection[:] = sinogram[:, position][np.newaxis, :]
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
        bp = singleBackprojection(sinogram, angles, position)
        backprojection_sum += bp
    return backprojection_sum

