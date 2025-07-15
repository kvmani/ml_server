from flask import Blueprint, render_template, request, jsonify
import os
import requests
from config import Config
from ..services.utils import allowed_file

bp = Blueprint('ebsd_cleanup', __name__)
config = Config()

@bp.route('/ebsd_cleanup', methods=['GET', 'POST'])
def ebsd_cleanup():
    if request.method == 'POST':
        if 'ebsd_file' not in request.files:
            return jsonify({'success': False, 'error': 'No EBSD file uploaded'}), 400

        file = request.files['ebsd_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400

        allowed_exts = config.config['ebsd_cleanup']['allowed_extensions']
        if not allowed_file(file.filename, allowed_exts):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        max_size = config.config['ebsd_cleanup']['file_settings']['max_size']
        if file_size > max_size:
            return jsonify({'success': False, 'error': 'File size exceeds limit'}), 400

        try:
            health_url = config.config['ebsd_cleanup']['ml_model']['health_url']
            health_response = requests.get(health_url, timeout=3)
            if health_response.status_code != 200:
                return jsonify({'success': False, 'error': 'EBSD ML model is not running'}), 503
        except requests.exceptions.RequestException:
            return jsonify({'success': False, 'error': 'EBSD ML model is not reachable'}), 503

        try:
            model_url = config.config['ebsd_cleanup']['ml_model']['url']
            timeout = config.config['ebsd_cleanup']['ml_model'].get('timeout', 30)
            response = requests.post(model_url, files={'ebsd_file': file}, timeout=timeout)
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'success': False, 'error': 'Model processing failed'}), 500
        except Exception as e:
            bp.logger.error(f"EBSD cleanup error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    return render_template('ebsd_cleanup.html')
