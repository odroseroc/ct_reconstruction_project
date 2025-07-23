# Hamamatsu DCamLib Python Interface

This folder contains a Python interface to the `DCamLib.dll` and `DCamImg.dll` dynamic libraries used to control some Hamamatsu imaging equipment from the early to mid 2000s. It wraps the original C API using `ctypes`, making it accessible and usable directly from Python.

In this project, we use the interface to control a digital radiography system: the C10819 Series, which includes a C10819-04 control module and an S10810 sensor unit.

## 📦 Contents

- `dcamlib.py` – Low-level wrapper for DCamLib.dll using ctypes.
- `dcamimg.py` – Low-level wrapper for DCamImg.dll, containing image-saving functions and extended image operations.
- `examples/` – Simple usage examples: initialize, capture, save images.
- `tests/` – Unit tests for your wrapper functions.

## 🔧 Requirements

- Windows (DCamLib and DCamImg are Windows DLL's)
- Python 3.x
- `DCamLib.dll` and `DCamImg.dll`must be available in your system path or current directory.
- All the equipment drivers should be installed.

## 🧪 Example Usage

```python
from dcam_interface import dcamlib

# Initialize camera
dcamlib.DcamInitialize()

# Capture image...
# Save image...

# Release resources
dcamlib.DcamUninitialize()