FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-test.txt
COPY . .
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "ml_server.app.microstructure_server:create_app()"]
