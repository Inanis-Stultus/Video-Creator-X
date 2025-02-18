import os
import io
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
from utils import process_video

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

ALLOWED_EXTENSIONS = {'mp4', 'jpg', 'jpeg', 'png', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
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

                # Read file data into memory
                file_data = file.read()

                return jsonify({
                    'success': True,
                    'filename': unique_filename,
                    'file_data': file_data.decode('utf-8') #added to handle potential decoding issues.
                })
            except Exception as e:
                logger.error(f"File processing error: {str(e)}")
                return jsonify({'error': 'Failed to process file'}), 500

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

        # Create output buffer
        output_buffer = io.BytesIO()

        # Process video with progress tracking
        process_video(timeline, output_buffer, target_resolution)

        # Prepare response
        output_buffer.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'output_{timestamp}.mp4'

        return send_file(
            output_buffer,
            as_attachment=True,
            download_name=output_filename,
            mimetype='video/mp4'
        )

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)