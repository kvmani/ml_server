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
    """
    Temporary ML model endpoint that flips images.
    This will be replaced with actual ML model in the future.
    """
    if 'image' not in request.files:
        logging.warning("No image uploaded in request.")
        return jsonify({"error": "No image uploaded"}), 400

    try:
        logging.info("Image received. Starting inference...")
        start_time = time.time()

        # Read and process the image
        img = Image.open(request.files['image'])
        
        # Convert RGBA/P images to RGB
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Temporary ML logic (image flipping)
        # This will be replaced with actual ML model processing
        processed_img = img.transpose(Image.FLIP_LEFT_RIGHT)

        # Save the processed image
        img_io = io.BytesIO()
        processed_img.save(img_io, format='PNG')
        img_io.seek(0)

        elapsed = time.time() - start_time
        logging.info(f"Processing complete. Time taken: {elapsed:.3f} seconds")

        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        logging.error(f"Error during processing: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "ML model server is running"}), 200

if __name__ == "__main__":
    port = 5002
    logging.info(f"Starting ML model server on port {port}")
    app.run(host="0.0.0.0", port=port)
