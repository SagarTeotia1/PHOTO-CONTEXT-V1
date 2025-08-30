#!/usr/bin/env python3
"""
Command-line interface for Image Context Analyzer
"""

import argparse
import os
import sys
from dotenv import load_dotenv
from image_processor import ImageProcessor

def main():
    parser = argparse.ArgumentParser(
        description="Process images with Gemini 2.5 Pro and save context to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py image.jpg
  python cli.py image.jpg --prompt "Describe the colors and mood"
  python cli.py image.jpg --output my_analysis.json
  python cli.py --batch images_folder/
  python cli.py --history
        """
    )
    
    parser.add_argument(
        "image_path",
        nargs="?",
        help="Path to the image file to process"
    )
    
    parser.add_argument(
        "--prompt", "-p",
        help="Custom prompt for image analysis"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Custom output filename for JSON (without .json extension)"
    )
    
    parser.add_argument(
        "--batch", "-b",
        help="Process all images in a directory"
    )
    
    parser.add_argument(
        "--history", "-H",
        action="store_true",
        help="Show processing history"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment variables")
        print("Please set your Gemini API key in a .env file or environment variable")
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    try:
        processor = ImageProcessor(api_key)
        if args.verbose:
            print("✅ Gemini API connected successfully!")
    except Exception as e:
        print(f"❌ Error: Failed to initialize Gemini API: {str(e)}")
        sys.exit(1)
    
    # Handle different modes
    if args.history:
        show_history(processor)
    elif args.batch:
        process_batch(processor, args.batch, args.prompt, args.verbose)
    elif args.image_path:
        process_single(processor, args.image_path, args.prompt, args.output, args.verbose)
    else:
        parser.print_help()
        sys.exit(1)

def show_history(processor):
    """Display processing history."""
    print("📋 Processing History:")
    print("-" * 50)
    
    history = processor.get_processing_history()
    
    if not history:
        print("No processed images found.")
        return
    
    for i, item in enumerate(history, 1):
        print(f"{i}. 📸 {item['image_name']}")
        print(f"   📅 {item['timestamp']}")
        print(f"   📁 {item['filename']}")
        print(f"   ✅ {item['status']}")
        print()

def process_single(processor, image_path, prompt, output_filename, verbose):
    """Process a single image."""
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)
    
    if verbose:
        print(f"🖼️ Processing image: {image_path}")
        if prompt:
            print(f"📝 Using custom prompt: {prompt}")
    
    try:
        # Process image
        result = processor.process_image(image_path, prompt)
        
        if result["processing_status"] == "success":
            # Save to JSON
            json_path = processor.save_to_json(result, output_filename)
            
            print(f"✅ Image processed successfully!")
            print(f"📁 JSON saved to: {json_path}")
            
            if verbose:
                print("\n📊 Analysis Results:")
                print(f"   Image: {result['image_name']}")
                print(f"   Size: {result['image_size']['width']}x{result['image_size']['height']}")
                print(f"   Format: {result['image_size']['format']}")
                print(f"   Context length: {len(result['context'])} characters")
                print(f"\nContext preview: {result['context'][:200]}...")
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error processing image: {str(e)}")
        sys.exit(1)

def process_batch(processor, directory, prompt, verbose):
    """Process all images in a directory."""
    if not os.path.exists(directory):
        print(f"❌ Error: Directory not found: {directory}")
        sys.exit(1)
    
    if not os.path.isdir(directory):
        print(f"❌ Error: Path is not a directory: {directory}")
        sys.exit(1)
    
    # Supported image extensions
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    
    # Find image files
    image_files = []
    for file in os.listdir(directory):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(os.path.join(directory, file))
    
    if not image_files:
        print(f"❌ No image files found in directory: {directory}")
        sys.exit(1)
    
    print(f"🖼️ Found {len(image_files)} images to process")
    if prompt:
        print(f"📝 Using custom prompt: {prompt}")
    print()
    
    successful = 0
    failed = 0
    
    for i, image_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] Processing: {os.path.basename(image_path)}")
        
        try:
            result = processor.process_image(image_path, prompt)
            
            if result["processing_status"] == "success":
                # Save to JSON with image name
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                json_path = processor.save_to_json(result, f"{base_name}_analysis")
                
                print(f"   ✅ Success - Saved to: {os.path.basename(json_path)}")
                successful += 1
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            failed += 1
        
        print()
    
    # Summary
    print("=" * 50)
    print(f"📊 Batch Processing Complete!")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📁 Total: {len(image_files)}")
    print(f"   📂 Results saved in: {processor.output_dir}")

if __name__ == "__main__":
    main()
