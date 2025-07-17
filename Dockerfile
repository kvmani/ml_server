FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-test.txt config.json ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-test.txt
COPY . .
CMD ["python", "app.py"]
