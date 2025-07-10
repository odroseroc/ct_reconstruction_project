"""
fit_to_tif.py

A small CLI tool to convert a single .fit or .fits file to a .tif image for visualization and further processing.

Usage:
    python convert_single_fits.py input_file.fit [--output_file output.tif]

Arguments:
    input_file : str
        Path to the input .fit or .fits file.
    output_file : str, optional
        Path to save the resulting .tif file. If not provided, the output will use the same base name.

This script normalizes the pixel values to [0, 1] for better visualization.
"""

import argparse
from pathlib import Path

from astropy.io import fits
from skimage.io import imsave
import numpy as np

def convert_fits(input_file, output_file=None):
    input_file = Path(input_file)

    if not input_file.exists():
        raise FileNotFoundError(f"File not found: {input_file}")

    if output_file is None:
        output_file = input_file.with_suffix(".tif")
    else:
        output_file = Path(output_file)

    # Read and normalize FITS data
    data = fits.getdata(input_file)
    data = data.astype(np.float32)
    data -= np.min(data)
    if np.max(data) != 0:
        data /= np.max(data)

    imsave(output_file, data)
    print(f"Converted: {input_file.name} → {output_file.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a FITS file to TIF format.")
    parser.add_argument("input_file", help="Path to the input .fit or .fits file")
    parser.add_argument("--output_file", help="Optional: output .tif path (default: same name)")

    args = parser.parse_args()
    convert_fits(args.input_file, args.output_file)