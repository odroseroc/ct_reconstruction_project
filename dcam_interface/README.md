# Hamamatsu DCamLib and DCamImg Python Interface

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

## Implementation Notes

The original `DCamLib` header file was not included in the CD provided with our hardware. 
As such, this Python wrapper is based on the header `DCamLibM2.h`, which was designed for 
a Windows XP-specific version of the library.

In cases where function names or constants differ from those in the `DCamLib` manual (included 
in the CD), we have adapted accordingly. Function names have been updated to match the manual 
where possible. Constant values not available in the headers were inferred from context and 
manual descriptions, but could not be independently verified.

**Caution:** This wrapper includes educated assumptions and manual mappings. Where such 
assumptions were made, comments are included directly in the code to indicate the adaptation. 
Use with care and validate on your specific hardware.
