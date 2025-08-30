import streamlit as st
import os
from dotenv import load_dotenv
from image_processor import ImageProcessor
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Image Context Analyzer",
    page_icon="🖼️",
    layout="wide"
)

def main():
    st.title("🖼️ Image Context Analyzer with Gemini 2.5 Pro")
    st.markdown("Upload an image and get detailed context analysis using Google's Gemini AI model")
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ Gemini API key not found! Please set GEMINI_API_KEY in your .env file")
        st.info("Get your API key from: https://makersuite.google.com/app/apikey")
        st.code("GEMINI_API_KEY=your_actual_api_key_here")
        return
    
    # Initialize processor
    try:
        processor = ImageProcessor(api_key)
        st.success("✅ Gemini API connected successfully!")
    except Exception as e:
        st.error(f"❌ Failed to initialize Gemini API: {str(e)}")
        return
    
    # Sidebar for options
    st.sidebar.header("⚙️ Options")
    
    # Custom prompt input
    custom_prompt = st.sidebar.text_area(
        "Custom Analysis Prompt (Optional)",
        value="Dynamic Universal Image Analysis Prompt\n\nSystem Role:\nYou are an advanced multimodal AI trained to perform exhaustive image analysis with maximum depth, precision, and creativity. Your job is not just to describe, but to extract, interpret, cross-reference, and contextualize every possible detail from an image.\n\nAnalyze the input image step by step and provide the most comprehensive extraction possible. Follow this layered approach:\n\n1. Raw Text Extraction (OCR++)\n2. Object & Scene Recognition\n3. People & Identity Clues\n4. Event / Situation Context\n5. Brand / Logo / Product Detection\n6. Colors, Style & Aesthetic\n7. Internet / Cultural Cross-Reference\n8. Metadata & Hidden Clues\n9. Contextual Reasoning\n10. Rich Human-Friendly Summary\n\nPlease be comprehensive and provide as much detail as possible.",
        height=200,
        help="Customize how Gemini analyzes your image"
    )
    
    # Custom filename input
    custom_filename = st.sidebar.text_input(
        "Custom JSON Filename (Optional)",
        placeholder="my_image_analysis.json",
        help="Leave empty for auto-generated timestamp-based filename"
    )
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 Upload Image")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
            help="Supported formats: PNG, JPG, JPEG, GIF, BMP, WEBP"
        )
        
        if uploaded_file is not None:
            # Display uploaded image
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
            
            # Process button
            if st.button("🚀 Process Image with Gemini", type="primary"):
                with st.spinner("Processing image with Gemini 2.5 Pro..."):
                    try:
                        # Save uploaded file temporarily
                        temp_path = f"temp_{uploaded_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Process image
                        result = processor.process_image(temp_path, custom_prompt)
                        
                        # Save to JSON
                        if result["processing_status"] == "success":
                            json_path = processor.save_to_json(result, custom_filename)
                            
                            # Clean up temp file
                            os.remove(temp_path)
                            
                            st.success(f"✅ Image processed successfully!")
                            st.info(f"📁 JSON saved to: {json_path}")
                            
                            # Display results
                            st.subheader("📊 Analysis Results")
                            st.json(result)
                            
                            # Download button for JSON
                            with open(json_path, 'r', encoding='utf-8') as f:
                                json_content = f.read()
                            
                            st.download_button(
                                label="📥 Download JSON",
                                data=json_content,
                                file_name=os.path.basename(json_path),
                                mime="application/json"
                            )
                        else:
                            st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                            os.remove(temp_path)
                            
                    except Exception as e:
                        st.error(f"❌ Error processing image: {str(e)}")
                        # Clean up temp file if it exists
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
    
    with col2:
        st.header("📋 Processing History")
        
        # Get processing history
        history = processor.get_processing_history()
        
        if not history:
            st.info("No processed images yet. Upload and process your first image!")
        else:
            st.info(f"Found {len(history)} processed images")
            
            # Display history
            for item in history[:10]:  # Show last 10
                with st.expander(f"📸 {item['image_name']} - {item['timestamp']}"):
                    st.write(f"**Status:** {item['status']}")
                    st.write(f"**File:** {item['filename']}")
                    
                    # Load and display JSON content
                    try:
                        with open(item['filepath'], 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        if item['status'] == 'success':
                            st.write("**Context:**")
                            st.write(data.get('context', 'No context available'))
                        else:
                            st.write(f"**Error:** {data.get('error', 'Unknown error')}")
                            
                    except Exception as e:
                        st.error(f"Error loading file: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Powered by:** Google Gemini 2.5 Pro | **Built with:** Streamlit & Python | "
        "[Get API Key](https://makersuite.google.com/app/apikey)"
    )

if __name__ == "__main__":
    main()
