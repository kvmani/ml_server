# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS dev
COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt
COPY . .
CMD ["python", "app.py"]

FROM base AS prod
COPY . .
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "ml_server.app.server:create_app()"]
