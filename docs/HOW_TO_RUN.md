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
   git clone https://github.com/yourusername/ml_server.git
   cd ml_server
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

1. **Start the ML Model Server**
   ```bash
    # Open a terminal and run
    python scripts/start_ml_model_service.py
   
    # The server will start on port 5002
    # You should see: "ML model server started successfully!"
   ```

2. **Start the Flask Server**
   ```bash
   # Open another terminal and run
   python app.py
   
   # The application will start on port 5000
   ```

3. **Access the Application**
   - Open your web browser
   - Navigate to: `http://127.0.0.1:5000`

## Using the Application

### Super Resolution Tool

1. **Check ML Model Status**
   - The application automatically checks if the ML model is running
   - You'll see a warning if the model server is not available

2. **Upload an Image**
   - Click "Choose File" or drag and drop an image
   - Supported formats: PNG, JPG, JPEG, GIF, BMP, TIFF, WebP

3. **View Results**
   - Original and processed images will be displayed side by side
   - Use the download button to save the processed image

### EBSD Clean-Up Tool

1. **Upload EBSD Data**
   - Click "Choose File" or drag and drop an EBSD file
   - Supported formats: .ang, .ctf, .cpr, .osc, .h5, .hdf5

2. **Process Data**
   - Select processing options
   - Click "Process" to start analysis

3. **View Results**
   - Compare original and processed maps
   - Download processed data using the download button

## Troubleshooting

### Common Issues

1. **ML Model Server Not Running**
   ```bash
   # Check if port 5002 is in use
   # On Windows
   netstat -ano | findstr :5002
   
   # On macOS/Linux
   lsof -i :5002
   ```

2. **Flask Server Port Conflict**
   ```bash
   # Check if port 5000 is in use
   # On Windows
   netstat -ano | findstr :5000
   
   # On macOS/Linux
   lsof -i :5000
   ```

3. **Browser Issues**
   - Clear browser cache
   - Try a different browser
   - Check browser console for errors

### Getting Help

- Check the [Development Guide](DEVELOPMENT_GUIDE.md)
- Review the [README](README.md)
- Open an issue on GitHub

## Development Mode

For development purposes:

1. **Enable Debug Mode**
   - Debug mode is enabled by default in app.py
   - Auto-reload on code changes
   - Detailed error messages

2. **Access Debug Tools**
   - Debugger PIN in console
   - Interactive debugger in browser
   - Detailed error tracebacks

## Production Deployment

For production deployment:

1. **Security Settings**
   - Set `DEBUG=False` in app.py
   - Use production-grade server (e.g., Gunicorn)
   - Configure proper logging

2. **Environment Variables**
   - Configure ML model endpoint
   - Set appropriate host and port
   - Configure logging levels

## Support

For additional support:
- Check the documentation
- Open an issue on GitHub
- Contact the development team 