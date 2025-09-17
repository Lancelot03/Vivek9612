from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Depends, Form, status
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'pm_connect_db')]

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

@api_router.get("/auth/status")
async def auth_status():
    """Check authentication status"""
    return {"authenticated": False, "message": "Emergent OAuth not yet implemented"}

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

# ================== GALLERY ROUTES ==================

@api_router.post("/gallery/upload")
async def upload_gallery_photo(
    employeeId: str = Form(...),
    eventVersion: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload photo to gallery"""
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check existing photos for this user in PM Connect 3.0
        if eventVersion == "PM Connect 3.0":
            existing_count = await db.gallery_photos.count_documents({
                "employeeId": employeeId,
                "eventVersion": "PM Connect 3.0"
            })
            if existing_count >= 2:
                raise HTTPException(status_code=400, detail="Maximum 2 photos allowed for PM Connect 3.0")
        
        contents = await file.read()
        image_base64 = base64.b64encode(contents).decode('utf-8')
        
        photo = GalleryPhoto(
            employeeId=employeeId,
            imageBase64=image_base64,
            eventVersion=eventVersion
        )
        
        await db.gallery_photos.insert_one(photo.dict())
        
        return {"message": "Photo uploaded successfully", "photoId": photo.photoId}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading photo: {str(e)}")

@api_router.get("/gallery/{event_version}")
async def get_gallery_photos(event_version: str):
    """Get photos by event version"""
    photos = await db.gallery_photos.find({"eventVersion": event_version}).to_list(1000)
    return [GalleryPhoto(**convert_objectid(photo)) for photo in photos]

@api_router.delete("/gallery/{photo_id}")
async def delete_gallery_photo(photo_id: str):
    """Delete a gallery photo"""
    result = await db.gallery_photos.delete_one({"photoId": photo_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    return {"message": "Photo deleted successfully"}

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