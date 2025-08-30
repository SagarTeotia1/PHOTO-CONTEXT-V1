#!/usr/bin/env python3
"""
Flask web server for Image Context Analyzer
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
from dotenv import load_dotenv
from image_processor import ImageProcessor
import json
import base64
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the image processor
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in environment variables")
    print("Please set your Gemini API key in a .env file")
    exit(1)

try:
    processor = ImageProcessor(api_key)
    print("✅ Gemini API connected successfully!")
except Exception as e:
    print(f"❌ Error: Failed to initialize Gemini API: {str(e)}")
    exit(1)

@app.route('/')
def index():
    """Serve the main HTML page."""
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return html_content

@app.route('/process-image', methods=['POST'])
def process_image():
    """Process uploaded image(s) with Gemini API."""
    try:
        print(f"🔍 Processing image request...")
        
        # Check if image files are present
        if 'images' not in request.files:
            # Fallback to single image for backward compatibility
            if 'image' not in request.files:
                print("❌ No image files in request")
                return jsonify({'error': 'No image files provided'}), 400
            
            # Handle single image
            return process_single_image(request)
        
        # Handle multiple images
        image_files = request.files.getlist('images')
        if not image_files or all(f.filename == '' for f in image_files):
            print("❌ No valid image files selected")
            return jsonify({'error': 'No valid image files selected'}), 400
        
        print(f"📸 Processing {len(image_files)} images...")
        
        # Get optional parameters
        custom_prompt = request.form.get('prompt', None)
        custom_filename = request.form.get('filename', None)
        
        print(f"📝 Custom prompt: {custom_prompt[:100] if custom_prompt else 'None'}...")
        print(f"📁 Custom filename: {custom_filename}")
        
        # Save uploaded files temporarily and copy to uploads
        temp_paths = []
        upload_paths = []
        
        for i, image_file in enumerate(image_files):
            if image_file.filename:
                # Create temp file in uploads directory instead of main directory
                temp_path = os.path.join(processor.uploads_dir, f"temp_{i}_{image_file.filename}")
                image_file.save(temp_path)
                temp_paths.append(temp_path)
                
                # Copy to uploads folder with timestamp
                upload_path = processor.copy_image_to_uploads(temp_path)
                upload_paths.append(upload_path)
                
                print(f"💾 Saved temp file {i+1}: {temp_path}")
                print(f"📁 Copied to uploads: {upload_path}")
        
        try:
            # Process all images with Gemini
            print("🤖 Calling Gemini API for batch processing...")
            
            batch_result = processor.process_multiple_images(temp_paths, custom_prompt)
            print(f"✅ Batch processing completed. Status: {batch_result['processing_status']}")
            
            # Add upload paths to results BEFORE saving to JSON
            for i, result in enumerate(batch_result['images']):
                if i < len(upload_paths):
                    result['upload_path'] = upload_paths[i]
            
            # Save batch results to JSON (after adding upload_paths)
            print("💾 Saving batch results to JSON...")
            json_path = processor.save_batch_to_json(batch_result, custom_filename)
            print(f"📁 Batch JSON saved to: {json_path}")
            
            # Clean up temp files from uploads directory
            for temp_path in temp_paths:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"🧹 Cleaned up temp file: {temp_path}")
            print("🧹 Temp files cleaned up")
            
            return jsonify({
                'success': True,
                'result': batch_result,
                'json_path': json_path,
                'upload_paths': upload_paths
            })
            
        except Exception as e:
            # Clean up temp files from uploads directory even after error
            for temp_path in temp_paths:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"🧹 Cleaned up temp file after error: {temp_path}")
            print(f"🧹 Temp files cleaned up after error")
            print(f"❌ Error during batch processing: {str(e)}")
            raise e
            
    except Exception as e:
        print(f"❌ Fatal error in process_image: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Ensure we have a complete error structure
        error_result = {
            'success': False,
            'error': str(e),
            'result': {
                'timestamp': datetime.now().isoformat(),
                'image_name': 'Multiple Images',
                'image_size': {'width': 0, 'height': 0, 'format': 'Unknown'},
                'context': f'Fatal error: {str(e)}',
                'processing_status': 'failed'
            }
        }
        
        return jsonify(error_result), 500

def process_single_image(request):
    """Process a single uploaded image (backward compatibility)."""
    try:
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        print(f"📸 Processing single image: {image_file.filename}")
        
        # Get optional parameters
        custom_prompt = request.form.get('prompt', None)
        custom_filename = request.form.get('filename', None)
        
        # Save uploaded file temporarily in uploads directory
        temp_path = os.path.join(processor.uploads_dir, f"temp_{image_file.filename}")
        image_file.save(temp_path)
        print(f"💾 Saved temp file: {temp_path}")
        
        # Copy to uploads folder with timestamp
        upload_path = processor.copy_image_to_uploads(temp_path)
        
        # Test if image can be opened
        try:
            from PIL import Image
            test_image = Image.open(temp_path)
            print(f"   Image test: {test_image.format} {test_image.size} {test_image.mode}")
            test_image.close()
        except Exception as img_error:
            print(f"   ⚠️ Image test failed: {str(img_error)}")
        
        try:
            # Process image with Gemini
            print("🤖 Calling Gemini API...")
            print(f"   Temp file: {temp_path}")
            print(f"   File size: {os.path.getsize(temp_path)} bytes")
            
            result = processor.process_image(temp_path, custom_prompt)
            print(f"✅ Gemini processing completed. Status: {result['processing_status']}")
            
            if result["processing_status"] == "success":
                # Add upload path to result BEFORE saving to JSON
                result['upload_path'] = upload_path
                
                # Save to JSON
                print("💾 Saving to JSON...")
                json_path = processor.save_to_json(result, custom_filename)
                print(f"📁 JSON saved to: {json_path}")
                
                # Clean up temp file from uploads directory
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print("🧹 Temp file cleaned up")
                
                return jsonify({
                    'success': True,
                    'result': result,
                    'json_path': json_path,
                    'upload_path': upload_path
                })
            else:
                # Add upload path to result even for failures
                result['upload_path'] = upload_path
                
                # Clean up temp file from uploads directory
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print("🧹 Temp file cleaned up")
                print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                
                # Ensure we have a complete result structure even for failures
                error_result = {
                    'success': False,
                    'error': result.get('error', 'Unknown processing error'),
                    'result': result
                }
                
                return jsonify(error_result), 500
        
        except Exception as e:
            # Clean up temp file from uploads directory even after error
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"🧹 Cleaned up temp file after error")
            print(f"❌ Error during processing: {str(e)}")
            raise e
            
    except Exception as e:
        print(f"❌ Error in single image processing: {str(e)}")
        raise e

@app.route('/history')
def get_history():
    """Get processing history."""
    try:
        history = processor.get_processing_history()
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/download/<filename>')
def download_json(filename):
    """Download a specific JSON file."""
    try:
        file_path = os.path.join(processor.output_dir, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'content': content,
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'gemini_connected': api_key is not None
    })

@app.route('/test')
def test_endpoint():
    """Simple test endpoint."""
    return jsonify({
        'message': 'Server is running!',
        'timestamp': datetime.now().isoformat(),
        'gemini_api_key': 'configured' if api_key else 'missing'
    })

@app.route('/search', methods=['POST'])
def search_images():
    """Search for images using natural language description."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Search query is required'}), 400
        
        search_query = data['query']
        max_results = data.get('max_results', 5)
        
        print(f"🔍 Search request: '{search_query}' (max: {max_results})")
        
        # Perform search
        search_results = processor.search_images_by_description(search_query, max_results)
        
        # Check if images exist in uploads folder
        for result in search_results:
            upload_path = result.get('upload_path', '')
            print(f"🔍 Search result: {result.get('image_name', 'Unknown')} - upload_path: {upload_path}")
            if upload_path and os.path.exists(upload_path):
                result['image_exists'] = True
                result['image_url'] = f'/uploads/{os.path.basename(upload_path)}'
                print(f"✅ Image exists: {result['image_url']}")
            else:
                result['image_exists'] = False
                result['image_url'] = None
                print(f"❌ Image not found: {upload_path}")
        
        return jsonify({
            'success': True,
            'query': search_query,
            'results': search_results,
            'total_found': len(search_results)
        })
        
    except Exception as e:
        print(f"❌ Error during search: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/uploads/<filename>')
def serve_uploaded_image(filename):
    """Serve uploaded images."""
    try:
        upload_path = os.path.join(processor.uploads_dir, filename)
        if os.path.exists(upload_path):
            from flask import send_file
            return send_file(upload_path)
        else:
            return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Image Context Analyzer Web Server...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🔧 API endpoints:")
    print("   - GET  /              - Main interface")
    print("   - POST /process-image - Process image with Gemini")
    print("   - POST /search        - Search images by description")
    print("   - GET  /uploads/<file> - Serve uploaded images")
    print("   - GET  /history       - Get processing history")
    print("   - GET  /health        - Health check")
    print("   - GET  /test          - Test endpoint")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
