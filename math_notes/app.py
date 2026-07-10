from flask import Flask, render_template, request, jsonify, send_file
import os
from datetime import datetime

app = Flask(__name__)

# Ensure upload directory exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save', methods=['POST'])
def save_note():
    """Save the note content to a file"""
    try:
        content = request.json.get('content', '')
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'math_note_{timestamp}.md'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save content to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'message': f'Note saved successfully!',
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saving note: {str(e)}'
        }), 500

@app.route('/upload_image', methods=['POST'])
def upload_image():
    """Handle image upload for OCR recognition (placeholder for future implementation)"""
    if 'image' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No image file provided'
        }), 400
    
    try:
        image_file = request.files['image']
        
        # Save the uploaded image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'image_{timestamp}.png'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        image_file.save(filepath)
        
        # TODO: Implement OCR recognition here
        # For now, return a placeholder response
        recognized_text = "[OCR recognition will be implemented here - Math formula detected from image]"
        
        return jsonify({
            'success': True,
            'message': 'Image uploaded successfully',
            'recognized_text': recognized_text,
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing image: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002, threaded=True)
