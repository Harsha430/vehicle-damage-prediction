import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import cv2
import numpy as np
from datetime import datetime

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
RESULTS_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Load model once at startup
model = YOLO('models/best.torchscript')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                           'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No file part',
            'data': None,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No selected file',
            'data': None,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 400
    
    if file and allowed_file(file.filename):
        try:
            # Ensure directories exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
            
            # Save original file
            filename = secure_filename(file.filename)
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(original_path)
            
            # Verify image was saved
            if not os.path.exists(original_path):
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to save file',
                    'data': None,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }), 500
                
            # Process image
            image = cv2.imread(original_path)
            if image is None:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid image file',
                    'data': None,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }), 400
                
            # Run prediction
            results = model(image)
            
            # Generate result filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            result_filename = f"result_{timestamp}.jpg"
            result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
            
            # Process and save results
            annotated_frame = results[0].plot()
            if not cv2.imwrite(result_path, annotated_frame):
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to save result image',
                    'data': None,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }), 500
                
            # Get predictions data
            predictions = []
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                predictions.append({
                    'class': results[0].names[int(box.cls[0])],
                    'confidence': float(box.conf[0]),
                    'bbox': [x1, y1, x2, y2],
                    'bbox_normalized': [float(x) for x in box.xyxyn[0].tolist()]
                })
            
            # Prepare response
            response = {
                'status': 'success',
                'message': 'File processed successfully',
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'data': {
                    'image_paths': {
                        'original': f"/static/uploads/{filename}",
                        'processed': f"/static/results/{result_filename}"
                    },
                    'predictions': predictions,
                    'statistics': {
                        'total_damages': len(predictions),
                        'damage_types': list(set(p['class'] for p in predictions)),
                        'confidence': {
                            'average': round(
                                sum(p['confidence'] for p in predictions) / len(predictions) if predictions else 0, 
                                2
                            ),
                            'min': round(min(p['confidence'] for p in predictions), 2) if predictions else 0,
                            'max': round(max(p['confidence'] for p in predictions), 2) if predictions else 0
                        }
                    }
                }
            }
            
            return jsonify(response)
            
        except Exception as e:
            app.logger.error(f"Error processing file: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'data': None,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }), 500
    
    return jsonify({
        'status': 'error',
        'message': 'Allowed file types are: png, jpg, jpeg',
        'data': None,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
