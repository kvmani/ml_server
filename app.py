from flask import Flask, render_template, request, jsonify, send_file
import os
import io
from PIL import Image, ImageDraw
import base64
import requests
import json
from datetime import datetime
from config import Config
import logging

# Initialize configuration
config = Config()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Constants
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
ALLOWED_EBSD_EXTENSIONS = {'ang', 'ctf', 'cpr', 'osc', 'h5', 'hdf5'}
ML_MODEL_URL = "http://localhost:5002/infer"

# Initialize feedback file
FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feedback.json')
if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump({'feedback': []}, f)

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

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
        # Check if ML model server is running
        try:
            response = requests.get(config.config['super_resolution']['ml_model']['health_url'])
            if response.status_code != 200:
                # Try to start the server if it's not running
                if config.start_ml_model_service():
                    return jsonify({
                        'success': False, 
                        'error': 'ML model server was not running. It has been started. Please try your request again.'
                    }), 503
                else:
                    return jsonify({
                        'success': False, 
                        'error': 'ML model server is not running and could not be started. Please try again later.'
                    }), 503
        except requests.exceptions.RequestException:
            # Try to start the server if it's not running
            if config.start_ml_model_service():
                return jsonify({
                    'success': False, 
                    'error': 'ML model server was not running. It has been started. Please try your request again.'
                }), 503
            else:
                return jsonify({
                    'success': False, 
                    'error': 'ML model server is not running and could not be started. Please try again later.'
                }), 503

        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image uploaded'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No image selected'}), 400

        if file and allowed_file(file.filename, config.super_resolution_extensions):
            try:
                # Forward the request to ML model server
                response = requests.post(config.ml_model_url, files={'image': file})
                if response.status_code == 200:
                    img_base64 = base64.b64encode(response.content).decode()
                    return jsonify({
                        'success': True,
                        'enhanced_image': f'data:image/png;base64,{img_base64}'
                    })
                else:
                    return jsonify({'success': False, 'error': 'Model processing failed'}), 500
            except Exception as e:
                app.logger.error(f"Super resolution error: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400

    return render_template('super_resolution.html')

@app.route('/superres', methods=['POST'])
def superres_proxy():
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image uploaded"}), 400

    file = request.files['image']
    try:
        # Get original image data
        orig_io = io.BytesIO()
        file.save(orig_io)
        orig_io.seek(0)
        orig_base64 = base64.b64encode(orig_io.getvalue()).decode()

        # Forward to ML model for processing
        file.seek(0)  # Reset file pointer
        response = requests.post(ML_MODEL_URL, files={'image': file})
        
        if response.status_code == 200:
            # Get processed (flipped) image data
            flipped_base64 = base64.b64encode(response.content).decode()

            return jsonify({
                "success": True,
                "original_image": f"data:image/png;base64,{orig_base64}",
                "enhanced_image": f"data:image/png;base64,{flipped_base64}"
            })
        else:
            return jsonify({"success": False, "error": "Model processing failed"}), 500

    except Exception as e:
        app.logger.error(f"Superres processing error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/ebsd_cleanup', methods=['GET', 'POST'])
def ebsd_cleanup():
    if request.method == 'POST':
        if 'ebsd_file' not in request.files:
            return jsonify({'success': False, 'error': 'No EBSD file uploaded'}), 400

        file = request.files['ebsd_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400

        if file and allowed_file(file.filename, config.ebsd_extensions):
            try:
                # Dummy visual EBSD map creation
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

                # Enhanced map
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
                app.logger.error(f"EBSD cleanup error: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        return jsonify({'success': False, 'error': 'Invalid file type'}), 400

    return render_template('ebsd_cleanup.html')

@app.route('/download_processed_data')
def download_processed_data():
    dummy_data = "This is processed EBSD data"
    return send_file(io.BytesIO(dummy_data.encode()), mimetype='text/plain', 
                    as_attachment=True, download_name='processed_ebsd_data.ang')

def check_ml_model_status():
    try:
        response = requests.get(config.ml_model_health_url)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

@app.route('/api/check_model_status')
def api_check_model_status():
    is_running = check_ml_model_status()
    return jsonify({'running': is_running})

if __name__ == '__main__':
    # Setup logging based on debug mode
    log_level = logging.DEBUG if config.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format=config.config['logging']['format'],
        filename=os.path.join(config.config['logging']['log_dir'], config.config['logging']['log_file'])
    )
    
    print("\nChecking ML model service...")
    if not config.start_ml_model_service():
        print("Warning: ML model service could not be started. Some features may not work.")
    else:
        print("ML model service is running!")
    
    print(f"\nServer is running!")
    print(f"Access the application at: http://127.0.0.1:{config.config['port']}")
    print(f"Debug mode: {config.debug}")
    print(f"Press CTRL+C to quit\n")
    
    app.run(
        host="127.0.0.1",
        port=config.config['port'],
        debug=config.debug,
        use_reloader=True
    )