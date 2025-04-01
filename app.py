from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import os
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw
import io
from datetime import datetime, timedelta
import json
import shutil
import uuid
import threading
import time
import base64
import requests  # NEW: For proxying to ML model

app = Flask(__name__)

# Configuration
TEMP_FOLDER = os.path.join('static', 'temp')
app.config['UPLOAD_FOLDER'] = os.path.join(TEMP_FOLDER, 'uploads')
app.config['ENHANCED_FOLDER'] = os.path.join(TEMP_FOLDER, 'enhanced')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.secret_key = os.urandom(24)

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ENHANCED_FOLDER'], exist_ok=True)

# Constants
CLEANUP_INTERVAL = 3600  # in seconds
FILE_EXPIRY = 24  # in hours
FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feedback.json')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
ALLOWED_EBSD_EXTENSIONS = {'ang', 'ctf', 'cpr', 'osc', 'h5', 'hdf5'}

# ML model endpoint (temporary flip-based)
ML_MODEL_URL = "http://localhost:5002/infer"

# Initialize feedback file
if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump({'feedback': []}, f)

# Background thread for cleanup
def cleanup_old_files():
    while True:
        try:
            now = datetime.now()
            for folder in [app.config['UPLOAD_FOLDER'], app.config['ENHANCED_FOLDER']]:
                for fname in os.listdir(folder):
                    path = os.path.join(folder, fname)
                    if datetime.fromtimestamp(os.path.getctime(path)) < now - timedelta(hours=FILE_EXPIRY):
                        os.remove(path)
        except Exception as e:
            app.logger.error(f"Cleanup error: {str(e)}")
        time.sleep(CLEANUP_INTERVAL)

cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def generate_unique_filename(original_filename):
    ext = os.path.splitext(original_filename)[1]
    return f"{uuid.uuid4().hex}{ext}"

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/help_faq')
def help_faq():
    return render_template('help_faq.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        rating = int(request.form.get('rating'))
        feedback_text = request.form.get('feedback')

        if not all([name, email, rating, feedback_text]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        feedback_data = {
            'name': name,
            'email': email,
            'rating': rating,
            'feedback': feedback_text,
            'date': datetime.now().isoformat(),
            'page': request.referrer
        }

        with open(FEEDBACK_FILE, 'r+') as f:
            data = json.load(f)
            data['feedback'].insert(0, feedback_data)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Feedback error: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/super_resolution', methods=['GET', 'POST'])
def super_resolution():
    if request.method == 'POST':
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image uploaded'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No image selected'}), 400

        if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            try:
                # Use real ML API call (proxy version below)
                response = requests.post(ML_MODEL_URL, files={'image': file})
                if response.status_code == 200:
                    img_base64 = base64.b64encode(response.content).decode()
                    return jsonify({
                        'success': True,
                        'enhanced_image': f'data:image/png;base64,{img_base64}'
                    })
                else:
                    return jsonify({'success': False, 'error': 'Model failed'}), 500
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400

    return render_template('super_resolution.html')

@app.route('/superres', methods=['POST'])
def superres_proxy():
    """
    Enhanced proxy endpoint that returns both original and flipped image as base64,
    to enable frontend preview and spinner control.
    """
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image uploaded"}), 400

    file = request.files['image']
    try:
        # Read original image
        img = Image.open(file)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Flip the image horizontally
        flipped = img.transpose(Image.FLIP_LEFT_RIGHT)

        # Encode original image
        orig_io = io.BytesIO()
        img.save(orig_io, format='PNG')
        orig_base64 = base64.b64encode(orig_io.getvalue()).decode()

        # Encode flipped image
        flip_io = io.BytesIO()
        flipped.save(flip_io, format='PNG')
        flip_base64 = base64.b64encode(flip_io.getvalue()).decode()

        return jsonify({
            "success": True,
            "original_image": f"data:image/png;base64,{orig_base64}",
            "enhanced_image": f"data:image/png;base64,{flip_base64}",
            "metadata": {
                "original_size": f"{img.width}x{img.height}",
                "enhanced_size": f"{flipped.width}x{flipped.height}",
                "model_version": "v1.0-placeholder",
                "processing_time": "0.5s"
            }
        })

    except Exception as e:
        app.logger.error(f"Superres processing error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/ebsd_cleanup', methods=['GET', 'POST'])
def ebsd_cleanup():
    # Dummy visual EBSD map creation — unchanged
    if request.method == 'POST':
        if 'ebsd_file' not in request.files:
            return jsonify({'success': False, 'error': 'No EBSD file uploaded'}), 400

        file = request.files['ebsd_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400

        if file and allowed_file(file.filename, ALLOWED_EBSD_EXTENSIONS):
            try:
                dummy_map = Image.new('RGB', (800, 600), color='white')
                draw = ImageDraw.Draw(dummy_map)
                for i in range(0, 800, 50):
                    for j in range(0, 600, 50):
                        color = (
                            int(128 + (i * j) % 128),
                            int(128 + (i + j) % 128),
                            int(128 + ((i - j) * 2) % 128)
                        )
                        draw.polygon([
                            (i, j),
                            (i + 50, j + 25),
                            (i + 25, j + 50),
                            (i - 25, j + 25)
                        ], fill=color)

                buffer = io.BytesIO()
                dummy_map.save(buffer, format='PNG')
                original_b64 = base64.b64encode(buffer.getvalue()).decode()

                # Enhanced
                enhanced_map = dummy_map.copy()
                draw = ImageDraw.Draw(enhanced_map)
                for i in range(0, 800, 50):
                    for j in range(0, 600, 50):
                        color = (
                            int(160 + (i * j) % 96),
                            int(160 + (i + j) % 96),
                            int(160 + ((i - j) * 2) % 96)
                        )
                        draw.polygon([
                            (i, j),
                            (i + 50, j + 25),
                            (i + 25, j + 50),
                            (i - 25, j + 25)
                        ], fill=color)

                buffer2 = io.BytesIO()
                enhanced_map.save(buffer2, format='PNG')
                enhanced_b64 = base64.b64encode(buffer2.getvalue()).decode()

                return jsonify({
                    'success': True,
                    'original_map': f'data:image/png;base64,{original_b64}',
                    'enhanced_map': f'data:image/png;base64,{enhanced_b64}',
                    'message': 'EBSD data processed successfully'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        return jsonify({'success': False, 'error': 'Invalid file type'}), 400

    return render_template('ebsd_cleanup.html')

@app.route('/download_processed_data')
def download_processed_data():
    dummy_data = "This is processed EBSD data"
    return send_file(io.BytesIO(dummy_data.encode()), mimetype='text/plain', as_attachment=True, download_name='processed_ebsd_data.ang')

@app.route('/api/v1/models/status', methods=['GET'])
def get_models_status():
    return jsonify({
        'super_resolution_model': {
            'status': 'ready',
            'version': 'v1.0-placeholder',
            'last_updated': '2024-01-01',
            'supported_formats': ['.png', '.jpg', '.jpeg']
        },
        'ebsd_cleanup_model': {
            'status': 'ready',
            'version': 'v1.0-placeholder',
            'last_updated': '2024-01-01',
            'supported_formats': ['.ang', '.ctf', '.ebsd']
        }
    })

if __name__ == '__main__':
    app.run(debug=True)
