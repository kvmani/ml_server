# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS dev
COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt
COPY . .
ENV PYTHONPATH=/app/src
CMD ["python", "app.py"]

FROM base AS prod
COPY . .
RUN pip install --no-cache-dir --no-deps .
ENV PYTHONPATH=/app/src
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "ml_server.app.server:create_app()"]
