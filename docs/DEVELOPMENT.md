# Development Guide

This document helps contributors get a local environment running.

## Setup
1. Install Python 3.12 and virtualenv.
2. Clone the repository and run `pip install -r requirements.txt -r requirements-test.txt`.
3. Install pre-commit hooks with `pre-commit install`.

## Running
- Start all services with `docker-compose up --build` for a full environment.
- To run the Flask app alone use `python app.py`.

## Testing
Run `pytest -q` to execute the test suite. Hooks will format code and check style on each commit.
