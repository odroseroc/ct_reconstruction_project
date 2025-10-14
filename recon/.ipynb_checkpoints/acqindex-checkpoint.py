import numpy as np
import tifffile as tfff
import matplotlib.pyplot as plt
from pathlib import Path, PurePosixPath, PureWindowsPath
import collections

# from imaging.img_utils import resolve_input_images
from recon import Sinogram, Projection

AcqisitionStep = collections.namedtuple('AcqisitionStep',['filepath','angle'])

class AcquisitionIndex():
    """
    Indexes all he images from a complete CT scan for easy access.

    Parameters
    ----------
    filepaths : list of str or Path
        List of paths to the acquisition image files.
    angles : np.ndarray
        1D array with the angles corresponding to each acquisition step.
    device : str, optional
        Name of the device used for acquisition. Default is 'cam'.
    steps : tuple
        Tuple of AcquisitionStep namedtuples, linking each filepath with its corresponding angle.
    """
    def __init__(self, filepaths, angles, device='cam'):
        self.filepaths = filepaths
        self.angles = angles
        self.device = device
        self.steps = tuple(AcqisitionStep(fp, angle) for fp, angle in zip(filepaths, angles))

    @classmethod
    def from_file(cls, metadata_file: str, device: str='cam', separator: str ="|"):
        """
        Load an acquisition index from a metadata.txt file
        """
        angles = []
        filepaths = []
        metadata_file = Path(metadata_file)
        parent_dir = metadata_file.parent
        with open(metadata_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or separator not in line:
                    continue

                cols = [c.strip() for c in line.split(separator)]
                if len(cols) >= 3:
                    try:
                        angles.append(float(cols[1]))
                        p = PureWindowsPath(cols[2])
                        filepaths.append(parent_dir/Path(p))
                    except ValueError:
                        pass
        return cls(filepaths=filepaths, angles=np.array(angles), device=device)

    def __getitem__(self, index: int):
        return self.steps[index]

    def create_sinogram(self, row: int, crop=None, max_projections=None, log_fn=print, log_freq=60) -> Sinogram:
        """
        Create a sinogram from the indexed acquisition images by extracting a specific row from each image.

        Parameters
        ----------
        row : int
            Row index to extract from each acquisition image.
        crop : tuple, optional
            Tuple specifying the (start, end) indices to crop the projections. Default is None (no cropping).
        max_projections : int, optional
            Maximum number of projections to include in the sinogram. Default is None (use all projections).
        log_fn : function, optional
            Function to use for logging messages. Default is print.
        log_freq : int, optional
            Frequency of logging progress messages. Default is 60.

        Returns
        -------
        Sinogram
            Sinogram object containing the extracted projections and corresponding angles.
        """
        projections = []
        log_fn(f"Creating sinogram from row {row} of {len(self.steps)} images...")
        for step in self.steps[:max_projections]:
            img = tfff.imread(step.filepath)
            if row < 0 or row >= img.shape[0]:
                raise ValueError(f"Row index {row} is out of bounds for image with shape {img.shape}.")
            if crop is not None:
                start, end = crop
                proj_values = img[row, start:end]
            else:
                proj_values = img[row, :]
            if len(projections) % log_freq == 0:
                log_fn(f"  Loaded {step.filepath.name}, angle={step.angle} deg, projection shape: {proj_values.shape}")
            projections.append(Projection(values=proj_values, angle=step.angle))
            del img
        log_fn(f"Sinogram creation complete. Created {len(projections)} projections.")
        return Sinogram.from_projections(projections)
