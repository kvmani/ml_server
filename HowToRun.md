# How to Run the Application

## Prerequisites

Before running the application, ensure you have the following installed:

1. **Python 3.8 or higher**
   - Download from [Python's official website](https://www.python.org/downloads/)
   - Verify installation: `python --version`

2. **pip (Python package installer)**
   - Usually comes with Python
   - Verify installation: `pip --version`

## Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/microstructure-analysis-flask.git
   cd microstructure-analysis-flask
   ```

2. **Create Virtual Environment**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the Flask Server**
   ```bash
   python app.py
   ```

2. **Access the Application**
   - Open your web browser
   - Navigate to: `http://127.0.0.1:5000`

## Using the Application

### Super Resolution Tool

1. **Upload an Image**
   - Click "Choose File" or drag and drop an image
   - Supported formats: PNG, JPG, JPEG, GIF, BMP, TIFF, WebP

2. **View Results**
   - Use the slider to compare original and enhanced images
   - Click "Download Enhanced Image" to save results

### EBSD Clean-Up Tool

1. **Upload EBSD Data**
   - Click "Choose File" or drag and drop an EBSD file
   - Supported formats: .ang, .ctf, .cpr, .osc, .h5, .hdf5

2. **Process Data**
   - Select processing options
   - Click "Process" to start analysis

3. **View Results**
   - Use the slider to compare original and processed maps
   - Download results using the download button

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port 5000
   # On Windows
   netstat -ano | findstr :5000
   
   # On macOS/Linux
   lsof -i :5000
   ```

2. **Missing Dependencies**
   ```bash
   # Reinstall requirements
   pip install -r requirements.txt
   ```

3. **Browser Issues**
   - Clear browser cache
   - Try a different browser
   - Check browser console for errors

### Getting Help

- Check the [Development Guide](DevelopmentGuide.md)
- Review the [README](README.md)
- Open an issue on GitHub

## Development Mode

For development purposes:

1. **Enable Debug Mode**
   - Set `DEBUG=True` in app.py
   - Auto-reload on code changes
   - Detailed error messages

2. **Access Debug Tools**
   - Debugger PIN in console
   - Interactive debugger in browser
   - Detailed error tracebacks

## Production Deployment

For production deployment:

1. **Security Settings**
   - Set `DEBUG=False`
   - Use production-grade server
   - Configure proper logging

2. **Performance Optimization**
   - Enable caching
   - Configure proper headers
   - Set up monitoring

## Support

For additional support:
- Check the documentation
- Open an issue on GitHub
- Contact the development team 