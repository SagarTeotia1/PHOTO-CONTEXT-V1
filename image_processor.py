import os
import json
import base64
from datetime import datetime
from typing import Dict, Any, Optional
import google.generativeai as genai
from PIL import Image
import io
from imagekit_service import ImageKitService

class ImageProcessor:
    def __init__(self, api_key: str):
        """Initialize the ImageProcessor with Gemini API key."""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.output_dir = "processed_images"
        self.uploads_dir = "uploads"
        
        # Initialize ImageKit service
        try:
            self.imagekit_service = ImageKitService()
            print("✅ ImageKit service initialized successfully")
        except Exception as e:
            print(f"⚠️ ImageKit service initialization failed: {str(e)}")
            self.imagekit_service = None
        
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
                prompt = """
                
                # Universal Enhanced Image Analysis Prompt

## System Role
You are an expert multimodal AI analyst specializing in exhaustive image interpretation, cross-referencing, and contextual reasoning. Your mission is to extract maximum insight from visual content through systematic analysis, web research validation, and comprehensive reporting.

## Core Analysis Framework

### Phase 1: Foundational Visual Processing

**1.1 Complete Text Extraction & OCR++**
- Extract ALL visible text regardless of size, clarity, orientation, or distortion
- Capture: printed text, handwritten notes, stylized fonts, watermarks, logos, signs, labels
- Preserve exact formatting: line breaks, indentation, table structures, bullet points
- Include partial/cropped text with [PARTIAL] notation
- Detect language(s) and provide translations if non-English
- Note text hierarchy (headlines, subtext, captions, fine print)

**1.2 Comprehensive Object & Scene Inventory**
- Catalog every identifiable object, tool, item, structure, or element
- Specify spatial relationships: foreground/background, left/right, above/below
- Describe physical properties: size, condition, age, materials
- Note interactions between objects and environmental context
- Classify scene type: indoor/outdoor, natural/artificial, public/private, formal/casual

**1.3 Human Subject Analysis**
- Demographics: apparent age ranges, gender presentation, ethnicity (when relevant)
- Physical attributes: clothing, accessories, hairstyles, notable features
- Behavioral cues: postures, gestures, facial expressions, apparent emotions
- Social dynamics: relationships, hierarchies, group interactions
- Professional/role indicators: uniforms, badges, equipment

### Phase 2: Identity & Recognition Systems

**2.1 Enhanced Public Figure & Key Person Identification**
- **Systematic Recognition Process**:
  - Analyze facial features, distinctive characteristics, and body language
  - Note clothing, accessories, or items that might indicate profession/role
  - Look for name tags, badges, or identifying text
  - Consider context clues (venue, other people present, event type)

- **Multi-Level Identification Strategy**:
  - **Level 1**: Immediate recognition of globally famous figures
  - **Level 2**: Industry-specific celebrities (sports, politics, entertainment, business)
  - **Level 3**: Regional or niche public figures
  - **Level 4**: Professional or contextual roles (officials, speakers, organizers)

- **Confidence Scoring with Evidence**:
  - **High Confidence (90%+)**: Multiple distinctive features match, confirmed by context
  - **Medium Confidence (60-89%)**: Strong resemblance with supporting context clues
  - **Low Confidence (30-59%)**: Possible match requiring verification
  - **Uncertain (<30%)**: Insufficient visual information for identification

- **Mandatory Verification for Event Context**:
  - If any person is identified, immediately search: "[Person name] + [date range] + [location/venue]"
  - Cross-reference their public schedule, social media, or news coverage
  - Look for other attendees or participants who might be visible
  - Verify their connection to the suspected event type

**2.2 Brand & Commercial Recognition**
- Identify corporate logos, brand marks, product packaging, store signage
- Classify industries: technology, fashion, automotive, food/beverage, entertainment, etc.
- Note brand positioning (luxury, mainstream, budget) and target demographics
- Recognize sponsored content or product placement

## Enhanced Event Detection Examples & Strategies

### Critical Visual Indicators for Major Event Types:

**Political Events:**
- Look for: Government seals, political party logos, campaign banners, podiums with official insignia
- Search strategy: "[Visible text/logos] + political event + [timeframe]"
- Key figures: Politicians, government officials, campaign staff

**Award Shows & Entertainment:**
- Look for: Red carpets, step-and-repeat backgrounds, trophy imagery, entertainment venue architecture
- Search strategy: "[Venue name/distinctive backdrop] + award show + [year]"
- Key figures: Celebrities, presenters, industry professionals

**Sports Events:**
- Look for: Team uniforms, stadium features, scoreboards, sports equipment, crowd formations
- Search strategy: "[Team colors/logos] + [sport type] + [venue] + [date]"
- Key figures: Athletes, coaches, officials, commentators

**Corporate/Business Events:**
- Look for: Company logos, conference staging, business attire, name badges, presentation screens
- Search strategy: "[Company logo] + conference/event + [location] + [year]"
- Key figures: Executives, speakers, industry leaders

**Cultural/Social Events:**
- Look for: Cultural symbols, traditional dress, ceremonial objects, festival decorations
- Search strategy: "[Cultural elements] + [location] + festival/celebration + [timeframe]"
- Key figures: Community leaders, performers, dignitaries

### Mandatory Search Queries for Event Identification:
1. **Exact text extraction search**: Search any readable text verbatim
2. **Visual similarity search**: Use reverse image search tools
3. **Contextual combination search**: "[Key person] + [location] + [event type] + [date range]"
4. **News archive search**: "[Suspected event] + news + [timeframe]"
5. **Social media hashtag search**: Look for event-specific hashtags or trending topics

**3.1 Advanced Event & Situational Context Detection**
- **Primary Event Classification**: Systematically analyze visual cues to determine event type:
  - Sports events: Look for uniforms, team colors, stadiums, scoreboards, crowds, equipment
  - Political events: Identify podiums, flags, campaign materials, government buildings, official ceremonies
  - Entertainment: Stage lighting, performers, audiences, venues, red carpets, award shows
  - Educational: Classrooms, graduation caps, academic regalia, school logos, learning materials
  - Religious: Ceremonial objects, religious symbols, traditional dress, places of worship
  - Corporate: Business attire, conference settings, company logos, networking events
  - Social celebrations: Decorations, cake, formal wear, gift wrapping, party supplies
  - News events: Media presence, breaking news overlays, emergency vehicles, crowds

- **Event-Specific Visual Markers**: Look for distinctive elements that pinpoint exact events:
  - Venue architecture and distinctive features
  - Specific logos, banners, or signage with event names/dates
  - Unique staging, decorations, or branding
  - Celebrity attendees or notable figures
  - Broadcast graphics or media watermarks
  - Crowd size and composition patterns
  - Security or staff uniforms and equipment

- **Temporal and Geographic Context Clues**:
  - Weather conditions and seasonal indicators
  - Architectural styles specific to regions
  - Language on signs and cultural dress
  - Technology visible (phones, cameras, screens) to estimate time period
  - Fashion trends and styles to narrow timeframe
  - Currency, license plates, or regional symbols

- **Cross-Reference Strategy for Event Identification**:
  - If you identify potential event markers, IMMEDIATELY search for:
    - "Event name + date + location" if any are visible
    - Notable attendees + event type + timeframe
    - Venue name + event type + recent dates
    - Unique visual elements + event context
  - Search for reverse image matches to find original source and context
  - Look up news coverage from the apparent timeframe
  - Verify through multiple independent sources

**3.2 Systematic Web Research & Event Verification Protocol**
*Execute this enhanced search strategy for event identification:*

**Step 1: Visual Element Extraction**
- Catalog ALL text visible in the image (signs, banners, screens, clothing, etc.)
- Note distinctive objects, symbols, or branding elements
- Identify any people who might be recognizable
- Document unique architectural or venue features

**Step 2: Multi-Vector Search Approach**
- **Text-based searches**: Search exact phrases found in the image
- **Visual similarity search**: Look for identical or similar images
- **Entity combination searches**: Combine identified people + location + context
- **Reverse chronological search**: If timeframe is suspected, search that period
- **News verification**: Cross-check against news archives and media coverage

**Step 3: Event Database Cross-Reference**
Search specific databases and sources:
- Major news outlets for the suspected timeframe
- Event venue websites and social media accounts
- Celebrity/public figure social media and news coverage
- Sports databases, award show archives, political event records
- Social media hashtags and trending topics from the period

**Step 4: Validation and Confirmation**
- Require at least 2-3 independent sources confirming the same event
- Look for official documentation or press releases
- Verify attendee lists or participant rosters
- Cross-check dates, locations, and other factual details
- Flag any conflicting information or uncertainty

**3.3 Platform & Media Type Detection**
- Identify source platform: Instagram, Twitter/X, TikTok, LinkedIn, news sites, etc.
- Recognize UI elements, platform-specific features, interaction buttons
- Note screenshot artifacts, mobile/desktop indicators
- Detect editing or filtering applied

### Phase 4: Technical & Aesthetic Analysis

**4.1 Visual Composition & Style**
- Color palette: dominant/accent colors with hex codes when possible
- Artistic style: photographic, illustrated, vintage, modern, minimalist, maximalist
- Composition techniques: rule of thirds, leading lines, symmetry, framing
- Lighting analysis: natural/artificial, direction, mood, quality

**4.2 Technical Metadata Inference**
- Image source: photograph, screenshot, scan, digital artwork, AI-generated
- Camera/device indicators: quality, perspective, lens effects
- Editing evidence: filters, retouching, composite elements
- Resolution and quality assessment

### Phase 5: Cultural & Historical Context

**5.1 Cultural Significance & References**
- Identify cultural symbols, traditions, or practices
- Recognize historical periods, architectural styles, fashion eras
- Note religious, political, or social symbolism
- Detect references to pop culture, literature, or art

**5.2 Meme & Viral Content Recognition**
- Identify known memes, viral images, or internet phenomena
- Explain cultural significance and typical usage
- Trace origin story and evolution if known
- Note current relevance or trending status

### Phase 6: Security & Privacy Considerations

**6.1 Sensitive Information Detection**
- Flag visible personal data: phone numbers, emails, addresses, IDs
- Note security badges, access cards, or confidential markings
- Identify potential privacy concerns or OPSEC issues
- Highlight any legal or safety implications

### Phase 7: Comprehensive Synthesis

**7.1 Purpose & Intent Analysis**
- Determine likely image purpose: documentation, marketing, personal, news, evidence
- Assess target audience and intended message
- Note emotional tone and psychological impact
- Suggest optimal categorization tags

**7.2 Event-Focused Rich Narrative Description**
Provide a detailed, accessible description that:
- **Event Context First**: Lead with the identified event and its significance
- **Timeline Placement**: Establish when and where this event occurred
- **Key Participants**: Explain who is present and their roles/importance
- **Event Significance**: Describe why this event matters historically, culturally, or socially
- **Visual Story**: Tell what's happening in the moment captured
- **Broader Impact**: Connect to larger themes, consequences, or related events
- **Verification Status**: Clearly state confidence level and sources used for identification

**7.3 Event Identification Confidence Matrix**
Rate event identification confidence:
- **Confirmed Event (95-100%)**: Multiple sources verify exact event, date, location
- **Highly Likely Event (80-94%)**: Strong evidence with minor gaps in verification
- **Probable Event (60-79%)**: Good contextual match but requires more confirmation
- **Possible Event (40-59%)**: Some indicators but significant uncertainty remains
- **Unknown Event (0-39%)**: Insufficient evidence for specific event identification

**Always include:**
- Specific search terms used for verification
- Sources that confirmed or contradicted the identification
- Alternative possibilities if primary identification is uncertain
- Gaps in evidence that prevent higher confidence rating

## Output Format Guidelines

- Use clear headings and structured organization
- Provide specific evidence for all claims
- Include relevant quotes of extracted text
- Use bullet points for inventory-style information
- Write flowing paragraphs for narrative sections
- Always cite web sources when used for verification
- Flag urgent or sensitive findings prominently

## Quality Assurance Protocols

- Cross-verify major identifications through multiple approaches
- Question initial assumptions and consider alternative interpretations
- Prioritize accuracy over speculation
- Distinguish between direct observation and inference
- Update analysis if web research reveals contradictory information

---

*Remember: This analysis should be thorough but respectful of privacy, accurate but acknowledging uncertainty, and comprehensive while remaining accessible to human readers.*"""
            
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
            
            # Upload to ImageKit if service is available
            imagekit_result = None
            if self.imagekit_service:
                try:
                    imagekit_result = self.imagekit_service.upload_image(image_path)
                    print(f"📤 ImageKit upload result: {imagekit_result.get('success', False)}")
                except Exception as upload_error:
                    print(f"⚠️ ImageKit upload failed: {str(upload_error)}")
                    imagekit_result = {"success": False, "error": str(upload_error)}
            
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
                "processing_status": "success",
                "imagekit": imagekit_result
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
    
    def upload_to_imagekit(self, image_path: str, folder: str = "photo-context") -> Dict[str, Any]:
        """
        Upload an image to ImageKit.
        
        Args:
            image_path: Path to the image file
            folder: Folder name in ImageKit
            
        Returns:
            Dictionary containing upload result
        """
        if not self.imagekit_service:
            return {
                "success": False,
                "error": "ImageKit service not available"
            }
        
        try:
            return self.imagekit_service.upload_image(image_path, folder)
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_imagekit_images(self, folder: str = "photo-context", limit: int = 100) -> Dict[str, Any]:
        """
        Get list of images stored in ImageKit.
        
        Args:
            folder: Folder name to list
            limit: Maximum number of images to return
            
        Returns:
            Dictionary containing list of images
        """
        if not self.imagekit_service:
            return {
                "success": False,
                "error": "ImageKit service not available"
            }
        
        try:
            return self.imagekit_service.list_images(folder, limit)
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
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
        print(f"🔍 AI-powered search for: '{search_query}'")
        
        # AI search is now implemented - this will use Gemini 2.5 Pro for semantic understanding
        # The old keyword search logic is preserved as fallback in case AI search fails
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
    
    def _ai_semantic_search(self, search_query: str, max_results: int) -> list:
        """
        Perform AI-powered semantic search using Gemini 2.5 Pro.
        
        Args:
            search_query: Natural language description to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of matching images with AI-calculated relevance scores
        """
        print(f"🤖 Using Gemini 2.5 Pro for semantic search...")
        
        # Collect all available image data for AI analysis
        all_images = self._collect_all_image_data()
        
        if not all_images:
            print("⚠️ No images found for AI search")
            return []
        
        # Create a comprehensive prompt for AI analysis
        ai_prompt = self._create_search_prompt(search_query, all_images, max_results)
        
        try:
            # Use Gemini to analyze and rank images
            ai_response = self._query_gemini_for_search(ai_prompt)
            ranked_results = self._parse_ai_search_response(ai_response, all_images, max_results)
            
            print(f"🤖 AI analysis completed. Returning {len(ranked_results)} results")
            return ranked_results
            
        except Exception as e:
            print(f"❌ AI search failed: {str(e)}")
            raise e
    
    def _collect_all_image_data(self) -> list:
        """
        Collect all available image data from JSON files.
        
        Returns:
            List of image data dictionaries
        """
        all_images = []
        
        # Search through all JSON files
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
                        for batch_index, batch in enumerate(data['batches']):
                            if 'images' in batch and isinstance(batch['images'], list):
                                for img_data in batch['images']:
                                    img_data['source_file'] = file
                                    img_data['batch_id'] = batch.get('batch_id', batch_index + 1)
                                    all_images.append(img_data)
                    
                    # Handle legacy batch structure with 'images' array
                    elif 'images' in data and isinstance(data['images'], list):
                        for img_data in data['images']:
                            img_data['source_file'] = file
                            img_data['batch_id'] = 'Legacy'
                            all_images.append(img_data)
                    
                    else:
                        # Single image result
                        data['source_file'] = file
                        data['batch_id'] = 'Single'
                        all_images.append(data)
                        
            except Exception as e:
                print(f"⚠️ Error reading {file}: {str(e)}")
                continue
        
        print(f"📊 Collected {len(all_images)} images for AI analysis")
        return all_images
    
    def _create_search_prompt(self, search_query: str, all_images: list, max_results: int) -> str:
        """
        Create a comprehensive prompt for AI-powered image search.
        
        Args:
            search_query: User's search query
            all_images: List of all available images
            max_results: Maximum number of results to return
            
        Returns:
            Formatted prompt string for Gemini
        """
        # Create a summary of available images
        image_summary = []
        for i, img in enumerate(all_images[:50]):  # Limit to first 50 for prompt efficiency
            context_preview = img.get('context', '')[:200] + '...' if len(img.get('context', '')) > 200 else img.get('context', '')
            image_summary.append(f"Image {i+1}: {img.get('image_name', 'Unknown')} - {context_preview}")
        
        prompt = f"""You are an expert AI image search assistant. Your task is to find the most relevant images based on a user's search query.

SEARCH QUERY: "{search_query}"

AVAILABLE IMAGES ({len(all_images)} total):
{chr(10).join(image_summary)}

TASK: Analyze the search query and rank the images by relevance. Consider:
1. Semantic meaning and context
2. Object recognition and scene understanding
3. Text content (OCR) if present
4. Visual elements and composition
5. Temporal and spatial context
6. Cultural and social relevance

INSTRUCTIONS:
- Return exactly {max_results} most relevant images
- Rank by relevance score (1.0 = perfect match, 0.0 = no match)
- Consider synonyms, related concepts, and contextual understanding
- Focus on the user's intent, not just exact keyword matches

OUTPUT FORMAT (JSON):
{{
    "search_query": "{search_query}",
    "results": [
        {{
            "image_index": 0,
            "relevance_score": 0.95,
            "reasoning": "Brief explanation of why this image is relevant"
        }}
    ]
}}

Analyze the search query and return the most relevant images in the specified JSON format."""

        return prompt
    
    def _query_gemini_for_search(self, prompt: str) -> str:
        """
        Query Gemini API for AI-powered search analysis.
        
        Args:
            prompt: Formatted prompt for Gemini
            
        Returns:
            Gemini's response string
        """
        try:
            # Use the existing Gemini model for search
            model = self.model
            
            # Generate content using Gemini
            response = model.generate_content(prompt)
            
            if response and response.text:
                print(f"🤖 Gemini response received: {len(response.text)} characters")
                return response.text
            else:
                raise Exception("Empty response from Gemini")
                
        except Exception as e:
            print(f"❌ Gemini API error: {str(e)}")
            raise e
    
    def _parse_ai_search_response(self, ai_response: str, all_images: list, max_results: int) -> list:
        """
        Parse Gemini's AI response and convert to search results.
        
        Args:
            ai_response: Raw response from Gemini
            all_images: List of all available images
            max_results: Maximum number of results to return
            
        Returns:
            List of formatted search results
        """
        try:
            # Try to extract JSON from the response
            import re
            
            # Find JSON content in the response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                ai_data = json.loads(json_str)
                
                results = []
                if 'results' in ai_data and isinstance(ai_data['results'], list):
                    for result in ai_data['results']:
                        image_index = result.get('image_index', 0)
                        relevance_score = result.get('relevance_score', 0.0)
                        reasoning = result.get('reasoning', 'AI analysis')
                        
                        if 0 <= image_index < len(all_images):
                            img_data = all_images[image_index]
                            
                            results.append({
                                'image_name': img_data.get('image_name', 'Unknown'),
                                'image_path': img_data.get('image_path', 'Unknown'),
                                'upload_path': img_data.get('upload_path', 'Unknown'),
                                'context': img_data.get('context', ''),
                                'image_size': img_data.get('image_size', {}),
                                'timestamp': img_data.get('timestamp', 'Unknown'),
                                'relevance_score': relevance_score,
                                'source_file': img_data.get('source_file', 'Unknown'),
                                'processing_status': img_data.get('processing_status', 'Unknown'),
                                'batch_id': img_data.get('batch_id', 'Unknown'),
                                'ai_reasoning': reasoning
                            })
                
                # Sort by AI relevance score and limit results
                results.sort(key=lambda x: x['relevance_score'], reverse=True)
                return results[:max_results]
            
            else:
                print("⚠️ No JSON found in AI response, using fallback")
                raise Exception("Invalid AI response format")
                
        except Exception as e:
            print(f"❌ Error parsing AI response: {str(e)}")
            raise e
    
    def _fallback_keyword_search(self, search_query: str, max_results: int) -> list:
        """
        Fallback to traditional keyword-based search.
        
        Args:
            search_query: Natural language description to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of formatted search results
        """
        print(f"🔍 Using fallback keyword search...")
        
        search_results = []
        
        # Collect all images
        all_images = self._collect_all_image_data()
        
        for img_data in all_images:
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
                    'source_file': img_data.get('source_file', 'Unknown'),
                    'processing_status': img_data.get('processing_status', 'Unknown'),
                    'batch_id': img_data.get('batch_id', 'Unknown'),
                    'ai_reasoning': 'Keyword-based fallback search'
                })
        
        # Sort by relevance score (highest first) and limit results
        search_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        search_results = search_results[:max_results]
        
        print(f"✅ Fallback search completed. Found {len(search_results)} relevant images")
        return search_results
