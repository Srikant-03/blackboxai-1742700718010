from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import json

app = Flask(__name__, 
    static_url_path='/static',
    static_folder='static',
    template_folder='templates'
)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def analyze_text_content(text):
    try:
        # Simple text analysis based on length and complexity
        word_count = len(text.split())
        sentence_count = len([s for s in text.split('.') if s.strip()])
        avg_word_length = sum(len(word) for word in text.split()) / word_count if word_count > 0 else 0
        
        # Basic authenticity metrics
        complexity_score = min(1.0, (avg_word_length / 10) * 0.5 + (sentence_count / word_count) * 0.5)
        
        return {
            'classification': "Likely Authentic" if complexity_score > 0.4 else "Potentially Modified",
            'confidence': float(complexity_score * 100),
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'word_count': word_count,
                'sentence_count': sentence_count,
                'avg_word_length': float(avg_word_length)
            }
        }
    except Exception as e:
        print(f"Error in text analysis: {str(e)}")
        return {
            'error': 'Text analysis failed',
            'details': str(e)
        }

def analyze_image_content(image):
    try:
        # Convert to numpy array if PIL Image
        if isinstance(image, Image.Image):
            image_array = np.array(image)
            if len(image_array.shape) == 2:  # Convert grayscale to RGB
                image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
        else:
            image_array = image

        # Convert BGR to RGB if needed
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

        # Load face cascade classifier
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return {
                'classification': 'No faces detected',
                'confidence': 0,
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'faces_detected': 0,
                    'image_dimensions': f"{image_array.shape[1]}x{image_array.shape[0]}"
                }
            }
        
        # Analyze each detected face
        face_results = []
        for (x, y, w, h) in faces:
            face_img = image_array[y:y+h, x:x+w]
            
            # Calculate quality metrics
            blur_score = cv2.Laplacian(cv2.cvtColor(face_img, cv2.COLOR_RGB2GRAY), cv2.CV_64F).var()
            noise_score = np.std(face_img)
            
            # Combine metrics for final score
            quality_score = min(1.0, (blur_score / 1000) * 0.4 + (noise_score / 100) * 0.6)
            
            face_results.append({
                'position': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                'quality_score': float(quality_score),
                'blur_score': float(blur_score),
                'noise_score': float(noise_score)
            })
        
        # Aggregate results
        avg_quality = np.mean([f['quality_score'] for f in face_results])
        classification = "Likely Authentic" if avg_quality > 0.6 else "Potentially Modified"
        
        return {
            'classification': classification,
            'confidence': float(avg_quality * 100),
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'faces_detected': len(faces),
                'face_details': face_results,
                'image_dimensions': f"{image_array.shape[1]}x{image_array.shape[0]}"
            }
        }
    except Exception as e:
        print(f"Error in image analysis: {str(e)}")
        return {
            'error': 'Image analysis failed',
            'details': str(e)
        }

def analyze_video_content(video_path):
    try:
        cap = cv2.VideoCapture(video_path)
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Sample frames at regular intervals
        frame_scores = []
        sample_interval = int(fps)  # Sample one frame per second
        
        for frame_idx in range(0, frame_count, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if ret:
                # Analyze frame
                frame_analysis = analyze_image_content(frame)
                if 'error' not in frame_analysis:
                    frame_scores.append({
                        'timestamp': f'{frame_idx/fps:.2f}',
                        'score': frame_analysis['confidence'] / 100,
                        'faces_detected': frame_analysis['metadata']['faces_detected']
                    })
        
        cap.release()
        
        if not frame_scores:
            return {
                'error': 'No valid frames analyzed',
                'timestamp': datetime.now().isoformat()
            }
        
        # Calculate overall metrics
        avg_score = np.mean([s['score'] for s in frame_scores])
        avg_faces = np.mean([s['faces_detected'] for s in frame_scores])
        score_std = np.std([s['score'] for s in frame_scores])
        
        # Higher variance in scores might indicate tampering
        authenticity_score = avg_score * (1 - score_std)
        
        return {
            'classification': 'Likely Authentic' if authenticity_score > 0.6 else 'Potentially Modified',
            'confidence': float(authenticity_score * 100),
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'fps': float(fps),
                'frame_count': frame_count,
                'dimensions': f'{width}x{height}',
                'duration': f'{frame_count/fps:.2f}',
                'frames_analyzed': len(frame_scores),
                'average_faces_per_frame': float(avg_faces),
                'score_stability': float(1 - score_std)
            },
            'frame_analysis': frame_scores[:10]  # Return first 10 frame analyses
        }
    except Exception as e:
        print(f"Error in video analysis: {str(e)}")
        return {
            'error': 'Video analysis failed',
            'details': str(e)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/text')
def text():
    return render_template('text.html')

@app.route('/image')
def image():
    return render_template('image.html')

@app.route('/video')
def video():
    return render_template('video.html')

@app.route('/analyze/text', methods=['POST'])
def analyze_text():
    try:
        text = request.form.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        result = analyze_text_content(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze/image', methods=['POST'])
def analyze_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Load and analyze image
            image = Image.open(filepath)
            result = analyze_image_content(image)
            
            # Clean up
            os.remove(filepath)
            
            return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze/video', methods=['POST'])
def analyze_video():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
            
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Analyze video
            result = analyze_video_content(filepath)
            
            # Clean up
            os.remove(filepath)
            
            return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)