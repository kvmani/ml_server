# Microstructural Analysis Portal

A web-based platform for microstructural image analysis and enhancement, built with Flask and modern web technologies.

## Features

- Image upload via drag-and-drop or file selection
- Image enhancement with flip transformation (placeholder for future ML-based super-resolution)
- Interactive user interface with real-time preview
- Feedback system for user input
- Help and FAQ section
- Responsive design for all devices

## Project Structure

```
microstructure-analysis-flask/
├── app.py                # Main Flask application
├── config.yml           # Configuration file
├── requirements.txt     # Python dependencies
├── README.md           # Project documentation
├── apps/               # Application modules
│   └── super_resolution/
│       ├── __init__.py  # Blueprint initialization
│       ├── routes.py    # Route handlers
│       ├── templates/   # HTML templates
│       └── static/      # Static files (JS, CSS, images)
├── models/             # ML models (future use)
└── utilities/          # Shared utilities
```

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/microstructure-analysis-flask.git
cd microstructure-analysis-flask
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Development

### Adding New Features

1. Create a new module in the `apps` directory
2. Create a Blueprint for the new module
3. Register the Blueprint in `app.py`
4. Add routes, templates, and static files as needed

### Testing

Run tests using pytest:
```bash
pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Future Enhancements

- Integration of actual super-resolution ML models
- Database integration for feedback storage
- User authentication system
- Additional image processing features
- Advanced analysis tools

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For any queries or suggestions, please contact:
- Email: contact@microstructure.org 