from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import hashlib
import secrets
import jwt
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class AuthService:
    """Authentication service for PM Connect 3.0"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.secret_key = os.getenv("JWT_SECRET_KEY", "pm-connect-secret-key-2025")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24  # 24 hours
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(plain_password) == hashed_password
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT access token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def create_user_from_invitee(self, employee_code: str) -> Optional[Dict[str, Any]]:
        """Create user account from invitee data"""
        # Find invitee by employee code
        invitee = await self.db.invitees.find_one({"employeeId": employee_code})
        if not invitee:
            return None
        
        # Check if user already exists
        existing_user = await self.db.users.find_one({"employeeId": employee_code})
        if existing_user:
            return existing_user
        
        # Create new user with default password = employee code
        default_password = self.hash_password(employee_code)
        
        user_data = {
            "employeeId": employee_code,
            "employeeName": invitee["employeeName"],
            "cadre": invitee["cadre"],
            "projectName": invitee["projectName"],
            "password": default_password,
            "role": "invitee",
            "isFirstLogin": True,
            "mustChangePassword": True,
            "officeType": None,  # Will be set on first login
            "createdAt": datetime.utcnow(),
            "lastLogin": None,
            "isActive": True
        }
        
        await self.db.users.insert_one(user_data)
        return user_data
    
    async def authenticate_user(self, employee_code: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with employee code and password"""
        # Try to find existing user
        user = await self.db.users.find_one({"employeeId": employee_code})
        
        # If user doesn't exist, create from invitee data
        if not user:
            user = await self.create_user_from_invitee(employee_code)
            if not user:
                return None
        
        # Check if account is active
        if not user.get("isActive", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
        
        # Verify password
        if not self.verify_password(password, user["password"]):
            return None
        
        # Update last login
        await self.db.users.update_one(
            {"employeeId": employee_code},
            {"$set": {"lastLogin": datetime.utcnow()}}
        )
        
        return user
    
    async def change_password(self, employee_code: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = await self.db.users.find_one({"employeeId": employee_code})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify old password
        if not self.verify_password(old_password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        new_hashed_password = self.hash_password(new_password)
        await self.db.users.update_one(
            {"employeeId": employee_code},
            {
                "$set": {
                    "password": new_hashed_password,
                    "mustChangePassword": False,
                    "isFirstLogin": False,
                    "passwordChangedAt": datetime.utcnow()
                }
            }
        )
        
        return True
    
    async def set_office_type(self, employee_code: str, office_type: str) -> bool:
        """Set user's office type during first login"""
        if office_type not in ["Head Office", "Site Office"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid office type. Must be 'Head Office' or 'Site Office'"
            )
        
        result = await self.db.users.update_one(
            {"employeeId": employee_code},
            {"$set": {"officeType": office_type}}
        )
        
        return result.modified_count > 0
    
    async def get_user_permissions(self, employee_id: str) -> List[str]:
        """Get user permissions based on role"""
        user = await self.db.users.find_one({"employeeId": employee_id})
        if not user:
            return []
        
        if user["role"] == "admin":
            return user.get("permissions", [
                "manage_invitees",
                "manage_responses", 
                "manage_agenda",
                "manage_gallery",
                "manage_cab_allocations",
                "export_data",
                "view_analytics"
            ])
        else:
            # Default invitee permissions
            return [
                "view_own_profile",
                "submit_rsvp", 
                "view_agenda",
                "upload_gallery",
                "view_cab_details"
            ]
    
    async def log_user_activity(
        self, 
        employee_id: str, 
        action: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        """Log user activity for audit trail"""
        log_entry = {
            "employeeId": employee_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.utcnow(),
            "ip_address": None,  # Will be set by middleware
            "user_agent": None   # Will be set by middleware
        }
        
        await self.db.audit_logs.insert_one(log_entry)