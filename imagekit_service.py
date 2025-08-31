import os
from typing import Dict, Any, Optional
from imagekitio import ImageKit
import requests
from PIL import Image
import io

class ImageKitService:
    def __init__(self):
        """Initialize ImageKit service with credentials from environment variables."""
        self.imagekit_id = os.getenv("IMAGEKIT_ID",)
        self.url_endpoint = os.getenv("IMAGEKIT_URL_ENDPOINT",)
        self.public_key = os.getenv("IMAGEKIT_PUBLIC_KEY",)
        self.private_key = os.getenv("IMAGEKIT_PRIVATE_KEY", )
        
        # Initialize ImageKit client
        self.imagekit = ImageKit(
            private_key=self.private_key,
            public_key=self.public_key,
            url_endpoint=self.url_endpoint
        )
        
        print(f"✅ ImageKit service initialized for endpoint: {self.url_endpoint}")
    
    def upload_image(self, image_path: str, folder: str = "photo-context") -> Dict[str, Any]:
        """
        Upload an image to ImageKit.
        
        Args:
            image_path: Path to the local image file
            folder: Folder name in ImageKit (default: "photo-context")
            
        Returns:
            Dictionary containing upload result with ImageKit URL and metadata
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Get file info before reading
            file_name = os.path.basename(image_path)
            file_size_on_disk = os.path.getsize(image_path)
            print(f"📁 File info: {file_name} (Size on disk: {file_size_on_disk:,} bytes)")
            
            # Read the image file with error checking
            try:
                with open(image_path, 'rb') as file:
                    image_data = file.read()
                    actual_read_size = len(image_data)
                    print(f"📖 File read: {actual_read_size:,} bytes read from disk")
                    
                    if actual_read_size != file_size_on_disk:
                        print(f"⚠️ Warning: Read size ({actual_read_size:,}) != Disk size ({file_size_on_disk:,})")
                    
                    if actual_read_size == 0:
                        raise ValueError("File is empty or could not be read")
                
                # Verify file integrity by checking first and last few bytes
                if actual_read_size > 100:
                    first_bytes = image_data[:10].hex()
                    last_bytes = image_data[-10:].hex()
                    print(f"🔍 File integrity check: First 10 bytes: {first_bytes}, Last 10 bytes: {last_bytes}")
                    
            except Exception as read_error:
                raise Exception(f"Failed to read file {image_path}: {str(read_error)}")
            
            # Try simple upload first without complex options
            print(f"📤 Uploading {file_name} to ImageKit...")
            
            # Upload to ImageKit without options for now
            result = self.imagekit.upload_file(
                file=image_data,
                file_name=file_name
            )
            
            # Check for errors in the result
            if hasattr(result, 'error') and result.error:
                raise Exception(f"ImageKit upload failed: {result.error.message}")
            
            # Debug: Print result object details
            print(f"🔍 Upload result object type: {type(result)}")
            print(f"🔍 Upload result attributes: {dir(result)}")
            
            # Extract upload details - handle both old and new result formats
            uploaded_size = getattr(result, 'size', None)
            if uploaded_size and uploaded_size != actual_read_size:
                print(f"⚠️ Warning: Uploaded size ({uploaded_size:,}) != Original size ({actual_read_size:,})")
            
            upload_result = {
                "success": True,
                "imagekit_url": getattr(result, 'url', None),
                "imagekit_id": getattr(result, 'file_id', None),
                "file_name": getattr(result, 'name', file_name),
                "file_size": uploaded_size or actual_read_size,
                "file_type": getattr(result, 'file_type', 'image/jpeg'),
                "folder": getattr(result, 'folder_name', folder),
                "tags": getattr(result, 'tags', ["photo-context", "ai-analysis"]),
                "metadata": getattr(result, 'metadata', {}),
                "version_id": getattr(result, 'version_id', None),
                "local_path": image_path,
                "original_size": actual_read_size,
                "uploaded_size": uploaded_size
            }
            
            print(f"✅ Image uploaded successfully to ImageKit")
            if upload_result["imagekit_url"]:
                print(f"   URL: {upload_result['imagekit_url']}")
            if upload_result["imagekit_id"]:
                print(f"   ID: {upload_result['imagekit_id']}")
            print(f"   Size: {upload_result['file_size']} bytes")
            
            return upload_result
            
        except Exception as e:
            print(f"❌ ImageKit upload failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "local_path": image_path
            }
    
    def upload_image_from_bytes(self, image_bytes: bytes, filename: str, folder: str = "photo-context") -> Dict[str, Any]:
        """
        Upload an image to ImageKit from bytes data.
        
        Args:
            image_bytes: Image data as bytes
            filename: Name for the uploaded file
            folder: Folder name in ImageKit (default: "photo-context")
            
        Returns:
            Dictionary containing upload result with ImageKit URL and metadata
        """
        try:
            # Try simple upload first without complex options
            print(f"📤 Uploading {filename} to ImageKit from bytes...")
            
            # Upload to ImageKit without options for now
            result = self.imagekit.upload_file(
                file=image_bytes,
                file_name=filename
            )
            
            # Check for errors in the result
            if hasattr(result, 'error') and result.error:
                raise Exception(f"ImageKit upload failed: {result.error.message}")
            
            # Extract upload details - handle both old and new result formats
            upload_result = {
                "success": True,
                "imagekit_url": getattr(result, 'url', None),
                "imagekit_id": getattr(result, 'file_id', None),
                "file_name": getattr(result, 'name', filename),
                "file_size": getattr(result, 'size', len(image_bytes)),
                "file_type": getattr(result, 'file_type', 'image/jpeg'),
                "folder": getattr(result, 'folder_name', folder),
                "tags": getattr(result, 'tags', ["photo-context", "ai-analysis"]),
                "metadata": getattr(result, 'metadata', {}),
                "version_id": getattr(result, 'version_id', None),
                "local_path": None
            }
            
            print(f"✅ Image uploaded successfully to ImageKit")
            if upload_result["imagekit_url"]:
                print(f"   URL: {upload_result['imagekit_url']}")
            if upload_result["imagekit_id"]:
                print(f"   ID: {upload_result['imagekit_id']}")
            
            return upload_result
            
        except Exception as e:
            print(f"❌ ImageKit upload failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }
    
    def delete_image(self, imagekit_id: str) -> Dict[str, Any]:
        """
        Delete an image from ImageKit.
        
        Args:
            imagekit_id: ImageKit file ID to delete
            
        Returns:
            Dictionary containing deletion result
        """
        try:
            print(f"🗑️ Deleting image {imagekit_id} from ImageKit...")
            result = self.imagekit.delete_file(imagekit_id)
            
            # Check for errors in the result
            if hasattr(result, 'error') and result.error:
                raise Exception(f"ImageKit deletion failed: {result.error.message}")
            
            print(f"✅ Image deleted successfully from ImageKit")
            return {
                "success": True,
                "deleted_id": imagekit_id,
                "message": "Image deleted successfully"
            }
            
        except Exception as e:
            print(f"❌ ImageKit deletion failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "imagekit_id": imagekit_id
            }
    
    def get_image_info(self, imagekit_id: str) -> Dict[str, Any]:
        """
        Get information about an image stored in ImageKit.
        
        Args:
            imagekit_id: ImageKit file ID
            
        Returns:
            Dictionary containing image information
        """
        try:
            print(f"🔍 Getting info for image {imagekit_id}...")
            result = self.imagekit.get_file_details(imagekit_id)
            
            # Check for errors in the result
            if hasattr(result, 'error') and result.error:
                raise Exception(f"ImageKit info retrieval failed: {result.error.message}")
            
            # Extract info - handle both old and new result formats
            image_info = {
                "success": True,
                "imagekit_url": getattr(result, 'url', None),
                "imagekit_id": getattr(result, 'file_id', None),
                "file_name": getattr(result, 'name', None),
                "file_size": getattr(result, 'size', None),
                "file_type": getattr(result, 'file_type', None),
                "folder": getattr(result, 'folder_name', None),
                "tags": getattr(result, 'tags', None),
                "metadata": getattr(result, 'metadata', {}),
                "version_id": getattr(result, 'version_id', None),
                "created_at": getattr(result, 'created_at', None),
                "updated_at": getattr(result, 'updated_at', None)
            }
            
            return image_info
            
        except Exception as e:
            print(f"❌ ImageKit info retrieval failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "imagekit_id": imagekit_id
            }
    
    def list_images(self, folder: str = "photo-context", limit: int = 100) -> Dict[str, Any]:
        """
        List images in a specific folder.
        
        Args:
            folder: Folder name to list (default: "photo-context")
            limit: Maximum number of images to return
            
        Returns:
            Dictionary containing list of images
        """
        try:
            print(f"📋 Listing images in folder: {folder}")
            result = self.imagekit.list_files({
                "path": folder,
                "limit": limit
            })
            
            # Check for errors in the result
            if hasattr(result, 'error') and result.error:
                raise Exception(f"ImageKit listing failed: {result.error.message}")
            
            images = []
            for file in result.list:
                images.append({
                    "imagekit_url": file.url,
                    "imagekit_id": file.file_id,
                    "file_name": file.name,
                    "file_size": file.size,
                    "file_type": file.file_type,
                    "folder": file.folder_name,
                    "tags": file.tags,
                    "created_at": file.created_at,
                    "updated_at": file.updated_at
                })
            
            return {
                "success": True,
                "folder": folder,
                "total_images": len(images),
                "images": images
            }
            
        except Exception as e:
            print(f"❌ ImageKit listing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "folder": folder
            }
    
    def optimize_image_url(self, imagekit_url: str, transformations: Dict[str, Any] = None) -> str:
        """
        Generate an optimized ImageKit URL with transformations.
        
        Args:
            imagekit_url: Base ImageKit URL
            transformations: Dictionary of transformations to apply
            
        Returns:
            Optimized ImageKit URL
        """
        if not transformations:
            return imagekit_url
        
        # Build transformation string
        transform_parts = []
        
        if "width" in transformations:
            transform_parts.append(f"w-{transformations['width']}")
        if "height" in transformations:
            transform_parts.append(f"h-{transformations['height']}")
        if "quality" in transformations:
            transform_parts.append(f"q-{transformations['quality']}")
        if "format" in transformations:
            transform_parts.append(f"f-{transformations['format']}")
        if "crop" in transformations:
            transform_parts.append(f"c-{transformations['crop']}")
        
        if transform_parts:
            # Insert transformations before the filename
            base_url = imagekit_url.rsplit('/', 1)[0]
            filename = imagekit_url.rsplit('/', 1)[1]
            return f"{base_url}/tr:{','.join(transform_parts)}/{filename}"
        
        return imagekit_url
