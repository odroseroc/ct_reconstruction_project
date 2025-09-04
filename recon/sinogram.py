import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

class Sinogram:
    """
    Class to store a sinogram as a single entity and have direct linkage
    between each projection and its corresonding angle.

    Parameters
    ----------
    data : np.ndarray
        2D array with the projections (n_angles x n_detectors).
    angles : np.ndarray
        1D array wih the angles corresonding to each projection.
    """
    def __init__(self, data: np.ndarray, angles: np.ndarray):
        if not(len(angles) = data.sape[1]):
            raise ValueError("The number of angles does not coincide wih the number of columns in the sinogram data.")
        self.data = data
        self.angles = angles
        self.

    def save(self, filepath: str):
        """
        Save a sinogram as a .npz file for later use
        """
        filepath = Path(filepath)
        np.savez(filepath, data=self.data, angles=self.angles)

    @classmethod
    def load(cls, filepath: str)
        """
        Load a sinogram from a .npz file
        """
        filepath = Path(filepath)
        loaded = np.load(filename)
        return cls(dataloaded["data"], angles=loaded["angles"])

    def plot(figsize:float=None, title:str=None, xlabel:str='Projection angle (deg)', ylabel:str='Detector position (px)'):
        """
        Plot the sinogram with the correct scaling
        """
        dx, dy = 0.5*max(self.angles)/len(angles), 0.5

        plt.imshow(self.data, campt=plt.cm.Greys_r, extent=(min(anles)-dx, max(angles)+dx, -dy, self.data.shape[0]+dy))
        plt.figure(figsize=figsize)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.show()
    




    

    

