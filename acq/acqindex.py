import numpy as np
import tifffile as tfff
import matplotlib.pyplot as plt
from pathlib import Path, PurePosixPath, PureWindowsPath
import collections
import re

# from imaging.img_utils import resolve_input_images
from recon import Sinogram, Projection

AcquisitionStep = collections.namedtuple('AcqisitionStep',['angle','filepath'])

class AcquisitionIndex():
    """
    Indexes all he images from a complete CT scan for easy access.

    Parameters
    ----------
    filepaths : list of str or Path
        List of paths to the acq image files.
    angles : np.ndarray
        1D array with the angles corresponding to each acq step.
    device : str, optional
        Name of the device used for acq. Default is 'DahengCam'.
        The second available option is 'HamamatsuCCD'
    steps : tuple
        Tuple of AcquisitionStep namedtuples, linking each filepath with its corresponding angle.
    """
    def __init__(self,
                 filepaths,
                 angles,
                 device='DahengCam',
                 parent_dir=None,
                 metadata_file=None):
        self._filepaths = filepaths
        self._angles = angles
        self.device = device
        self.parent_dir = parent_dir
        self.metadata_file = metadata_file

    @classmethod
    def from_file(cls,
                  metadata_file: str,
                  device: str = 'DahengCam',
                  separator: str = ","):
        """
        Load an acq index from a metadata.txt file
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
        return cls(filepaths=filepaths, angles=np.array(angles), device=device, parent_dir=parent_dir, metadata_file=metadata_file)

    @classmethod
    def from_list(cls, acq_steps, meta_file, parent_dir, device="DahengCam"):
        angles = []
        filepaths = []
        for step in acq_steps:
            angles.append(step.angle)
            filepaths.append(step.filepath)
        return cls(filepaths=filepaths, angles=np.array(angles), parent_dir=parent_dir, metadata_file=meta_file, device=device)
    
    @classmethod
    def from_folder(cls, folder, step: float, device="DahengCam"):
        """
        Create an AcquisitionIndex from a folder containing TIF images whose filenames
        end with an integer (e.g. img_001.tif, proj01.tif, scan1.tif).

        Parameters
        ----------
        folder : str or Path
            Directory containing the TIF images.
        step : float
            Angular step between projections (angle = number_in_name * step)
        device : str
            Camera/device name (default: 'DahengCam')

        Returns
        -------
        AcquisitionIndex
        """
        folder = Path(folder)

        # Regex: capture number at the end of the filename before .tif
        number_regex = re.compile(r"(\d+)(?=\.[Tt][Ii][Ff])")

        filepaths = []
        angles = []

        for tif_path in sorted(folder.glob("*.tif")):
            m = number_regex.search(tif_path.name)
            if not m:
                continue  # skip if no number found

            n = int(m.group(1))  # extract number at end
            angle = n * step

            filepaths.append(tif_path)
            angles.append(angle)

        return cls(
            filepaths=filepaths,
            angles=np.array(angles, dtype=float),
            device=device,
            parent_dir=folder.parent,
            metadata_file=folder / Path("meta.txt")
        )

    def __getitem__(self, index: int):
        if isinstance(index, slice):
            return AcquisitionIndex(
                filepaths=self._filepaths[index],
                angles=self._angles[index],
                device=self.device,
                parent_dir=self.parent_dir,
                metadata_file=self.metadata_file
            )
        elif isinstance(index, int):
            return AcquisitionStep(self._angles[index], self._filepaths[index])
        else:
            raise TypeError(f"Invalid index type: {type(index)}")

    def __len__(self):
        return len(self._filepaths)

    def create_sinogram(self,
                        row: int,
                        crop=None,
                        max_projections: int = None,
                        log_fn=print,
                        log_freq=None) -> Sinogram:
        """
        Create a sinogram from the indexed acq images by extracting a specific row from each image.

        Parameters
        ----------
        row : int
            Row index to extract from each acq image.
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
        if log_freq is None:
            log_freq = np.floor(len(self._filepaths)/6)
        projections = []
        log_fn(f"Creating sinogram from row {row} of {len(self._filepaths)} images...")
        for step in self[:max_projections]:
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
