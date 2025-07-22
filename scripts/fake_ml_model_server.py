import io
import logging
import logging.handlers
import os
import time

from flask import Flask, jsonify, request, send_file
from PIL import Image, ImageEnhance, ImageFilter

app = Flask(__name__)

# Logging setup
LOG_FILE = "ml_model_server.log"
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, LOG_FILE)

logger = logging.getLogger("FakeSuperResLogger")
logger.setLevel(logging.INFO)
logger.propagate = False
if logger.hasHandlers():
    logger.handlers.clear()

console_handler = logging.StreamHandler()
file_handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=10485760, backupCount=5)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


@app.route("/infer", methods=["POST"])
def infer():
    if "image" not in request.files:
        logger.warning("No image uploaded.")
        return jsonify({"error": "No image uploaded"}), 400

    try:
        uploaded_file = request.files["image"]
        filename = uploaded_file.filename.lower().strip()

        logger.info(f"Image received: {filename}")
        start_time = time.time()

        # ✅ Return fixed enhanced output if special input image is uploaded
        if filename == "noise_blur_image.png":
            fixed_path = os.path.join(
                app.root_path, "static", "fixed_outputs", "Clear_Neat_image.png"
            )
            if os.path.exists(fixed_path):
                logger.info("Matched special case — returning Clear_Neat_image.png")
                return send_file(fixed_path, mimetype="image/png", as_attachment=False)
            else:
                logger.error("Fixed output image missing!")
                return jsonify({"error": "Fixed enhanced image not found."}), 500

        # === Generic Fake Super-Resolution Enhancement ===
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Step 1: Denoising
        img = img.filter(ImageFilter.MedianFilter(size=3))

        # Step 2: Sharpening
        for _ in range(2):
            img = img.filter(ImageFilter.SHARPEN)

        # Step 3: Contrast & Brightness Boost
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Brightness(img).enhance(1.1)

        # Step 4: Upscaling
        img = img.resize((img.width * 1, img.height * 1), Image.LANCZOS)

        # Step 5: Final polish
        img = img.filter(ImageFilter.DETAIL)

        # Save to memory
        img_io = io.BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)

        duration = time.time() - start_time
        logger.info(f"Enhanced image generated in {duration:.2f} sec")

        return send_file(img_io, mimetype="image/png", as_attachment=False)

    except Exception as e:
        logger.error(f"Error in super-resolution logic: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "message": "Fake ML model is running"}), 200

@app.route("/", methods=["GET"])
def root_alias():
    return jsonify({"status": "healthy", "message": "Fake ML model is running"}), 200


if __name__ == "__main__":
    logger.info("Starting fake super-resolution server on port 5002...")
    app.run(host="0.0.0.0", port=5002)
