# Microstructural Analysis Web Application

A Flask-based web application for microstructural analysis, featuring super-resolution image enhancement and EBSD data cleanup tools.

## Features

### Super Resolution Tool
- Enhance microstructural images with 4x resolution improvement
- Advanced AI-powered detail enhancement
- Noise reduction and quality preservation
- Interactive image comparison slider
- Support for multiple image formats (PNG, JPG, JPEG, GIF, BMP, TIFF, WebP)

### EBSD Clean-Up Tool
- Process and clean EBSD data files
- Noise reduction in EBSD maps
- Grain boundary detection and enhancement
- Phase analysis and identification
- Support for standard EBSD file formats (.ang, .ctf, .cpr, .osc, .h5, .hdf5)
- Interactive before/after comparison slider

### General Features
- Modern, responsive user interface
- Drag-and-drop file upload
- Real-time image processing
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

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

3. Choose between Super Resolution or EBSD Clean-Up tools from the navigation menu.

4. Upload your files using the drag-and-drop interface or file browser.

5. View the results using the interactive comparison slider.

6. Download the processed results using the download button.

## Technical Details

- Built with Flask 3.0.2
- Uses Pillow for image processing
- Implements in-memory processing to avoid file storage
- Base64 encoding for image transfer
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