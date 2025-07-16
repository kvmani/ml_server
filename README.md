# Microstructural Analysis Web Application

A Flask-based web application for microstructural analysis, featuring super-resolution image enhancement and EBSD data cleanup tools.

## Features

### Super Resolution Tool
- Process microstructural images through ML model
- Real-time image processing
- Interactive image comparison (original vs processed)
- Support for multiple image formats (PNG, JPG, JPEG, GIF, BMP, TIFF, WebP)
- ML model status checking

### EBSD Clean-Up Tool
- Process and clean EBSD data files
- Noise reduction in EBSD maps
- Grain boundary detection and enhancement
- Phase analysis and identification
- Support for standard EBSD file formats (.ang, .ctf, .cpr, .osc, .h5, .hdf5)
- Interactive before/after comparison

### Hydride Segmentation Tool
- Automatically segment hydrides in microstructure images
- Overlay results on original image
- Support for common image formats (PNG, JPG, JPEG, GIF, BMP, TIFF, WebP)

### General Features
- Modern, responsive user interface
- Drag-and-drop file upload
- Real-time ML model status checking
- In-memory processing (no file storage)
- User feedback system
- Cross-browser compatibility

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/microstructure-analysis-flask.git
cd microstructure-analysis-flask
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the ML model server:
```bash
python scripts/start_ml_model_service.py
```

2. Start the Flask application (in a separate terminal):
```bash
python app.py
```

3. Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

4. Choose between Super Resolution, EBSD Clean-Up or Hydride Segmentation tools from the navigation menu.

5. Upload your files using the drag-and-drop interface or file browser.

6. View the results using the interactive comparison slider.

7. Download the processed results using the download button.

## Configuration

Default settings are stored in `config.json`. Any value can be overridden at
runtime using environment variables. Variables use the prefix `APP_` and `__`
to separate nested keys. For example to change the port and ML model URL:

```bash
export APP_PORT=8080
export APP_SUPER_RESOLUTION__ML_MODEL__URL=http://localhost:6000/infer
```

Start the application after exporting any overrides.

## Technical Details

- Built with Flask
- Separate ML model server
- In-memory image processing
- Base64 encoding for image transfer
- Real-time ML model status checking
- Responsive design with Bootstrap 5
- Interactive UI components with vanilla JavaScript

## File Format Support

### Super Resolution
- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)
- BMP (.bmp)
- TIFF (.tiff)
- WebP (.webp)

### EBSD Clean-Up
- ANG (.ang)
- CTF (.ctf)
- CPR (.cpr)
- OSC (.osc)
- HDF5 (.h5, .hdf5)
### Hydride Segmentation
- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)
- BMP (.bmp)
- TIFF (.tiff)
- WebP (.webp)

## Testing

Run all tests using `pytest`:

```bash
pytest -q
```

The repository provides `pytest.ini` which sets `testpaths` to the `tests`
directory and excludes the `external/` path from collection. After cloning any
submodules, running the command above should only collect the tests inside the
`tests/` folder.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask web framework
- Pillow image processing library
- Bootstrap for the UI framework
- All contributors and users of the application 