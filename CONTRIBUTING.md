# Contributing Guidelines

Thank you for considering a contribution! To keep the codebase consistent and
maintainable, please follow these rules:

1. **Coding style**
   - All new functions and public methods must include type hints and a concise
     docstring describing behaviour and return values.
   - Configuration values must be accessed via `ml_server.config.Config` and not
     hard coded.
   - UI elements such as icon sizes must read from configuration keys rather than
     using fixed values in templates or scripts.
   - Network calls using `requests` must specify a timeout and handle
     `RequestException` errors.

2. **Testing**
   - Add unit tests in the `tests/` directory following the existing pattern.
   - Run `pytest --cov=src` and ensure new code is covered.
   - Include the test results in your pull request description.

3. **Tooling**
   - Install development dependencies with `pip install -r requirements.txt -r
     requirements-test.txt` and run `pre-commit install` once.
   - Ensure `black`, `isort` and `flake8` all pass before committing.

4. **Repository hygiene**
   - Do not commit binary or model files (`*.pkl`, `*.h5`, `*.pt`, etc.).
   - Large data artifacts should be excluded via `.gitignore`.

### PDF Tools

The PDF merging and extraction utilities originate from a separate internal
repository. When modifying these tools, keep the code in
`ml_server/app/services/pdf_tools` in sync with the upstream project. Tests for
PDF functionality should accompany any changes.

Happy coding!
