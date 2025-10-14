import numpy as np
from skimage import io
from skimage.transform import rescale
from skimage.util import img_as_uint
from pathlib import Path, PureWindowsPath, PurePosixPath
import glob
from typing import Union, List, Tuple
from collections.abc  import Callable
from functools import wraps
from numpy.typing import NDArray
import tifffile as tfff
from datetime import datetime
# Imports from he project
from core.log_utils import no_op
from recon import AcquisitionIndex

def import_images(paths: List[str] | str, 
                  log_fn: Callable[[str], None] = no_op) -> list[np.ndarray]:
    """
    Imports a list of images and loads them as NumPy arrays.
    
    Parameters
    ----------
    files : list of strings or string.
        Can be a list of path-like strings , a single path-like string or a glob-like argument indicating the path of the files to be imported

    Returns
    -------
    List[np.ndarray]
        List of images loaded as arrays.
    """

    if isinstance(paths, str):
        paths = glob.glob(paths)

    if not paths:
        raise FileNotFoundError("No files found matching the given path or pattern.")

    paths = [Path(path) for path in paths] # Convert always to posix path for compatibility
    imgs = [io.imread(path) for path in paths]
    log_fn('Imported %d image(s)'%len(paths))
    return imgs

def resolve_input_images(func: Callable) -> Callable:
    """
    Decorator that transforms an argument input_imgs into a list of np.ndarray.
    Allows input_img to be a list of arrays, a glob expression or a list of
    path-like strings.

    The decorated funtion must have input_imgs as its first argument
    """
    @wraps(func)
    def wrapper(input_imgs, *args, **kwargs):
        match input_imgs:
            case str() | [str(), *_]:
                imgs = import_images(input_imgs)
            case [np.ndarray(imgs)]:
                imgs = input_imgs
            case _:
                raise TypeError('Input images must be provided as a list of arrays or path-like strings.')
        return func(imgs, *args, **kwargs)
    return wrapper

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

def scale_to_mean(img: np.ndarray,
                  mean_value: float,
                  img_mean: float = None,
                  log_fn: Callable[[str],None] = no_op) -> np.ndarray:
    """
    Scales the values of an image such that its mean becomes mean_value.
    Allows to parse the mean of the image as argument. This avoids repetition
    if the mean of this image has been previously calculated.
    """
    if img_mean == None:
        img_mean = np.mean(img)
    log_fn('Image scaled to mean value '+str(mean_value))
    return img*(mean_value/img_mean)

def normalize_to_mean(imgs: NDArray | List[NDArray]) -> List[NDArray]:
    """
    Normalize one or more images by their mean intensity.

    Each image is divided by its mean pixel value. If the input is a single image, it is automatically wrapped into a list. If the mean of an image is zero, the image is returned unchanged.

    Parameters
    ----------
    imgs : npt.NDArray or list of npt.NDArray
        A single image or a list of images to normalize. Each image must be a NumPy array.

    Returns
    -------
    normalized_imgs : list of npt.NDArray
        The normalized images, with each image divided by its mean.

    Notes
    -----
    If an image has a mean of zero, it is left unchanged to avoid division by zero.
    """
    if isinstance(imgs, np.ndarray):
        imgs = [imgs]
        
    means = [np.mean(img) for img in imgs]
    return [img/mean if mean != 0 else img for img, mean in zip(imgs, means)]

def crop_image(img: NDArray,
               rows_range: Tuple = None,
               cols_range: Tuple = None,
               log_fn=no_op) -> NDArray:
    if cols_range is None and rows_range is None:
        log_fn('No cols or rows specified')
        return img
    imshape = img.shape
    if cols_range is None:
        cols_range = (0,imshape[1])
    if rows_range is None:
        rows_range = (0,imshape[0])
    log_fn(f'Cropping image to {rows_range},{cols_range}')
    return img[rows_range[0]:rows_range[1], cols_range[0]:cols_range[1]]

def copy_metadata_header(file, sart_line=3):
    # By default, the metadata file contains two lines containing the name of the acquisition and te date of creation, but metadata files created with preliminary versions of this code may differ. Please verify the metadata file.
    file=Path(file)
    header_lines = []

    with open(file,'r') as f:
        for i, line in enumerate(f):
            if i < sart_line:
                continue
            if line.strip().startswith('#'):
                break
            header_lines.append(line)
    return header_lines

def write_metadata_file(metadata_path:str,
                        angles:NDArray,
                        filepaths: List[str],
                        header:str,
                        message:str):
    with open(metadata_path, 'w') as f:
        f.write(message)
        f.write(f"Date of creation: {datetime.today().strftime('%Y-%m-%d')}\n")
        f.write(f"============================================================\n")
        f.writelines(header)
        f.write(f"============================================================\n")
        f.write("#,angle,filepath\n")
        for idx, (pf, ang) in enumerate(zip(filepaths, angles)):
            f.writelines(f"{idx},{ang},{pf}\n")


def crop_acquisition(acq: AcquisitionIndex,
                     outdir: str,
                     rows_range: Tuple = None,
                     cols_range: Tuple = None,
                     preffix: str = None,
                     verbose_fn: Callable[[str],None] = no_op,
                     log_fn: Callable[[str],None] = no_op) -> AcquisitionIndex:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    new_filepaths = []
    new_angles = []
    for step in acq:
        img =  tfff.imread(step.filepath)
        cropped = crop_image(img, rows_range, cols_range, verbose_fn)
        filename = preffix + step.filepath.name
        outfile = outdir / filename
        tfff.imwrite(outfile, cropped)
        new_filepaths.append(PureWindowsPath(outfile.name))
        new_angles.append(step.angle)
        del img

    # Save new metadata file
    metadata_path = outdir / 'metadata.txt'
    old_header = copy_metadata_header(acq.metadata_file)
    message = f"Croped images to size {rows_range[1]-rows_range[0]}, {cols_range[1]-cols_range[0]}\n"
    write_metadata_file(metadata_path, new_angles, new_filepaths, old_header, message)

    log_fn(f"Images in the acquisition were cropped to size {rows_range[1]-rows_range[0]}, {cols_range[1]-cols_range[0]}")

    paths_for_index = []
    for fp in new_filepaths:
        paths_for_index.append(Path(outdir / fp.name))
    return AcquisitionIndex(filepaths=paths_for_index,
                            angles=np.array(new_angles),
                            device=acq.device,
                            parent_dir=outdir,
                            metadata_file=metadata_path)

def rescale_acquisition(acq: AcquisitionIndex,
                        outdir: str,
                        scale: float = 1,
                        preffix: str = None,
                        verbose_fn: Callable[[str], None] = no_op,
                        log_fn: Callable[[str], None] = no_op,
                        ) -> AcquisitionIndex:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    new_filepaths = []
    new_angles = []
    for step in acq:
        img = tfff.imread(step.filepath)
        rescaled_raw = rescale(img, scale, anti_aliasing=True)
        rescaled = img_as_uint(rescaled_raw)
        filename = preffix + step.filepath.name
        outfile = outdir / filename
        tfff.imwrite(outfile, rescaled)
        new_filepaths.append(PureWindowsPath(outfile.name))
        new_angles.append(step.angle)
        verbose_fn(f"{filename} rescaled. Saved at {outfile}")
        del img

    # Save new metadata file
    metadata_path = outdir / 'metadata.txt'
    old_header = copy_metadata_header(acq.metadata_file)
    message = f"Rescaled images to size {scale}, {scale}\n"
    write_metadata_file(metadata_path, new_angles, new_filepaths, old_header, message)

    log_fn(
        f"Images in the acquisition were rescaled to size {rescaled.shape}\n")

    paths_for_index = []
    for fp in new_filepaths:
        paths_for_index.append(Path(outdir / fp.name))
    return AcquisitionIndex(filepaths=paths_for_index,
                            angles=np.array(new_angles),
                            device=acq.device,
                            parent_dir=outdir,
                            metadata_file=metadata_path)


