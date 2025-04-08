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

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize feedback file
FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feedback.json')
if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump({'feedback': []}, f)

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

        if file and allowed_file(file.filename, config.config['super_resolution']['allowed_extensions']):
            try:
                # Forward the request to ML model server
                response = requests.post(config.ml_model_url, files={'image': file})
                if response.status_code == 200:
                    # Get base64 of original image
                    orig_io = io.BytesIO()
                    file.seek(0)
                    file.save(orig_io)
                    orig_io.seek(0)
                    original_b64 = base64.b64encode(orig_io.getvalue()).decode()

                    # Get base64 of enhanced image
                    enhanced_b64 = base64.b64encode(response.content).decode()

                    return jsonify({
                        'success': True,
                        'original_image': f'data:image/png;base64,{original_b64}',
                        'enhanced_image': f'data:image/png;base64,{enhanced_b64}'
                    })
                else:
                    return jsonify({'success': False, 'error': 'Model processing failed'}), 500
            except Exception as e:
                app.logger.error(f"Super resolution error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    return render_template('super_resolution.html')


@app.route('/ebsd_cleanup', methods=['GET', 'POST'])
def ebsd_cleanup():
    if request.method == 'POST':
        if 'ebsd_file' not in request.files:
            return jsonify({'success': False, 'error': 'No EBSD file uploaded'}), 400

        file = request.files['ebsd_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400

        # Check extension
        allowed_exts = config.config['ebsd_cleanup']['allowed_extensions']
        if not allowed_file(file.filename, allowed_exts):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        max_size = config.config['ebsd_cleanup']['file_settings']['max_size']
        if file_size > max_size:
            return jsonify({'success': False, 'error': 'File size exceeds limit'}), 400

        # ✅ Check if fake_ebsd_model.py is running
        try:
            health_url = config.config['ebsd_cleanup']['ml_model']['health_url']
            health_response = requests.get(health_url, timeout=3)
            if health_response.status_code != 200:
                return jsonify({'success': False, 'error': 'EBSD ML model is not running'}), 503
        except requests.exceptions.RequestException:
            return jsonify({'success': False, 'error': 'EBSD ML model is not reachable'}), 503

        # ✅ If model is up, send the file
        try:
            model_url = config.config['ebsd_cleanup']['ml_model']['url']
            timeout = config.config['ebsd_cleanup']['ml_model'].get('timeout', 30)
            response = requests.post(
                model_url,
                files={'ebsd_file': file},
                timeout=timeout
            )

            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'success': False, 'error': 'Model processing failed'}), 500

        except Exception as e:
            app.logger.error(f"EBSD cleanup error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    return render_template('ebsd_cleanup.html')


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


def check_ebsd_model_status():
    try:
        response = requests.get(config.config['ebsd_cleanup']['ml_model']['health_url'])
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

@app.route('/api/check_ebsd_model_status')
def api_check_ebsd_model_status():
    is_running = check_ebsd_model_status()
    return jsonify({'running': is_running})

@app.route('/download_processed_data')
def download_processed_data():
    try:
        file_path = "tmp/enhanced_ebsd_map.png"
        if not os.path.exists(file_path):
            return "Processed file not found.", 404
        return send_file(file_path, mimetype='image/png', as_attachment=True, download_name="enhanced_ebsd_map.png")
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return "Internal Server Error", 500

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

    print("\nChecking EBSD model service...")
    if not config.start_ebsd_model_service():
        print("Warning: EBSD model service could not be started. EBSD features may not work.")
    else:
        print("EBSD model service is running!")
    
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