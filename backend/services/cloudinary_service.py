import cloudinary
import cloudinary.uploader
import cloudinary.utils
from dotenv import load_dotenv
import os
import hashlib
import time
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status, UploadFile
import base64
import io

load_dotenv()

class CloudinaryService:
    """Centralized Cloudinary service for PM Connect 3.0"""
    
    def __init__(self):
        self.cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "pm-connect-demo")
        self.api_key = os.getenv("CLOUDINARY_API_KEY", "")
        self.api_secret = os.getenv("CLOUDINARY_API_SECRET", "")
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True
        )
    
    async def upload_image(
        self, 
        file: UploadFile, 
        folder: str = "pm_connect",
        tags: Optional[List[str]] = None,
        public_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload image to Cloudinary with optimization"""
        try:
            # Validate content type
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only image files are allowed"
                )
            
            # Read file content
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Prepare upload parameters
            upload_params = {
                "folder": folder,
                "resource_type": "image",
                "transformation": [
                    {"quality": "auto:good"},
                    {"format": "auto"},
                    {"fetch_format": "auto"}
                ],
                "tags": tags or ["pm_connect", "auto_upload"],
                "overwrite": False,
                "unique_filename": True
            }
            
            if public_id:
                upload_params["public_id"] = public_id
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_content,
                **upload_params
            )
            
            return {
                "public_id": result["public_id"],
                "url": result["secure_url"],
                "width": result.get("width", 0),
                "height": result.get("height", 0),
                "format": result["format"],
                "bytes": result["bytes"],
                "created_at": result["created_at"],
                "version": result.get("version", 1)
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Image upload failed: {str(e)}"
            )
    
    async def upload_video(
        self,
        file: UploadFile,
        folder: str = "pm_connect/videos",
        enable_hls: bool = True,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Upload video with HLS streaming support"""
        try:
            # Validate content type
            if not file.content_type or not file.content_type.startswith('video/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only video files are allowed"
                )
            
            # Read file content
            file_content = await file.read()
            await file.seek(0)
            
            # Base upload parameters
            upload_params = {
                "folder": folder,
                "resource_type": "video",
                "tags": tags or ["pm_connect", "video"],
                "overwrite": False,
                "unique_filename": True
            }
            
            # Add HLS streaming configuration
            if enable_hls:
                upload_params["eager"] = [
                    {
                        "streaming_profile": "hd",
                        "format": "m3u8"
                    },
                    {
                        "streaming_profile": "sd",
                        "format": "m3u8"
                    }
                ]
                upload_params["eager_async"] = True
            
            # Upload video
            result = cloudinary.uploader.upload(
                file_content,
                **upload_params
            )
            
            # Generate streaming URLs
            streaming_urls = {}
            if enable_hls:
                base_url = f"https://res.cloudinary.com/{self.cloud_name}/video/upload"
                streaming_urls = {
                    "hls_hd": f"{base_url}/sp_hd/{result['public_id']}.m3u8",
                    "hls_sd": f"{base_url}/sp_sd/{result['public_id']}.m3u8",
                    "mp4_fallback": result["secure_url"]
                }
            
            return {
                "public_id": result["public_id"],
                "url": result["secure_url"],
                "duration": result.get("duration"),
                "width": result.get("width", 0),
                "height": result.get("height", 0),
                "format": result["format"],
                "bytes": result["bytes"],
                "streaming_urls": streaming_urls,
                "created_at": result["created_at"]
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Video upload failed: {str(e)}"
            )
    
    def generate_image_url(
        self,
        public_id: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: str = "fill",
        quality: str = "auto:good",
        format: str = "auto"
    ) -> str:
        """Generate optimized image URL with transformations"""
        
        transformations = []
        
        if width or height:
            transformation = {"crop": crop}
            if width:
                transformation["width"] = width
            if height:
                transformation["height"] = height
            transformations.append(transformation)
        
        transformations.extend([
            {"quality": quality},
            {"format": format},
            {"fetch_format": "auto"}
        ])
        
        return cloudinary.utils.cloudinary_url(
            public_id,
            transformation=transformations,
            secure=True
        )[0]
    
    def delete_asset(self, public_id: str, resource_type: str = "image") -> Dict[str, Any]:
        """Delete asset from Cloudinary"""
        try:
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type
            )
            return {
                "success": result.get("result") == "ok",
                "public_id": public_id,
                "result": result.get("result")
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete asset: {str(e)}"
            )
    
    def generate_signed_upload_params(
        self,
        folder: str,
        tags: List[str],
        resource_type: str = "auto"
    ) -> Dict[str, Any]:
        """Generate signed upload parameters for client-side uploads"""
        
        timestamp = int(time.time())
        
        params = {
            "timestamp": timestamp,
            "folder": folder,
            "tags": ",".join(tags),
            "resource_type": resource_type,
            "quality": "auto:good",
            "format": "auto"
        }
        
        # Generate signature
        params_to_sign = {k: v for k, v in params.items() if v is not None}
        signature = cloudinary.utils.api_sign_request(params_to_sign, self.api_secret)
        
        return {
            **params,
            "signature": signature,
            "api_key": self.api_key,
            "cloud_name": self.cloud_name
        }

# Global service instance
cloudinary_service = CloudinaryService()