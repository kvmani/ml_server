from flask import render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from . import super_resolution_bp
import os
from PIL import Image
import io
import logging
from werkzeug.utils import secure_filename
import traceback
# import cv2  # OpenCV is no longer needed
import numpy as np

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@super_resolution_bp.route('/')
@super_resolution_bp.route('/index')
def index():
    return render_template('index.html')

# Commented out OpenCV image processing functions
# def enhance_image_clarity(image):
#     kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
#     enhanced_image = cv2.filter2D(src=image, ddepth=-1, kernel=kernel)
#     return enhanced_image

# def deblur_image(image):
#     blurred = cv2.GaussianBlur(image, (0, 0), 3)
#     deblurred_image = cv2.addWeighted(image, 1.5, blurred, -0.5, 0)
#     return deblurred_image

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
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # No modifications to image, just return the original
        img_io = io.BytesIO()
        image.save(img_io, 'PNG', quality=95)
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
            'message': 'Thank you for your feedback!'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error processing feedback: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error processing feedback'
        }), 500

# Commented out OpenCV-based functions
# def upscale_image(image):
#     width = int(image.shape[1] * 2)
#     height = int(image.shape[0] * 2)
#     dim = (width, height)
#     upscaled_image = cv2.resize(image, dim, interpolation=cv2.INTER_CUBIC)
#     return upscaled_image

# def sharpen_image(image):
#     kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
#     sharpened_image = cv2.filter2D(src=image, ddepth=-1, kernel=kernel)
#     return sharpened_image

@super_resolution_bp.route('/ai_super_enlarge', methods=['POST'])
def ai_super_enlarge():
    try:
        file = request.files['image']
        if file and allowed_file(file.filename):
            # Read image
            image = Image.open(file.stream)
            
            # No upscaling, return original image
            img_io = io.BytesIO()
            image.save(img_io, 'PNG', quality=95, optimize=True)
            img_io.seek(0)
            return send_file(img_io, mimetype='image/png', as_attachment=False, download_name='output_image.png')
        else:
            return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error in AI Super Enlargement: {error_details}")
        return jsonify({'error': 'Error processing image'}), 500

@super_resolution_bp.route('/ai_sharpen', methods=['POST'])
def ai_sharpen():
    try:
        file = request.files['image']
        if file and allowed_file(file.filename):
            # Read image
            image = Image.open(file.stream)

            # No sharpening, return original image
            img_io = io.BytesIO()
            image.save(img_io, 'PNG', quality=95, optimize=True)
            img_io.seek(0)
            return send_file(img_io, mimetype='image/png', as_attachment=False, download_name='output_image.png')
        else:
            return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error in AI Image Sharpening: {error_details}")
        return jsonify({'error': 'Error processing image'}), 500
