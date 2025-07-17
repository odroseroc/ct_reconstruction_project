# Data Credits and Description

This directory contains image datasets used for development and testing of the reconstruction, calibration and image processing routines in this project. All data are grouped by source or context of acquisition.

## `richmond/` directory

All the images in this directory are from [Michael Richmond's educational repository](http://spiff.rit.edu/classes/), which hosts an excellent collection of astronomy and physics teaching materials. 

We have used several image files from his [PHYS 445 course data archive](http://spiff.rit.edu/classes/phys445/data/sep20_2003/) to test dark-field and flat-field correction algorithms. The original data remain unaltered except for format conversion when necessary (e.g., from `.fit` to `.tif`).

Please refer to his site for additional licensing or attribution details.

## `lab_images/` directory

This directory contains X-ray images acquired in the lab using our custom experimental setup. The goal of this dataset is to evaluate and benchmark our reconstruction algorithms on real, noisy data.

- **Camera**: Daheng Imaging MER2-1220
- **Scintillator**: [details under confirmation]
- **X-ray source**: Hamamatsu (exact model reference to be confirmed)
- **Setup**: The camera is directly pointed at the scintillator plate, which is exposed to the X-ray source. All images are grayscale and taken under varying exposure and intensity conditions.

Note: Please do not redistribute these lab images without permission, as they are part of ongoing research.

---

Let us know if you use this data in your own research or development. We’d be happy to connect!
