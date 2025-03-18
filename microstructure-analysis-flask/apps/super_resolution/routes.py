from flask import render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from . import super_resolution_bp
import os
from PIL import Image, ImageEnhance, ImageFilter
import io
import logging
from werkzeug.utils import secure_filename
import traceback

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@super_resolution_bp.route('/')
@super_resolution_bp.route('/index')
def index():
    return render_template('index.html')

def enhance_image(image):
    """Basic image enhancement using simple filters and adjustments"""
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 1. Sharpen the image slightly
    image = image.filter(ImageFilter.SHARPEN)
    
    # 2. Adjust contrast
    contrast = ImageEnhance.Contrast(image)
    image = contrast.enhance(1.2)  # Increase contrast
    
    # 3. Adjust brightness
    brightness = ImageEnhance.Brightness(image)
    image = brightness.enhance(1.1)  # Increase brightness
    
    # 4. Adjust color balance
    color = ImageEnhance.Color(image)
    image = color.enhance(1.1)  # Increase color saturation
    
    return image

@super_resolution_bp.route('/process', methods=['POST'])
def process_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['image']
        if not file or not file.filename:
            return jsonify({'error': 'No selected file'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        # Read image
        image = Image.open(file.stream)
        
        # Apply basic enhancement
        enhanced_image = enhance_image(image)
        
        # Save to bytes buffer
        img_io = io.BytesIO()
        enhanced_image.save(img_io, 'PNG', quality=95)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=False)
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error in image processing: {error_details}")
        return jsonify({'error': 'Error processing image'}), 500

@super_resolution_bp.route('/feedback', methods=['POST'])
def feedback():
    try:
        feedback_text = request.form.get('feedback')
        if not feedback_text:
            return jsonify({
                'success': False,
                'error': 'No feedback provided'
            }), 400
            
        # Log feedback (can be replaced with database storage later)
        current_app.logger.info(f"Feedback received: {feedback_text}")
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!!'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error processing feedback: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error processing feedback'
        }), 500
