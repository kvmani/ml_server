import base64
import io
import logging
import logging.handlers
import os
import time

from flask import Flask, jsonify, request
from PIL import Image, ImageDraw

app = Flask(__name__)

# === Logging Configuration ===
LOG_FILE = "ebsd_model_server.log"
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, LOG_FILE)

# Set up logger
logger = logging.getLogger("EbsdLogger")
logger.setLevel(logging.INFO)
logger.propagate = False

# Clear old handlers (useful for interactive/debug mode)
if logger.hasHandlers():
    logger.handlers.clear()

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

file_handler = logging.handlers.RotatingFileHandler(
    log_path, maxBytes=10485760, backupCount=5
)
file_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# === Routes ===


@app.route("/", methods=["GET"])
def health():
    logger.info("Health check received.")
    return jsonify({"status": "EBSD model running"}), 200


@app.route("/infer", methods=["POST"])
def infer():
    if "ebsd_file" not in request.files:
        logger.warning("No EBSD file received.")
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["ebsd_file"]
    logger.info("EBSD file received. Starting dummy processing...")

    start_time = time.time()

    # Create dummy original map
    dummy_map = Image.new("RGB", (800, 600), color="white")
    draw = ImageDraw.Draw(dummy_map)
    for i in range(0, 800, 50):
        for j in range(0, 600, 50):
            color = (
                int(128 + (i * j) % 128),
                int(128 + (i + j) % 128),
                int(128 + ((i - j) * 2) % 128),
            )
            draw.polygon([(i, j), (i + 50, j + 25), (i + 25, j + 50), (i - 25, j + 25)], fill=color)

    orig_io = io.BytesIO()
    dummy_map.save(orig_io, format="PNG")
    original_b64 = base64.b64encode(orig_io.getvalue()).decode()

    # Create enhanced map
    enhanced_map = dummy_map.copy()
    draw = ImageDraw.Draw(enhanced_map)
    for i in range(0, 800, 50):
        for j in range(0, 600, 50):
            color = (
                int(160 + (i * j) % 96),
                int(160 + (i + j) % 96),
                int(160 + ((i - j) * 2) % 96),
            )
            draw.polygon([(i, j), (i + 50, j + 25), (i + 25, j + 50), (i - 25, j + 25)], fill=color)

    enhanced_io = io.BytesIO()
    enhanced_map.save(enhanced_io, format="PNG")
    enhanced_b64 = base64.b64encode(enhanced_io.getvalue()).decode()

    # ✅ Save enhanced map for download
    os.makedirs("tmp", exist_ok=True)
    enhanced_map.save("tmp/enhanced_ebsd_map.png", format="PNG")
    logger.info("Enhanced EBSD map saved to tmp/enhanced_ebsd_map.png")

    duration = time.time() - start_time
    logger.info(f"Processing complete. Time taken: {duration:.3f} seconds")

    return jsonify(
        {
            "success": True,
            "original_map": f"data:image/png;base64,{original_b64}",
            "enhanced_map": f"data:image/png;base64,{enhanced_b64}",
        }
    )


if __name__ == "__main__":
    logger.info("Starting EBSD fake model server on port 5003...")
    app.run(port=5003)
