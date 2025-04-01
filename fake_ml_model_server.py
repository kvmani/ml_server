from flask import Flask, request, send_file, jsonify
from PIL import Image
import io
import logging
import time
import os

app = Flask(__name__)

# === Logging Configuration ===
LOG_FILE = "ml_model_server.log"
os.makedirs("logs", exist_ok=True)
log_path = os.path.join("logs", LOG_FILE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# File Handler
file_handler = logging.FileHandler(log_path)
file_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

@app.route("/infer", methods=["POST"])
def infer():
    if 'image' not in request.files:
        logging.warning("No image uploaded in request.")
        return jsonify({"error": "No image uploaded"}), 400

    try:
        logging.info("Image received. Starting inference...")
        start_time = time.time()

        img = Image.open(request.files['image'])
        flipped = img.transpose(Image.FLIP_LEFT_RIGHT)

        img_io = io.BytesIO()
        flipped.save(img_io, 'PNG')
        img_io.seek(0)

        elapsed = time.time() - start_time
        logging.info(f"Inference complete. Time taken: {elapsed:.3f} seconds.")

        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        logging.error(f"Error during inference: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/", methods=["GET"])
def health():
    logging.info("Health check called.")
    return jsonify({"status": "ML model server running"}), 200

if __name__ == "__main__":
    logging.info("Starting ML model server on port 5002...")
    app.run(host="0.0.0.0", port=5002)
