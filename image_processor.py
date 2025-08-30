import os
import json
import base64
from datetime import datetime
from typing import Dict, Any, Optional
import google.generativeai as genai
from PIL import Image
import io

class ImageProcessor:
    def __init__(self, api_key: str):
        """Initialize the ImageProcessor with Gemini API key."""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.output_dir = "processed_images"
        self.uploads_dir = "uploads"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create output and uploads directories if they don't exist."""
        for directory in [self.output_dir, self.uploads_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Clean up old files and migrate to new structure
        self._migrate_old_files()
        
        # Clean up any temporary files in main directory
        self._cleanup_temp_files()
    
    def _migrate_old_files(self):
        """Migrate old JSON files to the new batch structure."""
        try:
            # Look for old format files (files with 'images' array but no 'batches' array)
            for filename in os.listdir(self.output_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.output_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Check if this is old format that needs migration
                        if isinstance(data, dict) and "images" in data and isinstance(data["images"], list) and "batches" not in data:
                            print(f"🔄 Found old format file: {filename}")
                            
                            # Create new structure
                            new_data = {
                                "batches": [data],  # Wrap old data as first batch
                                "total_images_processed": data.get("total_images", 0),
                                "last_updated": data.get("batch_timestamp", datetime.now().isoformat())
                            }
                            
                            # Save as new format
                            new_filename = "image_analysis_history.json"
                            new_filepath = os.path.join(self.output_dir, new_filename)
                            
                            with open(new_filepath, 'w', encoding='utf-8') as f:
                                json.dump(new_data, f, indent=2, ensure_ascii=False)
                            
                            print(f"✅ Migrated {filename} to {new_filename}")
                            
                            # Remove old file
                            os.remove(filepath)
                            print(f"🧹 Removed old file: {filename}")
                            
                    except Exception as e:
                        print(f"⚠️ Error processing {filename}: {e}")
                        continue
                        
        except Exception as e:
            print(f"⚠️ Error during migration: {e}")
    
    def _cleanup_temp_files(self):
        """Clean up any temporary files in the main directory."""
        try:
            current_dir = os.getcwd()
            for filename in os.listdir(current_dir):
                if filename.startswith('temp_') and (filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg')):
                    filepath = os.path.join(current_dir, filename)
                    try:
                        os.remove(filepath)
                        print(f"🧹 Cleaned up old temp file: {filename}")
                    except Exception as e:
                        print(f"⚠️ Could not remove old temp file {filename}: {e}")
        except Exception as e:
            print(f"⚠️ Error during temp file cleanup: {e}")
    
    def process_image(self, image_path: str, prompt: str = None) -> Dict[str, Any]:
        """
        Process an image with Gemini 2.5 Pro and return the context.
        
        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt for image analysis
            
        Returns:
            Dictionary containing image context and metadata
        """
        try:
            # Load and prepare the image
            image = Image.open(image_path)
            
            # Convert image to bytes for Gemini - use PNG format for better compatibility
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)  # Reset position to beginning
            
            # Default prompt if none provided
            if prompt is None:
                prompt = """Dynamic Universal Image Analysis Prompt

System Role:
You are an advanced multimodal AI trained to perform exhaustive image analysis with maximum depth, precision, and creativity. Your job is not just to describe, but to extract, interpret, cross-reference, and contextualize every possible detail from an image.

Prompt:

"Analyze the input image step by step and provide the most comprehensive extraction possible. Follow this layered approach:

1. Raw Text Extraction (OCR++)

Extract every visible text fragment, no matter how small or distorted.

Detect printed, handwritten, stylized, or watermark text.

Preserve formatting, line breaks, and structure (tables, lists, captions).

2. Object & Scene Recognition

Identify all objects, people, items, vehicles, animals, tools, etc.

Mention orientation, positions, and interactions between them.

Specify environment type (indoor/outdoor, natural/urban, staged/candid).

3. People & Identity Clues

Describe faces, clothing, age group, emotions, gestures, and roles.

If any famous personality or public figure is detected, identify them and provide relevant background/context.

If not certain, list possible matches with confidence levels.

4. Event / Situation Context

Infer if this image relates to an event (sports, wedding, protest, concert, classroom, conference, etc.).

Provide cultural, geographical, or historical context if available.

If it's a social media screenshot, specify the likely platform (Instagram, Twitter/X, WhatsApp, etc.).

5. Brand / Logo / Product Detection

Recognize any brand marks, corporate logos, or product packaging.

Suggest likely industries (tech, fashion, food, automotive, entertainment).

6. Colors, Style & Aesthetic

List dominant and secondary colors in plain language and hex codes if possible.

Describe artistic or photographic style (retro, cinematic, minimalistic, futuristic, casual, documentary).

Mention lighting quality, composition, camera angle if inferable.

7. Internet / Cultural Cross-Reference

If the image resembles a famous photo, meme, artwork, or viral media, identify it and explain its significance.

Provide background (origin, meaning, how it is used online).

8. Metadata & Hidden Clues

Infer medium (photo, screenshot, scanned document, poster, magazine, digital art).

Detect timestamps, icons, UI elements, or signs of editing/manipulation.

Highlight any security or sensitive data visible (emails, phone numbers, IDs).

9. Contextual Reasoning

Provide possible purposes of this image (advertisement, memory, news coverage, personal use, legal doc, educational material).

Suggest categories/tags that would help index it in a knowledge system.

10. Rich Human-Friendly Summary

Write a detailed description as if explaining the image to a blind person.

Capture what is seen, what it might mean, and why it matters.

Be factual but also provide possible interpretations."""
            
            # Generate content with Gemini - pass the PIL Image object directly
            print(f"🤖 Sending image to Gemini API...")
            print(f"   Image format: {image.format}")
            print(f"   Image size: {image.size}")
            print(f"   Image mode: {image.mode}")
            
            try:
                response = self.model.generate_content([prompt, image])
                print(f"✅ Gemini API response received ({len(response.text)} characters)")
            except Exception as gemini_error:
                print(f"❌ Gemini API error: {str(gemini_error)}")
                # Try alternative approach with bytes
                print(f"🔄 Trying alternative approach with image bytes...")
                img_bytes = img_byte_arr.getvalue()
                response = self.model.generate_content([prompt, img_bytes])
                print(f"✅ Gemini API response received with bytes ({len(response.text)} characters)")
            
            # Extract the response text
            context = response.text
            
            # Create result dictionary
            result = {
                "timestamp": datetime.now().isoformat(),
                "image_path": image_path,
                "image_name": os.path.basename(image_path),
                "image_size": {
                    "width": image.width,
                    "height": image.height,
                    "format": image.format or "Unknown"
                },
                "prompt_used": prompt,
                "context": context,
                "processing_status": "success"
            }
            
            return result
            
        except Exception as e:
            # Try to get basic image info even if processing fails
            try:
                temp_image = Image.open(image_path)
                image_size = {
                    "width": temp_image.width,
                    "height": temp_image.height,
                    "format": temp_image.format or "Unknown"
                }
                temp_image.close()
            except:
                image_size = {
                    "width": 0,
                    "height": 0,
                    "format": "Unknown"
                }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "image_path": image_path,
                "image_name": os.path.basename(image_path),
                "image_size": image_size,
                "error": str(e),
                "processing_status": "failed",
                "context": f"Processing failed: {str(e)}"
            }
    
    def save_to_json(self, result: Dict[str, Any], filename: str = None) -> str:
        """
        Save the processing result to a JSON file.
        
        Args:
            result: The result dictionary from process_image
            filename: Optional custom filename, defaults to timestamp-based name
            
        Returns:
            Path to the saved JSON file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_context_{timestamp}.json"
        
        # Ensure filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            return filepath
        except Exception as e:
            raise Exception(f"Failed to save JSON file: {str(e)}")
    
    def process_and_save(self, image_path: str, prompt: str = None, filename: str = None) -> str:
        """
        Process an image and save the result to JSON in one step.
        
        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt for image analysis
            filename: Optional custom filename for the JSON output
            
        Returns:
            Path to the saved JSON file
        """
        result = self.process_image(image_path, prompt)
        return self.save_to_json(result, filename)
    
    def process_multiple_images(self, image_paths: list, prompt: str = None, batch_filename: str = None) -> Dict[str, Any]:
        """
        Process multiple images and return a comprehensive batch result.
        
        Args:
            image_paths: List of image file paths
            prompt: Optional custom prompt for image analysis
            batch_filename: Optional custom filename for the batch JSON output
            
        Returns:
            Dictionary containing batch processing results
        """
        batch_result = {
            "batch_timestamp": datetime.now().isoformat(),
            "total_images": len(image_paths),
            "successful_images": 0,
            "failed_images": 0,
            "images": [],
            "batch_summary": "",
            "processing_status": "processing"
        }
        
        print(f"🔄 Processing batch of {len(image_paths)} images...")
        
        for i, image_path in enumerate(image_paths, 1):
            print(f"📸 Processing image {i}/{len(image_paths)}: {os.path.basename(image_path)}")
            
            try:
                # Process individual image
                result = self.process_image(image_path, prompt)
                batch_result["images"].append(result)
                
                if result["processing_status"] == "success":
                    batch_result["successful_images"] += 1
                else:
                    batch_result["failed_images"] += 1
                    
            except Exception as e:
                print(f"❌ Error processing {image_path}: {str(e)}")
                error_result = {
                    "timestamp": datetime.now().isoformat(),
                    "image_path": image_path,
                    "image_name": os.path.basename(image_path),
                    "image_size": {"width": 0, "height": 0, "format": "Unknown"},
                    "error": str(e),
                    "processing_status": "failed",
                    "context": f"Processing failed: {str(e)}"
                }
                batch_result["images"].append(error_result)
                batch_result["failed_images"] += 1
        
        # Generate batch summary
        if batch_result["successful_images"] > 0:
            batch_result["processing_status"] = "completed"
            batch_result["batch_summary"] = f"Successfully processed {batch_result['successful_images']} out of {batch_result['total_images']} images"
        else:
            batch_result["processing_status"] = "failed"
            batch_result["batch_summary"] = f"Failed to process any images out of {batch_result['total_images']} total"
        
        print(f"✅ Batch processing completed: {batch_result['successful_images']} successful, {batch_result['failed_images']} failed")
        
        return batch_result
    
    def save_batch_to_json(self, batch_result: Dict[str, Any], filename: str = None) -> str:
        """
        Save batch processing results to a JSON file, appending to existing if available.
        
        Args:
            batch_result: The batch result dictionary from process_multiple_images
            filename: Optional custom filename, defaults to consistent history file
            
        Returns:
            Path to the saved JSON file
        """
        if filename is None:
            filename = "image_analysis_history.json"  # Use consistent filename for all batches
        
        # Ensure filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Load existing data if file exists
        existing_data = {"batches": [], "total_images_processed": 0, "last_updated": ""}
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    
                    # Check if this is the new format (with 'batches' array)
                    if isinstance(loaded_data, dict) and "batches" in loaded_data and isinstance(loaded_data["batches"], list):
                        print(f"✅ Loading existing new-format data with {len(loaded_data['batches'])} batches")
                        existing_data = loaded_data
                    
                    # Check if this is the old format (with 'images' array directly)
                    elif isinstance(loaded_data, dict) and "images" in loaded_data and isinstance(loaded_data["images"], list):
                        print(f"🔄 Migrating old-format data to new format")
                        # Convert old format to new format
                        existing_data = {
                            "batches": [loaded_data],  # Wrap the old data as the first batch
                            "total_images_processed": loaded_data.get("total_images", 0),
                            "last_updated": loaded_data.get("batch_timestamp", datetime.now().isoformat())
                        }
                        print(f"✅ Migrated old format: {len(existing_data['batches'])} batches, {existing_data['total_images_processed']} images")
                    
                    else:
                        print(f"⚠️ Existing file has unrecognized structure, starting fresh")
                        existing_data = {"batches": [], "total_images_processed": 0, "last_updated": ""}
                        
            except Exception as e:
                print(f"⚠️ Error reading existing file: {e}, starting fresh")
                existing_data = {"batches": [], "total_images_processed": 0, "last_updated": ""}
        
        # Ensure the existing_data has the required structure
        if "batches" not in existing_data or not isinstance(existing_data["batches"], list):
            existing_data["batches"] = []
        if "total_images_processed" not in existing_data:
            existing_data["total_images_processed"] = 0
        if "last_updated" not in existing_data:
            existing_data["last_updated"] = ""
        
        # Add new batch to existing data
        batch_result["batch_id"] = len(existing_data["batches"]) + 1
        existing_data["batches"].append(batch_result)
        existing_data["total_images_processed"] += batch_result.get("total_images", 0)
        existing_data["last_updated"] = datetime.now().isoformat()
        
        # Save updated data back to file
        try:
            # Validate the data structure before saving
            if not isinstance(existing_data, dict):
                raise ValueError("existing_data must be a dictionary")
            if "batches" not in existing_data or not isinstance(existing_data["batches"], list):
                raise ValueError("existing_data must have a 'batches' list")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Batch results appended to: {filepath}")
            print(f"📊 Total batches: {len(existing_data['batches'])}, Total images: {existing_data['total_images_processed']}")
            print(f"🔍 Data structure validation passed")
            return filepath
        except Exception as e:
            print(f"❌ Error saving batch JSON file: {str(e)}")
            print(f"🔍 existing_data structure: {type(existing_data)}")
            if isinstance(existing_data, dict):
                print(f"🔍 existing_data keys: {list(existing_data.keys())}")
            raise Exception(f"Failed to save batch JSON file: {str(e)}")
    
    def copy_image_to_uploads(self, image_path: str) -> str:
        """
        Copy an image to the uploads directory with a unique filename.
        
        Args:
            image_path: Path to the source image file
            
        Returns:
            Path to the copied image in uploads directory
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = os.path.basename(image_path)
            name, ext = os.path.splitext(original_name)
            unique_filename = f"{name}_{timestamp}{ext}"
            
            upload_path = os.path.join(self.uploads_dir, unique_filename)
            
            # Copy the image
            import shutil
            shutil.copy2(image_path, upload_path)
            
            print(f"💾 Image copied to uploads: {upload_path}")
            return upload_path
            
        except Exception as e:
            print(f"❌ Error copying image to uploads: {str(e)}")
            return image_path  # Return original path if copy fails
    
    def get_processing_history(self) -> list:
        """Get list of all processed JSON files."""
        json_files = []
        for file in os.listdir(self.output_dir):
            if file.endswith('.json'):
                filepath = os.path.join(self.output_dir, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        json_files.append({
                            "filename": file,
                            "filepath": filepath,
                            "timestamp": data.get("timestamp", "Unknown"),
                            "image_name": data.get("image_name", "Unknown"),
                            "status": data.get("processing_status", "Unknown")
                        })
                except Exception:
                    continue
        
        # Sort by timestamp (newest first)
        json_files.sort(key=lambda x: x["timestamp"], reverse=True)
        return json_files
    
    def search_images_by_description(self, search_query: str, max_results: int = 5) -> list:
        """
        Search through processed images using natural language description.
        
        Args:
            search_query: Natural language description to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of matching images with relevance scores
        """
        print(f"🔍 Searching for: '{search_query}'")
        
        search_results = []
        
        # Search through all JSON files, prioritizing the new format
        json_files = []
        for file in os.listdir(self.output_dir):
            if file.endswith('.json'):
                json_files.append(file)
        
        # Sort files to prioritize image_analysis_history.json (new format)
        json_files.sort(key=lambda x: (x != "image_analysis_history.json", x))
        
        for file in json_files:
            filepath = os.path.join(self.output_dir, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Handle new batch structure with 'batches' array
                        if 'batches' in data and isinstance(data['batches'], list):
                            # New batch structure - search through all batches
                            for batch_index, batch in enumerate(data['batches']):
                                if 'images' in batch and isinstance(batch['images'], list):
                                    for img_data in batch['images']:
                                        relevance_score = self._calculate_relevance(img_data, search_query)
                                        if relevance_score > 0:
                                            search_results.append({
                                                'image_name': img_data.get('image_name', 'Unknown'),
                                                'image_path': img_data.get('image_path', 'Unknown'),
                                                'upload_path': img_data.get('upload_path', 'Unknown'),
                                                'context': img_data.get('context', ''),
                                                'image_size': img_data.get('image_size', {}),
                                                'timestamp': img_data.get('timestamp', 'Unknown'),
                                                'relevance_score': relevance_score,
                                                'source_file': file,
                                                'processing_status': img_data.get('processing_status', 'Unknown'),
                                                'batch_id': batch.get('batch_id', batch_index + 1)
                                            })
                        # Handle legacy batch structure with 'images' array
                        elif 'images' in data and isinstance(data['images'], list):
                            # Legacy batch result - search through individual images
                            for img_data in data['images']:
                                relevance_score = self._calculate_relevance(img_data, search_query)
                                if relevance_score > 0:
                                    search_results.append({
                                        'image_name': img_data.get('image_name', 'Unknown'),
                                        'image_path': img_data.get('image_path', 'Unknown'),
                                        'upload_path': img_data.get('upload_path', 'Unknown'),
                                        'context': img_data.get('context', ''),
                                        'image_size': img_data.get('image_size', {}),
                                        'timestamp': img_data.get('timestamp', 'Unknown'),
                                        'relevance_score': relevance_score,
                                        'source_file': file,
                                        'processing_status': img_data.get('processing_status', 'Unknown'),
                                        'batch_id': 'Legacy'
                                    })
                        else:
                            # Single image result
                            relevance_score = self._calculate_relevance(data, search_query)
                            if relevance_score > 0:
                                search_results.append({
                                    'image_name': data.get('image_name', 'Unknown'),
                                    'image_path': data.get('image_path', 'Unknown'),
                                    'upload_path': data.get('upload_path', 'Unknown'),
                                    'context': data.get('context', ''),
                                    'image_size': data.get('image_size', {}),
                                    'timestamp': data.get('timestamp', 'Unknown'),
                                    'relevance_score': relevance_score,
                                    'source_file': file,
                                    'processing_status': data.get('processing_status', 'Unknown'),
                                    'batch_id': 'Single'
                                })
                                
            except Exception as e:
                print(f"⚠️ Error reading {file}: {str(e)}")
                continue
        
        # Sort by relevance score (highest first) and limit results
        search_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        search_results = search_results[:max_results]
        
        print(f"✅ Found {len(search_results)} relevant images")
        return search_results
    
    def _calculate_relevance(self, image_data: dict, search_query: str) -> float:
        """
        Calculate relevance score between image data and search query.
        
        Args:
            image_data: Image data dictionary
            search_query: Search query string
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        if not search_query or not image_data:
            return 0.0
        
        # Convert to lowercase for comparison
        query_lower = search_query.lower()
        context_lower = image_data.get('context', '').lower()
        image_name_lower = image_data.get('image_name', '').lower()
        
        # Check if query words appear in context
        query_words = query_lower.split()
        context_words = context_lower.split()
        
        # Calculate word overlap
        matching_words = sum(1 for word in query_words if word in context_words)
        word_relevance = matching_words / len(query_words) if query_words else 0.0
        
        # Check for exact phrase matches
        phrase_relevance = 0.0
        if len(query_words) > 1:
            # Check for consecutive word matches
            for i in range(len(context_words) - len(query_words) + 1):
                if context_words[i:i+len(query_words)] == query_words:
                    phrase_relevance = 1.0
                    break
        
        # Check image name relevance
        name_relevance = 0.0
        if any(word in image_name_lower for word in query_words):
            name_relevance = 0.5
        
        # Weighted combination
        final_score = (word_relevance * 0.6) + (phrase_relevance * 0.3) + (name_relevance * 0.1)
        
        return min(final_score, 1.0)
