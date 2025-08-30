# 🖼️ Image Context Analyzer

AI-powered image analysis using Google's Gemini 2.5 Pro

## ✨ Features

- **AI-Powered Analysis**: Intelligent image understanding with Gemini 2.5 Pro
- **Multiple Image Support**: Upload and process multiple images simultaneously
- **Smart Search**: Search through processed images using natural language descriptions
- **Image Storage**: Automatically stores uploaded images in organized folders
- **Multiple Formats**: Supports PNG, JPG, JPEG, GIF, BMP, and WEBP

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### 2. Installation

```bash
# Clone or download the project files
cd PHOTO-CONTEXT

# Install dependencies
pip install -r requirements.txt

# Set up your API key
# Copy env_example.txt to .env and add your actual API key
```

### 3. Configuration

Create a `.env` file in the project root:

```bash
# Copy the example file
cp env_example.txt .env

# Edit .env and add your actual Gemini API key
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Testing Multiple Image Processing

Before running the web server, test multiple image processing:

```bash
# Test multiple image processing
python test_multiple_images.py

# This will:
# - Verify your API key works
# - Test batch processing with multiple images
# - Confirm JSON saving works
# - Check image upload functionality
```

### 5. Testing Search Functionality

Test the search feature:

```bash
# Test search functionality
python test_search.py

# This will:
# - Verify search works with processed images
# - Test various search queries
# - Confirm relevance scoring works
```

## 🎯 Usage

### Web Interface

```bash
# Start the web server
python web_server.py
```

Then open your browser to `http://localhost:5000`

The web interface allows you to:
- Upload multiple images simultaneously
- Process images with Gemini 2.5 Pro
- Search through processed images using natural language descriptions
- View analysis results and download JSON files



## 📁 Project Structure

```
PHOTO-CONTEXT/
├── index.html            # Web interface
├── web_server.py         # Flask web server
├── image_processor.py    # Core image processing logic
├── requirements.txt      # Python dependencies
├── env_example.txt       # Environment variables template
├── README.md            # This file
├── processed_images/     # Output directory (created automatically)
│   └── *.json           # Generated analysis files
└── uploads/              # Uploaded images storage (created automatically)
    └── *.jpg, *.png, etc. # Stored image files
```

## 🔧 Core Components

### ImageProcessor Class (`image_processor.py`)

The main class that handles:
- Gemini API integration
- Image processing and analysis
- Multiple image batch processing
- Image storage in uploads folder
- JSON file generation and storage
- Smart search through processed images

### Web Interface (`index.html`)

A responsive web interface with:
- Modern, gradient-based design
- Image upload with preview
- Custom prompt configuration
- Real-time processing with Gemini

### Flask Web Server (`web_server.py`)

Web server with Gemini API integration:
- RESTful API endpoints
- Real image processing with Gemini
- File upload handling
- JSON storage and retrieval
- Image search API
- Image serving from uploads folder

## 📊 Output Format

### Single Image Processing

Each processed image generates a JSON file with:

```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "image_path": "/path/to/image.jpg",
  "image_name": "image.jpg",
  "image_size": {
    "width": 1920,
    "height": 1080,
    "format": "JPEG"
  },
  "prompt_used": "Analyze this image...",
  "context": "Detailed analysis from Gemini...",
  "processing_status": "success",
  "upload_path": "uploads/image_20240115_103000.jpg"
}
```

### Multiple Image Batch Processing

Batch processing creates a comprehensive JSON file containing all images:

```json
{
  "batch_timestamp": "2024-01-15T10:30:00.123456",
  "total_images": 3,
  "successful_images": 3,
  "failed_images": 0,
  "images": [
    {
      "timestamp": "2024-01-15T10:30:01.123456",
      "image_name": "image1.jpg",
      "image_size": {"width": 1920, "height": 1080, "format": "JPEG"},
      "context": "Detailed analysis...",
      "processing_status": "success",
      "upload_path": "uploads/image1_20240115_103001.jpg"
    },
    {
      "timestamp": "2024-01-15T10:30:02.123456",
      "image_name": "image2.jpg",
      "image_size": {"width": 800, "height": 600, "format": "PNG"},
      "context": "Detailed analysis...",
      "processing_status": "success",
      "upload_path": "uploads/image2_20240115_103002.png"
    }
  ],
  "batch_summary": "Successfully processed 3 out of 3 images",
  "processing_status": "completed"
}
```

## 🎨 Customization

### Custom Prompts

You can customize how Gemini analyzes your images:

```python
custom_prompt = """
Analyze this image focusing on:
1. Architectural elements and design
2. Historical significance
3. Cultural context
4. Technical details
"""
```

### Batch Processing

Process multiple images with the same prompt:

```bash
# Process all images in a folder
python cli.py --batch vacation_photos/ --prompt "Describe the location and activities"
```

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your `.env` file contains the correct `GEMINI_API_KEY`
2. **Image Format**: Check that your image is in a supported format
3. **File Permissions**: Ensure the script can write to the output directory
4. **Network Issues**: Check your internet connection for API calls

### Getting Help

- Verify your Gemini API key is valid
- Check the console/terminal for error messages
- Ensure all dependencies are installed correctly
- Try with a simple image first

## 🔒 Security Notes

- Never commit your `.env` file to version control
- Keep your API key secure and don't share it
- The API key is only used locally and not transmitted elsewhere

## 📈 Future Enhancements

Potential improvements:
- Support for video analysis
- Integration with cloud storage
- Advanced prompt templates
- Export to other formats (CSV, XML)
- Real-time processing with webhooks

## 🤝 Contributing

Feel free to:
- Report bugs and issues
- Suggest new features
- Submit pull requests
- Improve documentation

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Google Gemini AI for the powerful image analysis capabilities
- Streamlit for the excellent web framework
- Python community for the robust ecosystem

---

**Happy Image Analyzing! 🎉**

For questions or support, please check the troubleshooting section or create an issue in the project repository.
