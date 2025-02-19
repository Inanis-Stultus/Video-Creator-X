import os
import io
import logging
import base64
import tempfile
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
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/editor')
def editor():
    return render_template('editor.html')

@app.route('/ai-workflow')
def ai_workflow():
    return render_template('ai_workflow.html')

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
                # Save file to temp directory first
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                unique_filename = timestamp + filename
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

                file.save(temp_path)

                # Read file data and encode as base64
                with open(temp_path, 'rb') as f:
                    file_data = base64.b64encode(f.read()).decode('utf-8')

                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {temp_path}: {str(e)}")

                return jsonify({
                    'success': True,
                    'filename': unique_filename,
                    'file_data': file_data,
                    'mime_type': file.content_type
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

        # Create temporary files for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Process each timeline item
                processed_timeline = []
                for item in timeline:
                    if 'file_data' in item:
                        # Decode base64 data and save to temp file
                        file_data = base64.b64decode(item['file_data'])
                        temp_path = os.path.join(temp_dir, item['filename'])
                        with open(temp_path, 'wb') as f:
                            f.write(file_data)
                        item_copy = item.copy()
                        item_copy['filepath'] = temp_path
                        processed_timeline.append(item_copy)

                # Create output file
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
                    try:
                        # Process video with the processed timeline
                        process_video(processed_timeline, temp_output.name, target_resolution)

                        # Read the processed video file
                        with open(temp_output.name, 'rb') as f:
                            video_data = f.read()

                        # Generate unique output filename
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        output_filename = f'output_{timestamp}.mp4'

                        # Create response
                        return send_file(
                            io.BytesIO(video_data),
                            mimetype='video/mp4',
                            as_attachment=True,
                            download_name=output_filename
                        )
                    finally:
                        # Clean up output file
                        try:
                            os.unlink(temp_output.name)
                        except:
                            pass

            except Exception as e:
                logger.error(f"Processing error in temp directory: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)