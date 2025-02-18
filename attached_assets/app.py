import os
import logging
import glob
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from utils import process_video

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'mp4', 'jpg', 'jpeg', 'png', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_files():
    """Remove files older than 24 hours from the upload folder."""
    try:
        cutoff = datetime.now() - timedelta(hours=24)
        for filepath in glob.glob(os.path.join(UPLOAD_FOLDER, '*')):
            if os.path.getmtime(filepath) < cutoff.timestamp():
                os.remove(filepath)
                logger.debug(f"Removed old file: {filepath}")
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")

@app.route('/')
def index():
    cleanup_old_files()
    return render_template('editor.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        if file:
            try:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                unique_filename = timestamp + filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                logger.debug(f"File saved successfully at {filepath}")
                return jsonify({
                    'success': True,
                    'filename': unique_filename,
                    'filepath': filepath
                })
            except Exception as e:
                logger.error(f"File save error: {str(e)}")
                return jsonify({'error': 'Failed to save file'}), 500

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        if not data or 'timeline' not in data:
            return jsonify({'error': 'Invalid request data'}), 400

        timeline = data['timeline']
        if not timeline:
            return jsonify({'error': 'Empty timeline'}), 400

        # Get custom resolution if provided
        target_resolution = None
        if 'resolution' in data:
            width = int(data['resolution'].get('width', 1920))
            height = int(data['resolution'].get('height', 1080))
            target_resolution = (width, height)

        # Verify all files exist
        for item in timeline:
            if not os.path.exists(item['filepath']):
                return jsonify({'error': f"File not found: {item['filename']}"}), 404

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'output_{timestamp}.mp4'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        process_video(timeline, output_path, target_resolution)
        logger.debug(f"Video processed successfully at {output_path}")

        return jsonify({'success': True, 'output': output_filename})

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)