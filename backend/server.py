from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Depends, Form, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date
import json
import base64
from bson import ObjectId
import pandas as pd
import io
from services.cloudinary_service import cloudinary_service
from services.auth_service import AuthService
from services.data_validation_service import DataValidationService
from services.excel_export_service import ExcelExportService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'pm_connect_db')]

# Initialize services
auth_service = AuthService(db)
data_validation_service = DataValidationService(db)
excel_export_service = ExcelExportService(db)

# Create the main app without a prefix
app = FastAPI(title="PM Connect 3.0 API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# File storage directories
UPLOAD_DIR = ROOT_DIR / "uploads"
AGENDA_DIR = UPLOAD_DIR / "agendas"
GALLERY_DIR = UPLOAD_DIR / "gallery"
CSV_DIR = UPLOAD_DIR / "csv"

# Create directories if they don't exist
for directory in [UPLOAD_DIR, AGENDA_DIR, GALLERY_DIR, CSV_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Security
security = HTTPBearer()

# ================== MODELS ==================

class InviteeCreate(BaseModel):
    employeeId: str
    employeeName: str
    cadre: str
    projectName: str

class Invitee(BaseModel):
    employeeId: str
    employeeName: str
    cadre: str
    projectName: str
    hasResponded: bool = False

class ResponseCreate(BaseModel):
    employeeId: str
    mobileNumber: str
    requiresAccommodation: bool
    arrivalDate: Optional[date] = None
    departureDate: Optional[date] = None
    foodPreference: str  # 'Veg', 'Non-Veg', 'Not Required'

class Response(BaseModel):
    responseId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employeeId: str
    mobileNumber: str
    requiresAccommodation: bool
    arrivalDate: Optional[date] = None
    departureDate: Optional[date] = None
    foodPreference: str
    submissionTimestamp: datetime = Field(default_factory=datetime.utcnow)

class GalleryPhoto(BaseModel):
    photoId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employeeId: str
    imageBase64: str  # Store as base64
    eventVersion: str  # 'PM Connect 1.0', 'PM Connect 2.0', 'PM Connect 3.0'
    uploadTimestamp: datetime = Field(default_factory=datetime.utcnow)

class Agenda(BaseModel):
    agendaId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agendaTitle: str
    pdfBase64: str  # Store PDF as base64
    uploadTimestamp: datetime = Field(default_factory=datetime.utcnow)

class CabAllocation(BaseModel):
    cabId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cabNumber: int
    assignedMembers: List[str]  # List of employeeIds
    pickupLocation: str
    pickupTime: str

class DashboardStats(BaseModel):
    totalInvitees: int
    rsvpYes: int
    rsvpNo: int
    accommodationRequests: int
    foodPreferences: Dict[str, int]

# ================== HELPER FUNCTIONS ==================

def convert_objectid(data):
    """Convert ObjectId to string in MongoDB documents"""
    if isinstance(data, list):
        return [convert_objectid(item) for item in data]
    elif isinstance(data, dict):
        return {key: str(value) if isinstance(value, ObjectId) else convert_objectid(value) for key, value in data.items()}
    return data

# ================== AUTHENTICATION ROUTES ==================

class LoginRequest(BaseModel):
    employeeCode: str
    password: str

class ChangePasswordRequest(BaseModel):
    employeeCode: str
    oldPassword: str
    newPassword: str

class SetOfficeTypeRequest(BaseModel):
    employeeCode: str
    officeType: str

class UserResponse(BaseModel):
    employeeId: str
    employeeName: str
    cadre: str
    projectName: str
    role: str
    isFirstLogin: bool
    mustChangePassword: bool
    officeType: Optional[str]
    permissions: List[str]

@api_router.post("/auth/login")
async def login(login_data: LoginRequest):
    """Authenticate user with employee code and password"""
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            login_data.employeeCode, 
            login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid employee code or password"
            )
        
        # Get user permissions
        permissions = await auth_service.get_user_permissions(user["employeeId"])
        
        # Create access token
        token_data = {
            "sub": user["employeeId"],
            "role": user["role"],
            "permissions": permissions
        }
        access_token = auth_service.create_access_token(token_data)
        
        # Log login activity
        await auth_service.log_user_activity(
            user["employeeId"], 
            "login", 
            {"login_time": datetime.utcnow().isoformat()}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "employeeId": user["employeeId"],
                "employeeName": user["employeeName"],
                "cadre": user.get("cadre", ""),
                "projectName": user.get("projectName", ""),
                "role": user["role"],
                "isFirstLogin": user.get("isFirstLogin", False),
                "mustChangePassword": user.get("mustChangePassword", False),
                "officeType": user.get("officeType"),
                "permissions": permissions
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@api_router.post("/auth/change-password")
async def change_password(password_data: ChangePasswordRequest):
    """Change user password"""
    try:
        success = await auth_service.change_password(
            password_data.employeeCode,
            password_data.oldPassword,
            password_data.newPassword
        )
        
        if success:
            # Log password change activity
            await auth_service.log_user_activity(
                password_data.employeeCode, 
                "password_changed"
            )
            
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )

@api_router.post("/auth/set-office-type")
async def set_office_type(office_data: SetOfficeTypeRequest):
    """Set user's office type during first login"""
    try:
        success = await auth_service.set_office_type(
            office_data.employeeCode,
            office_data.officeType
        )
        
        if success:
            # Log office type setting
            await auth_service.log_user_activity(
                office_data.employeeCode, 
                "office_type_set",
                {"office_type": office_data.officeType}
            )
            
            return {"message": "Office type set successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set office type: {str(e)}"
        )

@api_router.get("/auth/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user information"""
    try:
        # Verify token
        payload = auth_service.verify_access_token(credentials.credentials)
        employee_id = payload.get("sub")
        
        if not employee_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from database
        user = await db.users.find_one({"employeeId": employee_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get current permissions
        permissions = await auth_service.get_user_permissions(employee_id)
        
        return {
            "employeeId": user["employeeId"],
            "employeeName": user["employeeName"],
            "cadre": user.get("cadre", ""),
            "projectName": user.get("projectName", ""),
            "role": user["role"],
            "isFirstLogin": user.get("isFirstLogin", False),
            "mustChangePassword": user.get("mustChangePassword", False),
            "officeType": user.get("officeType"),
            "permissions": permissions,
            "lastLogin": user.get("lastLogin")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )

@api_router.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user and invalidate token"""
    try:
        # Verify token to get user info
        payload = auth_service.verify_access_token(credentials.credentials)
        employee_id = payload.get("sub")
        
        if employee_id:
            # Log logout activity
            await auth_service.log_user_activity(
                employee_id, 
                "logout",
                {"logout_time": datetime.utcnow().isoformat()}
            )
        
        # In a production system, you'd add the token to a blacklist
        # For now, we'll just confirm the logout
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        # Even if token verification fails, we'll allow logout
        return {"message": "Logged out successfully"}

# ================== INITIAL ADMIN SETUP ROUTE ==================

@api_router.post("/auth/create-admin")
async def create_initial_admin():
    """Create initial admin user for testing - should be secured in production"""
    try:
        # Check if admin already exists
        existing_admin = await db.users.find_one({"role": "admin"})
        if existing_admin:
            return {"message": "Admin user already exists", "admin_exists": True}
        
        # Create admin user
        admin_data = {
            "employeeId": "ADMIN001",
            "employeeName": "System Administrator",
            "email": "admin@jakson.com",
            "password": auth_service.hash_password("admin123"),
            "role": "admin",
            "isFirstLogin": False,
            "mustChangePassword": False,
            "officeType": "Head Office",
            "createdAt": datetime.utcnow(),
            "lastLogin": None,
            "isActive": True,
            "permissions": [
                "manage_invitees",
                "manage_responses", 
                "manage_agenda",
                "manage_gallery",
                "manage_cab_allocations",
                "export_data",
                "view_analytics"
            ]
        }
        
        await db.users.insert_one(admin_data)
        
        # Also create in invitees table for compatibility
        admin_invitee = {
            "employeeId": "ADMIN001",
            "employeeName": "System Administrator",
            "cadre": "Administrator",
            "projectName": "PM Connect 3.0",
            "hasResponded": True
        }
        
        await db.invitees.insert_one(admin_invitee)
        
        return {
            "message": "Initial admin user created successfully",
            "admin_id": "ADMIN001",
            "password": "admin123",
            "note": "Please change the password after first login"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin user: {str(e)}"
        )

# ================== INVITEE MANAGEMENT ROUTES ==================

@api_router.post("/invitees/bulk-upload")
async def bulk_upload_invitees(file: UploadFile = File(...)):
    """Upload CSV file with invitee data"""
    try:
        if not file.filename.endswith(('.csv', '.xlsx')):
            raise HTTPException(status_code=400, detail="File must be CSV or Excel format")
        
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Validate required columns
        required_columns = ['Employee ID', 'Employee Name', 'Cadre', 'Project Name']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"CSV must contain columns: {required_columns}")
        
        invitees = []
        for _, row in df.iterrows():
            invitee = {
                "employeeId": str(row['Employee ID']),
                "employeeName": str(row['Employee Name']),
                "cadre": str(row['Cadre']),
                "projectName": str(row['Project Name']),
                "hasResponded": False
            }
            invitees.append(invitee)
        
        # Clear existing invitees and insert new ones
        await db.invitees.delete_many({})
        result = await db.invitees.insert_many(invitees)
        
        return {"message": f"Successfully uploaded {len(invitees)} invitees", "inserted_count": len(result.inserted_ids)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@api_router.get("/invitees", response_model=List[Invitee])
async def get_invitees():
    """Get all invitees"""
    invitees = await db.invitees.find().to_list(1000)
    return [Invitee(**convert_objectid(invitee)) for invitee in invitees]

@api_router.get("/invitees/unresponded")
async def get_unresponded_invitees():
    """Get invitees who haven't responded yet"""
    invitees = await db.invitees.find({"hasResponded": False}).to_list(1000)
    return [{"employeeId": inv["employeeId"], "employeeName": inv["employeeName"], "cadre": inv["cadre"], "projectName": inv["projectName"]} for inv in invitees]

# ================== RESPONSE MANAGEMENT ROUTES ==================

@api_router.post("/responses")
async def submit_response(response_data: ResponseCreate):
    """Submit RSVP response"""
    try:
        # Check if invitee exists
        invitee = await db.invitees.find_one({"employeeId": response_data.employeeId})
        if not invitee:
            raise HTTPException(status_code=404, detail="Invitee not found")
        
        # Check if already responded
        existing_response = await db.responses.find_one({"employeeId": response_data.employeeId})
        if existing_response:
            raise HTTPException(status_code=400, detail="Response already submitted")
        
        # Create response
        response = Response(**response_data.dict())
        response_dict = response.dict()
        
        # Convert date objects to strings for MongoDB storage
        if response_dict.get('arrivalDate'):
            response_dict['arrivalDate'] = response_dict['arrivalDate'].isoformat()
        if response_dict.get('departureDate'):
            response_dict['departureDate'] = response_dict['departureDate'].isoformat()
            
        await db.responses.insert_one(response_dict)
        
        # Mark invitee as responded
        await db.invitees.update_one(
            {"employeeId": response_data.employeeId},
            {"$set": {"hasResponded": True}}
        )
        
        return {"message": "Response submitted successfully", "responseId": response.responseId}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting response: {str(e)}")

@api_router.get("/responses", response_model=List[Response])
async def get_responses():
    """Get all responses"""
    responses = await db.responses.find().to_list(1000)
    return [Response(**convert_objectid(response)) for response in responses]

@api_router.get("/responses/export")
async def export_responses():
    """Export responses to Excel format"""
    try:
        responses = await db.responses.find().to_list(1000)
        
        if not responses:
            return {"message": "No responses to export"}
        
        # Convert to DataFrame
        df_data = []
        for response in responses:
            df_data.append({
                "Employee ID": response.get("employeeId"),
                "Mobile Number": response.get("mobileNumber"),
                "Requires Accommodation": "Yes" if response.get("requiresAccommodation") else "No",
                "Arrival Date": response.get("arrivalDate"),
                "Departure Date": response.get("departureDate"),
                "Food Preference": response.get("foodPreference"),
                "Submission Time": response.get("submissionTimestamp")
            })
        
        df = pd.DataFrame(df_data)
        
        # Convert to Excel bytes
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, sheet_name='Responses')
        excel_bytes = excel_buffer.getvalue()
        
        # Convert to base64
        excel_base64 = base64.b64encode(excel_bytes).decode('utf-8')
        
        return {
            "excel_data": excel_base64,
            "filename": f"PM_Connect_Responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting responses: {str(e)}")

# ================== DASHBOARD ROUTES ==================

@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        total_invitees = await db.invitees.count_documents({})
        rsvp_yes = await db.invitees.count_documents({"hasResponded": True})
        rsvp_no = total_invitees - rsvp_yes
        
        accommodation_requests = await db.responses.count_documents({"requiresAccommodation": True})
        
        food_prefs = await db.responses.aggregate([
            {"$group": {"_id": "$foodPreference", "count": {"$sum": 1}}}
        ]).to_list(10)
        
        food_preferences = {pref["_id"]: pref["count"] for pref in food_prefs}
        
        return DashboardStats(
            totalInvitees=total_invitees,
            rsvpYes=rsvp_yes,
            rsvpNo=rsvp_no,
            accommodationRequests=accommodation_requests,
            foodPreferences=food_preferences
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard stats: {str(e)}")

# ================== AGENDA MANAGEMENT ROUTES ==================

@api_router.post("/agenda")
async def upload_agenda(title: str = Form(...), file: UploadFile = File(...)):
    """Upload agenda PDF"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be PDF format")
        
        contents = await file.read()
        pdf_base64 = base64.b64encode(contents).decode('utf-8')
        
        # Remove existing agenda and add new one
        await db.agendas.delete_many({})
        
        agenda = Agenda(
            agendaTitle=title,
            pdfBase64=pdf_base64
        )
        
        await db.agendas.insert_one(agenda.dict())
        
        return {"message": "Agenda uploaded successfully", "agendaId": agenda.agendaId}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading agenda: {str(e)}")

@api_router.get("/agenda")
async def get_current_agenda():
    """Get current agenda"""
    agenda = await db.agendas.find_one()
    if not agenda:
        return {"message": "No agenda available"}
    
    return Agenda(**convert_objectid(agenda))

# ================== ENHANCED GALLERY ROUTES WITH CLOUDINARY ==================

@api_router.post("/gallery/upload-cdn")
async def upload_gallery_photo_cdn(
    employeeId: str = Form(...),
    eventVersion: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload photo to gallery using Cloudinary CDN"""
    try:
        # Check existing photos for this user in PM Connect 3.0
        if eventVersion == "PM Connect 3.0":
            existing_count = await db.gallery_photos.count_documents({
                "employeeId": employeeId,
                "eventVersion": "PM Connect 3.0"
            })
            if existing_count >= 2:
                raise HTTPException(status_code=400, detail="Maximum 2 photos allowed for PM Connect 3.0")
        
        # Upload to Cloudinary
        upload_result = await cloudinary_service.upload_image(
            file,
            folder=f"pm_connect/gallery/{eventVersion.replace(' ', '_').lower()}",
            tags=["gallery", eventVersion.replace(' ', '_').lower(), employeeId]
        )
        
        # Create enhanced photo document
        photo = {
            "photoId": str(uuid.uuid4()),
            "employeeId": employeeId,
            "cloudinary_public_id": upload_result["public_id"],
            "imageUrl": upload_result["url"],
            "imageBase64": "",  # Keep empty for backward compatibility
            "eventVersion": eventVersion,
            "uploadTimestamp": datetime.utcnow(),
            "cdn_metadata": {
                "width": upload_result["width"],
                "height": upload_result["height"],
                "format": upload_result["format"],
                "bytes": upload_result["bytes"]
            }
        }
        
        await db.gallery_photos.insert_one(photo)
        
        return {
            "message": "Photo uploaded successfully to CDN",
            "photoId": photo["photoId"],
            "url": upload_result["url"],
            "metadata": upload_result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading photo: {str(e)}"
        )

@api_router.get("/gallery/cdn/{event_version}")
async def get_gallery_photos_cdn(event_version: str):
    """Get photos by event version from CDN"""
    photos = await db.gallery_photos.find({"eventVersion": event_version}).to_list(1000)
    
    enhanced_photos = []
    for photo in photos:
        # Generate optimized URLs for different sizes
        if photo.get("cloudinary_public_id"):
            optimized_urls = {
                "thumbnail": cloudinary_service.generate_image_url(
                    photo["cloudinary_public_id"], width=300, height=300, crop="fill"
                ),
                "medium": cloudinary_service.generate_image_url(
                    photo["cloudinary_public_id"], width=800, height=600, crop="limit"
                ),
                "full": cloudinary_service.generate_image_url(
                    photo["cloudinary_public_id"]
                )
            }
            photo["optimized_urls"] = optimized_urls
        
        enhanced_photos.append(convert_objectid(photo))
    
    return enhanced_photos

@api_router.delete("/gallery/cdn/{photo_id}")
async def delete_gallery_photo_cdn(photo_id: str):
    """Delete a gallery photo from both database and CDN"""
    
    # Find the photo first
    photo = await db.gallery_photos.find_one({"photoId": photo_id})
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    try:
        # Delete from Cloudinary if it has a public_id
        if photo.get("cloudinary_public_id"):
            cloudinary_service.delete_asset(photo["cloudinary_public_id"], "image")
        
        # Delete from database
        result = await db.gallery_photos.delete_one({"photoId": photo_id})
        
        return {
            "message": "Photo deleted successfully from CDN and database",
            "deleted": result.deleted_count > 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting photo: {str(e)}"
        )

# ================== ENHANCED AGENDA ROUTES WITH CLOUDINARY ==================

@api_router.post("/agenda/cdn")
async def upload_agenda_cdn(title: str = Form(...), file: UploadFile = File(...)):
    """Upload agenda PDF to Cloudinary CDN"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be PDF format")
        
        # Upload PDF to Cloudinary
        upload_result = await cloudinary_service.upload_video(  # PDFs use video resource type
            file,
            folder="pm_connect/agendas",
            enable_hls=False,
            tags=["agenda", "pdf"]
        )
        
        # Remove existing agenda and add new one
        await db.agendas.delete_many({})
        
        agenda = {
            "agendaId": str(uuid.uuid4()),
            "agendaTitle": title,
            "cloudinary_public_id": upload_result["public_id"],
            "pdfUrl": upload_result["url"],
            "pdfBase64": "",  # Keep empty for backward compatibility
            "uploadTimestamp": datetime.utcnow(),
            "cdn_metadata": {
                "format": upload_result["format"],
                "bytes": upload_result["bytes"]
            }
        }
        
        await db.agendas.insert_one(agenda)
        
        return {
            "message": "Agenda uploaded successfully to CDN",
            "agendaId": agenda["agendaId"],
            "url": upload_result["url"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading agenda: {str(e)}"
        )

# ================== VIDEO UPLOAD ROUTES WITH HLS STREAMING ==================

@api_router.post("/video/upload")
async def upload_video_hls(
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...)
):
    """Upload video with HLS streaming support"""
    try:
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be video format")
        
        # Upload video with HLS streaming
        upload_result = await cloudinary_service.upload_video(
            file,
            folder="pm_connect/videos",
            enable_hls=True,
            tags=["teaser", "video", "hls"]
        )
        
        # Store video metadata
        video_doc = {
            "videoId": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "cloudinary_public_id": upload_result["public_id"],
            "videoUrl": upload_result["url"],
            "streaming_urls": upload_result["streaming_urls"],
            "uploadTimestamp": datetime.utcnow(),
            "metadata": {
                "duration": upload_result.get("duration"),
                "width": upload_result["width"],
                "height": upload_result["height"],
                "format": upload_result["format"],
                "bytes": upload_result["bytes"]
            }
        }
        
        await db.videos.insert_one(video_doc)
        
        return {
            "message": "Video uploaded successfully with HLS streaming",
            "videoId": video_doc["videoId"],
            "streaming_urls": upload_result["streaming_urls"],
            "metadata": upload_result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading video: {str(e)}"
        )

@api_router.get("/videos")
async def get_videos():
    """Get all uploaded videos"""
    videos = await db.videos.find().to_list(1000)
    return [convert_objectid(video) for video in videos]

@api_router.get("/videos/featured")
async def get_featured_video():
    """Get the most recent video for dashboard display"""
    video = await db.videos.find_one(sort=[("uploadTimestamp", -1)])
    if not video:
        return {"message": "No videos available"}
    
    return convert_objectid(video)

# ================== IMAGE OPTIMIZATION ROUTES ==================

@api_router.get("/image/optimize/{public_id}")
async def get_optimized_image_url(
    public_id: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    quality: str = "auto:good",
    format: str = "auto",
    crop: str = "fill"
):
    """Generate optimized image URL with transformations"""
    try:
        optimized_url = cloudinary_service.generate_image_url(
            public_id, width, height, crop, quality, format
        )
        
        return {
            "public_id": public_id,
            "optimized_url": optimized_url,
            "transformations": {
                "width": width,
                "height": height,
                "quality": quality,
                "format": format,
                "crop": crop
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating optimized URL: {str(e)}"
        )

# ================== SPRINT 2: ENHANCED DATA MANAGEMENT ROUTES ==================

# Enhanced CSV Import with Validation
@api_router.post("/invitees/bulk-upload-enhanced")
async def bulk_upload_invitees_enhanced(file: UploadFile = File(...)):
    """Enhanced CSV upload with comprehensive validation"""
    try:
        if not file.filename.endswith(('.csv', '.xlsx')):
            raise HTTPException(status_code=400, detail="File must be CSV or Excel format")
        
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Validate using enhanced validation service
        validation_result = data_validation_service.validate_invitee_csv(df)
        
        if not validation_result.is_valid:
            return {
                "success": False,
                "validation_result": validation_result.dict(),
                "message": f"Validation failed with {len(validation_result.errors)} errors"
            }
        
        # If validation passed, insert the processed data
        if validation_result.processed_data:
            # Clear existing invitees and insert new ones
            await db.invitees.delete_many({})
            
            # Convert processed data to proper format
            invitees = []
            for data in validation_result.processed_data:
                invitee = {
                    "employeeId": data["employeeId"],
                    "employeeName": data["employeeName"],
                    "cadre": data["cadre"],
                    "projectName": data["projectName"],
                    "email": data.get("email", ""),
                    "department": data.get("department", ""),
                    "phone": data.get("phone", ""),
                    "hasResponded": False,
                    "importedAt": datetime.utcnow()
                }
                invitees.append(invitee)
            
            result = await db.invitees.insert_many(invitees)
            
            return {
                "success": True,
                "validation_result": validation_result.dict(),
                "message": f"Successfully uploaded {len(invitees)} invitees",
                "inserted_count": len(result.inserted_ids),
                "warnings": len(validation_result.warnings)
            }
        else:
            raise HTTPException(status_code=400, detail="No valid data to import")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@api_router.post("/cab-allocations/upload-enhanced")
async def upload_cab_allocations_enhanced(file: UploadFile = File(...)):
    """Enhanced cab allocation upload with validation"""
    try:
        if not file.filename.endswith(('.csv', '.xlsx')):
            raise HTTPException(status_code=400, detail="File must be CSV or Excel format")
        
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Validate using enhanced validation service
        validation_result = data_validation_service.validate_cab_csv(df)
        
        if not validation_result.is_valid:
            return {
                "success": False,
                "validation_result": validation_result.dict(),
                "message": f"Validation failed with {len(validation_result.errors)} errors"
            }
        
        # If validation passed, process and insert data
        if validation_result.processed_data:
            # Clear existing allocations
            await db.cab_allocations.delete_many({})
            
            # Group by cab number
            cab_groups = {}
            for data in validation_result.processed_data:
                cab_num = data["cabNumber"]
                if cab_num not in cab_groups:
                    cab_groups[cab_num] = {
                        "cabId": str(uuid.uuid4()),
                        "cabNumber": cab_num,
                        "assignedMembers": [],
                        "pickupLocation": data["pickupLocation"],
                        "pickupTime": data["pickupTime"],
                        "memberDetails": []
                    }
                
                cab_groups[cab_num]["assignedMembers"].append(data["employeeId"])
                cab_groups[cab_num]["memberDetails"].append({
                    "employeeId": data["employeeId"],
                    "employeeName": data.get("employeeName", ""),
                    "contactNumber": data.get("contactNumber", "")
                })
            
            allocations = list(cab_groups.values())
            result = await db.cab_allocations.insert_many(allocations)
            
            return {
                "success": True,
                "validation_result": validation_result.dict(),
                "message": f"Successfully uploaded {len(allocations)} cab allocations",
                "inserted_count": len(result.inserted_ids),
                "warnings": len(validation_result.warnings)
            }
        else:
            raise HTTPException(status_code=400, detail="No valid data to import")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Advanced Excel Export Routes
@api_router.post("/exports/responses/advanced")
async def create_advanced_responses_export(background_tasks: BackgroundTasks, filters: Dict[str, Any] = None):
    """Create advanced responses export with background processing"""
    try:
        result = await excel_export_service.export_responses_advanced()
        return {
            "message": "Advanced responses export created successfully",
            "export_id": result["export_id"],
            "download_info": {
                "filename": result["filename"],
                "excel_data": result["excel_data"]
            },
            "summary": result["summary"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@api_router.post("/exports/invitees/status")
async def create_invitees_status_export():
    """Create invitees with status export"""
    try:
        result = await excel_export_service.export_invitees_with_status()
        return {
            "message": "Invitees status export created successfully",
            "export_id": result["export_id"],
            "download_info": {
                "filename": result["filename"],
                "excel_data": result["excel_data"]
            },
            "summary": result["summary"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@api_router.post("/exports/cab-allocations")
async def create_cab_allocations_export():
    """Create cab allocations export"""
    try:
        result = await excel_export_service.export_cab_allocations()
        return {
            "message": "Cab allocations export created successfully",
            "export_id": result["export_id"],
            "download_info": {
                "filename": result["filename"],
                "excel_data": result["excel_data"]
            },
            "summary": result["summary"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@api_router.get("/exports/progress/{export_id}")
async def get_export_progress(export_id: str):
    """Get export progress status"""
    progress = excel_export_service.get_export_progress(export_id)
    if progress.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Export task not found")
    return progress

# Data Integrity Routes
@api_router.get("/data/integrity-check")
async def check_data_integrity():
    """Perform comprehensive data integrity check"""
    try:
        integrity_report = await data_validation_service.check_data_integrity()
        return {
            "message": "Data integrity check completed",
            "report": integrity_report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integrity check failed: {str(e)}")

@api_router.post("/data/fix-integrity")
async def fix_data_integrity():
    """Automatically fix common data integrity issues"""
    try:
        fix_report = await data_validation_service.fix_data_integrity_issues()
        return {
            "message": "Data integrity fixes applied",
            "report": fix_report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fix failed: {str(e)}")

@api_router.post("/data/refresh-totals")
async def refresh_dashboard_totals():
    """Refresh and recompute dashboard totals for data consistency"""
    try:
        # Recompute all dashboard statistics
        total_invitees = await db.invitees.count_documents({})
        total_responses = await db.responses.count_documents({})
        
        # Fix response flags
        responses = await db.responses.find({}, {"employeeId": 1}).to_list(10000)
        response_employee_ids = {r["employeeId"] for r in responses}
        
        # Update hasResponded flag correctly
        await db.invitees.update_many(
            {"employeeId": {"$in": list(response_employee_ids)}},
            {"$set": {"hasResponded": True}}
        )
        
        await db.invitees.update_many(
            {"employeeId": {"$nin": list(response_employee_ids)}},
            {"$set": {"hasResponded": False}}
        )
        
        # Recompute stats
        rsvp_yes = await db.invitees.count_documents({"hasResponded": True})
        rsvp_no = total_invitees - rsvp_yes
        accommodation_requests = await db.responses.count_documents({"requiresAccommodation": True})
        
        food_prefs = await db.responses.aggregate([
            {"$group": {"_id": "$foodPreference", "count": {"$sum": 1}}}
        ]).to_list(10)
        
        food_preferences = {pref["_id"]: pref["count"] for pref in food_prefs}
        
        return {
            "message": "Dashboard totals refreshed successfully",
            "updated_stats": {
                "totalInvitees": total_invitees,
                "totalResponses": total_responses,
                "rsvpYes": rsvp_yes, 
                "rsvpNo": rsvp_no,
                "accommodationRequests": accommodation_requests,
                "foodPreferences": food_preferences
            },
            "fixes_applied": {
                "response_flags_updated": True,
                "totals_recomputed": True
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")

# ================== END SPRINT 2 ROUTES ==================

# ================== CAB ALLOCATION ROUTES ==================

@api_router.post("/cab-allocations/upload")
async def upload_cab_allocations(file: UploadFile = File(...)):
    """Upload cab allocation CSV"""
    try:
        if not file.filename.endswith(('.csv', '.xlsx')):
            raise HTTPException(status_code=400, detail="File must be CSV or Excel format")
        
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Validate required columns
        required_columns = ['Cab Number', 'Employee ID', 'Pickup Location', 'Time']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"CSV must contain columns: {required_columns}")
        
        # Clear existing allocations
        await db.cab_allocations.delete_many({})
        
        # Group by cab number
        cab_groups = df.groupby('Cab Number')
        allocations = []
        
        for cab_num, group in cab_groups:
            allocation = CabAllocation(
                cabNumber=int(cab_num),
                assignedMembers=group['Employee ID'].astype(str).tolist(),
                pickupLocation=str(group.iloc[0]['Pickup Location']),
                pickupTime=str(group.iloc[0]['Time'])
            )
            allocations.append(allocation.dict())
        
        result = await db.cab_allocations.insert_many(allocations)
        
        return {"message": f"Successfully uploaded {len(allocations)} cab allocations", "inserted_count": len(result.inserted_ids)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading cab allocations: {str(e)}")

@api_router.get("/cab-allocations/{employee_id}")
async def get_cab_allocation(employee_id: str):
    """Get cab allocation for specific employee"""
    allocation = await db.cab_allocations.find_one({"assignedMembers": employee_id})
    if not allocation:
        return {"message": "No cab allocation found"}
    
    return CabAllocation(**convert_objectid(allocation))

@api_router.get("/cab-allocations")
async def get_all_cab_allocations():
    """Get all cab allocations"""
    allocations = await db.cab_allocations.find().to_list(1000)
    return [CabAllocation(**convert_objectid(allocation)) for allocation in allocations]

@api_router.post("/cab-allocations/upload")
async def upload_cab_allocations(file: UploadFile = File(...)):
    """Upload cab allocation CSV"""
    try:
        if not file.filename.endswith(('.csv', '.xlsx')):
            raise HTTPException(status_code=400, detail="File must be CSV or Excel format")
        
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Validate required columns
        required_columns = ['Cab Number', 'Employee ID', 'Pickup Location', 'Time']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"CSV must contain columns: {required_columns}")
        
        # Clear existing allocations
        await db.cab_allocations.delete_many({})
        
        # Group by cab number
        cab_groups = df.groupby('Cab Number')
        allocations = []
        
        for cab_num, group in cab_groups:
            allocation = CabAllocation(
                cabNumber=int(cab_num),
                assignedMembers=group['Employee ID'].astype(str).tolist(),
                pickupLocation=str(group.iloc[0]['Pickup Location']),
                pickupTime=str(group.iloc[0]['Time'])
            )
            allocations.append(allocation.dict())
        
        result = await db.cab_allocations.insert_many(allocations)
        
        return {"message": f"Successfully uploaded {len(allocations)} cab allocations", "inserted_count": len(result.inserted_ids)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading cab allocations: {str(e)}")

@api_router.get("/cab-allocations/{employee_id}")
async def get_cab_allocation(employee_id: str):
    """Get cab allocation for specific employee"""
    allocation = await db.cab_allocations.find_one({"assignedMembers": employee_id})
    if not allocation:
        return {"message": "No cab allocation found"}
    
    return CabAllocation(**convert_objectid(allocation))

@api_router.get("/cab-allocations")
async def get_all_cab_allocations():
    """Get all cab allocations"""
    allocations = await db.cab_allocations.find().to_list(1000)
    return [CabAllocation(**convert_objectid(allocation)) for allocation in allocations]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()