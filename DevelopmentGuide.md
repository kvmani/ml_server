# Development Guide

## Development Environment Setup

1. **Python Environment**
   - Python 3.8 or higher
   - Virtual environment (venv)
   - Required packages from requirements.txt

2. **IDE Setup**
   - Recommended: VS Code or PyCharm
   - Python extension
   - Flask extension
   - Git integration

3. **Code Style**
   - Follow PEP 8 guidelines
   - Use meaningful variable and function names
   - Add docstrings to functions and classes
   - Keep functions focused and single-purpose

## Project Structure

```
microstructure-analysis-flask/
├── static/
│   ├── css/           # CSS styles
│   ├── js/            # JavaScript files
│   └── images/        # Static images
├── templates/         # HTML templates
├── app.py            # Main Flask application
├── fake_ml_model_server.py  # Temporary ML model server
├── requirements.txt   # Python dependencies
├── feedback.json     # User feedback storage
└── README.md         # Project documentation
```

## Development Workflow

1. **Starting Development**
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/microstructure-analysis-flask.git
   cd microstructure-analysis-flask

   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Running the Application**
   ```bash
   # Start the ML model server (in a separate terminal)
   python fake_ml_model_server.py

   # Start the Flask application (in another terminal)
   python app.py
   ```

3. **Making Changes**
   - Create a new branch for your feature
   - Make your changes
   - Test thoroughly
   - Submit a pull request

## Code Organization

### Flask Application (app.py)
- Route handlers for web interface
- ML model communication
- Error handling and validation
- Feedback system

### ML Model Server (fake_ml_model_server.py)
- Image processing endpoints
- Health check endpoint
- Logging configuration

### Templates
- Base template (base.html) for common elements
- Tool-specific templates extend base.html
- Keep JavaScript in separate files

### Static Files
- CSS in static/css/
- JavaScript in static/js/
- Images in static/images/

## Best Practices

1. **Error Handling**
   - Check ML model availability
   - Validate file formats
   - Provide user-friendly error messages

2. **Security**
   - Validate all user inputs
   - Use in-memory processing
   - Implement proper error handling

3. **Performance**
   - Process images in memory
   - Efficient ML model communication
   - Base64 encoding for image transfer

4. **Testing**
   - Test ML model connectivity
   - Verify image processing
   - Check error scenarios
   - Run the full suite with `pytest -q`. The `pytest.ini` configuration
     collects tests from the `tests/` directory and ignores anything in
     `external/`.

## Deployment

1. **Production Setup**
   - Configure ML model server
   - Set up proper logging
   - Configure security headers

2. **Environment Variables**
   - ML model endpoint configuration
   - Debug settings
   - Logging configuration

## Troubleshooting

1. **Common Issues**
   - ML model connection errors
   - Image processing failures
   - File format validation

2. **Debugging**
   - Check ML model status
   - Verify request/response flow
   - Monitor server logs

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [Bootstrap Documentation](https://getbootstrap.com/docs/)
- [Python Style Guide](https://www.python.org/dev/peps/pep-0008/) 