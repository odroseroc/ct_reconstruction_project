import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import collections 

Projection = collections.namedtuple('Projection',['values','angle'])

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
    projections : tuple
        Tuple of namedtuples, each containing the values of a projection and its corresponding angle. Used for implementation of __getitem__ method.
    """
    def __init__(self, data: np.ndarray, angles: np.ndarray):
        if data.ndim != 2:
            raise ValueError("`data` must be 2D (n_angles x n_detectors or n_detectors x n_angles).")
        if not(len(angles) == data.shape[1]):
            raise ValueError("The number of angles does not coincide wih the number of columns in the sinogram data.")
        self.data = data
        self.angles = angles
        self.projections = tuple(Projection(values, angle) for values, angle in zip(data.T, angles))

    def save(self, filepath: str):
        """
        Save a sinogram as a .npz file for later use
        """
        filepath = Path(filepath)
        np.savez(filepath, data=self.data, angles=self.angles)

    @classmethod
    def load(cls, filepath: str):
        """
        Load a sinogram from a .npz file
        """
        filepath = Path(filepath)
        loaded = np.load(filename)
        return cls(data=loaded["data"], angles=loaded["angles"])

    def plot(self, title:str=None, xlabel:str='Projection angle (deg)', ylabel:str='Detector position (px)'):
        """
        Plot the sinogram with the correct scaling
        """
        dx, dy = 0.5*max(self.angles)/max(self.data.shape), 0.5

        # plt.figure(figsize=figsize)
        plt.imshow(self.data, cmap=plt.cm.Greys_r, extent=(min(self.angles)-dx, max(self.angles)+dx, -dy, self.data.shape[0]+dy), aspect='auto')
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.show()
    
    def __len__(self):
        """Special method that returns the number of projections in the sinogram"""
        return len(self.angles)

    def __getitem__(self, position):
        """This special method returns a tuple containing the projection at cerain position and the angle at which it was taken"""
        return self.projections[position]

if __name__ == "__main__":
    pass
    

    

