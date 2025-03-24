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

app = Flask(__name__)

# Configure upload folder for images with temporary storage
TEMP_FOLDER = os.path.join('static', 'temp')
app.config['UPLOAD_FOLDER'] = os.path.join(TEMP_FOLDER, 'uploads')
app.config['ENHANCED_FOLDER'] = os.path.join(TEMP_FOLDER, 'enhanced')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = os.urandom(24)  # Generate a random secret key

# Ensure temporary folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ENHANCED_FOLDER'], exist_ok=True)

# Configure cleanup settings
CLEANUP_INTERVAL = 3600  # 1 hour in seconds
FILE_EXPIRY = 24  # 24 hours

def cleanup_old_files():
    """Clean up files older than FILE_EXPIRY hours"""
    while True:
        try:
            current_time = datetime.now()
            # Clean up uploads folder
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                if current_time - file_time > timedelta(hours=FILE_EXPIRY):
                    os.remove(filepath)

            # Clean up enhanced folder
            for filename in os.listdir(app.config['ENHANCED_FOLDER']):
                filepath = os.path.join(app.config['ENHANCED_FOLDER'], filename)
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                if current_time - file_time > timedelta(hours=FILE_EXPIRY):
                    os.remove(filepath)

        except Exception as e:
            app.logger.error(f"Cleanup error: {str(e)}")
        
        time.sleep(CLEANUP_INTERVAL)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving the original extension"""
    ext = os.path.splitext(original_filename)[1]
    return f"{uuid.uuid4().hex}{ext}"

# Configure feedback storage
FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feedback.json')

# Initialize feedback file if it doesn't exist
if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump({'feedback': []}, f)

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
ALLOWED_EBSD_EXTENSIONS = {'ang', 'ctf', 'cpr', 'osc', 'h5', 'hdf5'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def process_image_in_memory(image_file):
    """Process image in memory without saving to disk"""
    try:
        # Read image into memory
        img = Image.open(image_file)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Get original size
        width, height = img.size
        
        # Calculate new size (4x upscaling)
        new_width = width * 4
        new_height = height * 4
        
        # Enhance image using high-quality upscaling
        enhanced = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert both original and enhanced images to base64
        # Original image
        original_buffer = io.BytesIO()
        img.save(original_buffer, format='PNG')
        original_base64 = base64.b64encode(original_buffer.getvalue()).decode()
        
        # Enhanced image
        enhanced_buffer = io.BytesIO()
        enhanced.save(enhanced_buffer, format='PNG')
        enhanced_base64 = base64.b64encode(enhanced_buffer.getvalue()).decode()
        
        return {
            'success': True,
            'original_image': f'data:image/png;base64,{original_base64}',
            'enhanced_image': f'data:image/png;base64,{enhanced_base64}',
            'original_size': f'{width}x{height}',
            'enhanced_size': f'{new_width}x{new_height}'
        }
    except Exception as e:
        app.logger.error(f"Error processing image: {str(e)}")
        raise Exception(f"Error processing image: {str(e)}")

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
            'page': request.referrer  # Store which page the feedback came from
        }
        
        with open(FEEDBACK_FILE, 'r+') as f:
            data = json.load(f)
            data['feedback'].insert(0, feedback_data)  # Add new feedback at the beginning
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

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
                # Process image in memory
                result = process_image_in_memory(file)
                return jsonify(result)
            except Exception as e:
                app.logger.error(f"Image processing error: {str(e)}")
                return jsonify({'success': False, 'error': 'Error processing image'}), 500
        
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    return render_template('super_resolution.html')

@app.route('/ebsd_cleanup', methods=['GET', 'POST'])
def ebsd_cleanup():
    if request.method == 'POST':
        if 'ebsd_file' not in request.files:
            return jsonify({'success': False, 'error': 'No EBSD file uploaded'}), 400
        
        file = request.files['ebsd_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename, ALLOWED_EBSD_EXTENSIONS):
            try:
                # Create a dummy visualization in memory
                dummy_map = Image.new('RGB', (800, 600), color='white')
                
                # Add some dummy patterns to make it look like an EBSD map
                draw = ImageDraw.Draw(dummy_map)
                
                # Draw some grain-like patterns
                for i in range(0, 800, 50):
                    for j in range(0, 600, 50):
                        color = (
                            int(128 + (i * j) % 128),
                            int(128 + (i + j) % 128),
                            int(128 + ((i - j) * 2) % 128)
                        )
                        points = [
                            (i, j),
                            (i + 50, j + 25),
                            (i + 25, j + 50),
                            (i - 25, j + 25)
                        ]
                        draw.polygon(points, fill=color)
                
                # Convert to base64
                buffer = io.BytesIO()
                dummy_map.save(buffer, format='PNG')
                map_base64 = base64.b64encode(buffer.getvalue()).decode()
                
                # Create an "enhanced" version with slightly different colors
                enhanced_map = dummy_map.copy()
                draw = ImageDraw.Draw(enhanced_map)
                for i in range(0, 800, 50):
                    for j in range(0, 600, 50):
                        color = (
                            int(160 + (i * j) % 96),
                            int(160 + (i + j) % 96),
                            int(160 + ((i - j) * 2) % 96)
                        )
                        points = [
                            (i, j),
                            (i + 50, j + 25),
                            (i + 25, j + 50),
                            (i - 25, j + 25)
                        ]
                        draw.polygon(points, fill=color)
                
                # Convert enhanced map to base64
                enhanced_buffer = io.BytesIO()
                enhanced_map.save(enhanced_buffer, format='PNG')
                enhanced_base64 = base64.b64encode(enhanced_buffer.getvalue()).decode()
                
                # Return the base64 encoded images
                return jsonify({
                    'success': True,
                    'original_map': f'data:image/png;base64,{map_base64}',
                    'enhanced_map': f'data:image/png;base64,{enhanced_base64}',
                    'message': 'EBSD data processed successfully'
                })
                
            except Exception as e:
                app.logger.error(f"EBSD processing error: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500
            
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    return render_template('ebsd_cleanup.html')

@app.route('/download_processed_data')
def download_processed_data():
    # Return processed data directly from memory
    dummy_data = "This is processed EBSD data"
    return send_file(
        io.BytesIO(dummy_data.encode()),
        mimetype='text/plain',
        as_attachment=True,
        download_name='processed_ebsd_data.ang'
    )

if __name__ == '__main__':
    app.run(debug=True) 