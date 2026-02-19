# Custom Built Scanner for the Hard X-Rays Labotaroty ad KTH

**Status:** 🚧 *Under development*

This repository contains core utilities for a **custom-built Computed Tomography (CT) scanner** currently under construction at the **Hard X-ray Laboratory, KTH Royal Institute of Technology**.

The project provides tools for **image preprocessing**, **calibration**, and **reconstruction**, and is designed to be eventually integrated into the scanner’s user interface, developed in parallel by another team member.

---

## Current Features

### Imaging Utilities
- Import `.tiff` images from file paths or patterns
- Basic image manipulation (e.g., normalization, mean scaling, addition)

### Calibration Utilities
- Generate **dark frames**
- Generate **flat frames**

### Reconstruction Utilities
- Basic **backprojection** implementation 
  *(Filtering not yet implemented)*

---

## 🗺️ Project Roadmap (Planned)
- [ ] Add filtered backprojection
- [ ] Implement automated calibration workflows
- [ ] Integrate with GUI interface
- [ ] Add unit tests and CI workflows

---

## Contributing

This project is currently under internal development and is not open to public contributions at this time.

---

## License

To be determined.
