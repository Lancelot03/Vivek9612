import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import re
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, ValidationError
from fastapi import HTTPException

class ValidationError(BaseModel):
    row: int
    column: str
    value: Any
    error: str
    severity: str  # 'error', 'warning', 'info'

class ValidationResult(BaseModel):
    is_valid: bool
    total_rows: int
    valid_rows: int
    errors: List[ValidationError]
    warnings: List[ValidationError]
    processed_data: Optional[List[Dict[str, Any]]] = None

class DataValidationService:
    """Enhanced data validation service for PM Connect 3.0"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    # ============ INVITEE CSV VALIDATION ============
    
    def validate_invitee_csv(self, df: pd.DataFrame) -> ValidationResult:
        """Validate invitee CSV with comprehensive error checking"""
        
        required_columns = ['Employee ID', 'Employee Name', 'Cadre', 'Project Name']
        optional_columns = ['Email', 'Department', 'Phone']
        errors = []
        warnings = []
        valid_data = []
        
        # Check required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            for col in missing_columns:
                errors.append(ValidationError(
                    row=0,
                    column=col,
                    value="",
                    error=f"Required column '{col}' is missing",
                    severity="error"
                ))
            return ValidationResult(
                is_valid=False,
                total_rows=len(df),
                valid_rows=0,
                errors=errors,
                warnings=warnings
            )
        
        # Validate each row
        for index, row in df.iterrows():
            row_errors = []
            row_warnings = []
            
            # Validate Employee ID
            emp_id = str(row['Employee ID']).strip() if pd.notna(row['Employee ID']) else ""
            if not emp_id:
                row_errors.append(ValidationError(
                    row=index + 1,
                    column='Employee ID',
                    value=emp_id,
                    error="Employee ID cannot be empty",
                    severity="error"
                ))
            elif len(emp_id) < 3:
                row_errors.append(ValidationError(
                    row=index + 1,
                    column='Employee ID',
                    value=emp_id,
                    error="Employee ID must be at least 3 characters",
                    severity="error"
                ))
            elif not re.match(r'^[A-Za-z0-9_-]+$', emp_id):
                row_warnings.append(ValidationError(
                    row=index + 1,
                    column='Employee ID',
                    value=emp_id,
                    error="Employee ID contains special characters",
                    severity="warning"
                ))
            
            # Validate Employee Name
            emp_name = str(row['Employee Name']).strip() if pd.notna(row['Employee Name']) else ""
            if not emp_name:
                row_errors.append(ValidationError(
                    row=index + 1,
                    column='Employee Name',
                    value=emp_name,
                    error="Employee Name cannot be empty",
                    severity="error"
                ))
            elif len(emp_name) < 2:
                row_errors.append(ValidationError(
                    row=index + 1,
                    column='Employee Name',
                    value=emp_name,
                    error="Employee Name must be at least 2 characters",
                    severity="error"
                ))
            elif not re.match(r'^[A-Za-z\s.,-]+$', emp_name):
                row_warnings.append(ValidationError(
                    row=index + 1,
                    column='Employee Name',
                    value=emp_name,
                    error="Employee Name contains unusual characters",
                    severity="warning"
                ))
            
            # Validate Cadre
            cadre = str(row['Cadre']).strip() if pd.notna(row['Cadre']) else ""
            if not cadre:
                row_warnings.append(ValidationError(
                    row=index + 1,
                    column='Cadre',
                    value=cadre,
                    error="Cadre is empty - will use 'Not Specified'",
                    severity="warning"
                ))
                cadre = "Not Specified"
            
            # Validate Project Name
            project = str(row['Project Name']).strip() if pd.notna(row['Project Name']) else ""
            if not project:
                row_warnings.append(ValidationError(
                    row=index + 1,
                    column='Project Name',
                    value=project,
                    error="Project Name is empty - will use 'Not Specified'",
                    severity="warning"
                ))
                project = "Not Specified"
            
            # Validate Email if present
            if 'Email' in df.columns and pd.notna(row['Email']):
                email = str(row['Email']).strip()
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if email and not re.match(email_pattern, email):
                    row_warnings.append(ValidationError(
                        row=index + 1,
                        column='Email',
                        value=email,
                        error="Invalid email format",
                        severity="warning"
                    ))
            
            # Add to errors/warnings lists
            errors.extend(row_errors)
            warnings.extend(row_warnings)
            
            # If no errors, add to valid data
            if not row_errors:
                valid_data.append({
                    "employeeId": emp_id,
                    "employeeName": emp_name,
                    "cadre": cadre,
                    "projectName": project,
                    "email": str(row.get('Email', '')).strip() if pd.notna(row.get('Email')) else "",
                    "department": str(row.get('Department', '')).strip() if pd.notna(row.get('Department')) else "",
                    "phone": str(row.get('Phone', '')).strip() if pd.notna(row.get('Phone')) else ""
                })
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            total_rows=len(df),
            valid_rows=len(valid_data),
            errors=errors,
            warnings=warnings,
            processed_data=valid_data if len(errors) == 0 else None
        )
    
    # ============ CAB ALLOCATION CSV VALIDATION ============
    
    def validate_cab_csv(self, df: pd.DataFrame) -> ValidationResult:
        """Validate cab allocation CSV with comprehensive error checking"""
        
        required_columns = ['Cab Number', 'Employee ID', 'Pickup Location', 'Time']
        optional_columns = ['Employee Name', 'Contact Number']
        errors = []
        warnings = []
        valid_data = []
        
        # Check required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            for col in missing_columns:
                errors.append(ValidationError(
                    row=0,
                    column=col,
                    value="",
                    error=f"Required column '{col}' is missing",
                    severity="error"
                ))
            return ValidationResult(
                is_valid=False,
                total_rows=len(df),
                valid_rows=0,
                errors=errors,
                warnings=warnings
            )
        
        # Track cab numbers and employee assignments
        cab_assignments = {}
        employee_assignments = {}
        
        # Validate each row
        for index, row in df.iterrows():
            row_errors = []
            row_warnings = []
            
            # Validate Cab Number
            try:
                cab_num = int(float(row['Cab Number']))
                if cab_num <= 0:
                    row_errors.append(ValidationError(
                        row=index + 1,
                        column='Cab Number',
                        value=cab_num,
                        error="Cab Number must be positive",
                        severity="error"
                    ))
            except (ValueError, TypeError):
                row_errors.append(ValidationError(
                    row=index + 1,
                    column='Cab Number',
                    value=row['Cab Number'],
                    error="Cab Number must be a valid integer",
                    severity="error"
                ))
                cab_num = None
            
            # Validate Employee ID
            emp_id = str(row['Employee ID']).strip() if pd.notna(row['Employee ID']) else ""
            if not emp_id:
                row_errors.append(ValidationError(
                    row=index + 1,
                    column='Employee ID',
                    value=emp_id,
                    error="Employee ID cannot be empty",
                    severity="error"
                ))
            elif emp_id in employee_assignments:
                row_warnings.append(ValidationError(
                    row=index + 1,
                    column='Employee ID',
                    value=emp_id,
                    error=f"Employee {emp_id} is already assigned to Cab {employee_assignments[emp_id]}",
                    severity="warning"
                ))
            
            # Validate Pickup Location
            pickup = str(row['Pickup Location']).strip() if pd.notna(row['Pickup Location']) else ""
            if not pickup:
                row_errors.append(ValidationError(
                    row=index + 1,
                    column='Pickup Location',
                    value=pickup,
                    error="Pickup Location cannot be empty",
                    severity="error"
                ))
            
            # Validate Time
            pickup_time = str(row['Time']).strip() if pd.notna(row['Time']) else ""
            if not pickup_time:
                row_errors.append(ValidationError(
                    row=index + 1,
                    column='Time',
                    value=pickup_time,
                    error="Pickup Time cannot be empty",
                    severity="error"
                ))
            else:
                # Try to parse time format
                time_formats = ['%H:%M', '%I:%M %p', '%H:%M:%S', '%I:%M:%S %p']
                valid_time = False
                for fmt in time_formats:
                    try:
                        datetime.strptime(pickup_time, fmt)
                        valid_time = True
                        break
                    except ValueError:
                        continue
                
                if not valid_time:
                    row_warnings.append(ValidationError(
                        row=index + 1,
                        column='Time',
                        value=pickup_time,
                        error="Time format may not be standard (HH:MM recommended)",
                        severity="warning"
                    ))
            
            # Track assignments for duplicate checking
            if cab_num and emp_id:
                if cab_num not in cab_assignments:
                    cab_assignments[cab_num] = []
                cab_assignments[cab_num].append(emp_id)
                employee_assignments[emp_id] = cab_num
            
            # Add to errors/warnings lists
            errors.extend(row_errors)
            warnings.extend(row_warnings)
            
            # If no errors, add to valid data
            if not row_errors:
                valid_data.append({
                    "cabNumber": cab_num,
                    "employeeId": emp_id,
                    "pickupLocation": pickup,
                    "pickupTime": pickup_time,
                    "employeeName": str(row.get('Employee Name', '')).strip() if pd.notna(row.get('Employee Name')) else "",
                    "contactNumber": str(row.get('Contact Number', '')).strip() if pd.notna(row.get('Contact Number')) else ""
                })
        
        # Check for cab capacity warnings
        for cab_num, employees in cab_assignments.items():
            if len(employees) > 8:  # Assuming max 8 per cab
                warnings.append(ValidationError(
                    row=0,
                    column='Cab Number',
                    value=cab_num,
                    error=f"Cab {cab_num} has {len(employees)} employees (consider splitting)",
                    severity="warning"
                ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            total_rows=len(df),
            valid_rows=len(valid_data),
            errors=errors,
            warnings=warnings,
            processed_data=valid_data if len(errors) == 0 else None
        )
    
    # ============ DATA INTEGRITY CHECKS ============
    
    async def check_data_integrity(self) -> Dict[str, Any]:
        """Comprehensive data integrity checks"""
        
        integrity_report = {
            "timestamp": datetime.utcnow(),
            "overall_status": "healthy",
            "checks": [],
            "issues": [],
            "statistics": {}
        }
        
        # Check 1: Invitee-Response consistency
        total_invitees = await self.db.invitees.count_documents({})
        total_responses = await self.db.responses.count_documents({})
        responded_invitees = await self.db.invitees.count_documents({"hasResponded": True})
        
        integrity_report["statistics"]["total_invitees"] = total_invitees
        integrity_report["statistics"]["total_responses"] = total_responses
        integrity_report["statistics"]["responded_invitees"] = responded_invitees
        
        if total_responses != responded_invitees:
            integrity_report["issues"].append({
                "type": "data_mismatch",
                "severity": "error",
                "message": f"Response count ({total_responses}) doesn't match responded invitees ({responded_invitees})",
                "suggested_fix": "Run data synchronization to fix response flags"
            })
            integrity_report["overall_status"] = "warning"
        
        integrity_report["checks"].append({
            "name": "Invitee-Response Consistency",
            "status": "passed" if total_responses == responded_invitees else "failed",
            "details": f"{total_responses} responses for {responded_invitees} responded invitees"
        })
        
        # Check 2: Food preference totals
        food_prefs = await self.db.responses.aggregate([
            {"$group": {"_id": "$foodPreference", "count": {"$sum": 1}}}
        ]).to_list(10)
        
        food_total = sum(pref["count"] for pref in food_prefs)
        
        integrity_report["statistics"]["food_preferences"] = {pref["_id"]: pref["count"] for pref in food_prefs}
        integrity_report["statistics"]["food_preference_total"] = food_total
        
        if food_total != total_responses:
            integrity_report["issues"].append({
                "type": "data_mismatch", 
                "severity": "error",
                "message": f"Food preference total ({food_total}) doesn't match response total ({total_responses})",
                "suggested_fix": "Check for responses with missing food preferences"
            })
            integrity_report["overall_status"] = "warning"
        
        integrity_report["checks"].append({
            "name": "Food Preference Totals",
            "status": "passed" if food_total == total_responses else "failed",
            "details": f"{food_total} food preferences for {total_responses} responses"
        })
        
        # Check 3: Cab allocation consistency
        cab_allocations = await self.db.cab_allocations.find().to_list(1000)
        total_cab_members = sum(len(cab["assignedMembers"]) for cab in cab_allocations)
        
        integrity_report["statistics"]["total_cab_allocations"] = len(cab_allocations)
        integrity_report["statistics"]["total_cab_members"] = total_cab_members
        
        # Check for duplicate employee assignments in cabs
        all_assigned_employees = []
        for cab in cab_allocations:
            all_assigned_employees.extend(cab["assignedMembers"])
        
        duplicate_assignments = []
        seen = set()
        for emp_id in all_assigned_employees:
            if emp_id in seen:
                duplicate_assignments.append(emp_id)
            seen.add(emp_id)
        
        if duplicate_assignments:
            integrity_report["issues"].append({
                "type": "duplicate_assignment",
                "severity": "error", 
                "message": f"Employees assigned to multiple cabs: {', '.join(duplicate_assignments)}",
                "suggested_fix": "Remove duplicate cab assignments"
            })
            integrity_report["overall_status"] = "error"
        
        integrity_report["checks"].append({
            "name": "Cab Assignment Duplicates",
            "status": "passed" if not duplicate_assignments else "failed",
            "details": f"{len(duplicate_assignments)} duplicate assignments found"
        })
        
        # Check 4: Orphaned data
        response_employee_ids = {doc["employeeId"] async for doc in self.db.responses.find({}, {"employeeId": 1})}
        invitee_employee_ids = {doc["employeeId"] async for doc in self.db.invitees.find({}, {"employeeId": 1})}
        
        orphaned_responses = response_employee_ids - invitee_employee_ids
        if orphaned_responses:
            integrity_report["issues"].append({
                "type": "orphaned_data",
                "severity": "warning",
                "message": f"Responses exist for non-invitees: {', '.join(list(orphaned_responses)[:5])}{'...' if len(orphaned_responses) > 5 else ''}",
                "suggested_fix": "Add missing invitees or remove orphaned responses"
            })
            if integrity_report["overall_status"] == "healthy":
                integrity_report["overall_status"] = "warning"
        
        integrity_report["checks"].append({
            "name": "Orphaned Data Check",
            "status": "passed" if not orphaned_responses else "warning",
            "details": f"{len(orphaned_responses)} orphaned responses found"
        })
        
        return integrity_report
    
    async def fix_data_integrity_issues(self) -> Dict[str, Any]:
        """Automatically fix common data integrity issues"""
        
        fix_report = {
            "timestamp": datetime.utcnow(),
            "fixes_applied": [],
            "issues_remaining": [],
            "success": True
        }
        
        try:
            # Fix 1: Sync response flags with actual responses
            responses = await self.db.responses.find({}, {"employeeId": 1}).to_list(10000)
            response_employee_ids = {r["employeeId"] for r in responses}
            
            # Update hasResponded flag for employees with responses
            result1 = await self.db.invitees.update_many(
                {"employeeId": {"$in": list(response_employee_ids)}},
                {"$set": {"hasResponded": True}}
            )
            
            # Update hasResponded flag for employees without responses  
            result2 = await self.db.invitees.update_many(
                {"employeeId": {"$nin": list(response_employee_ids)}},
                {"$set": {"hasResponded": False}}
            )
            
            fix_report["fixes_applied"].append({
                "type": "response_flag_sync",
                "description": f"Updated {result1.modified_count + result2.modified_count} invitee response flags"
            })
            
            # Fix 2: Remove duplicate cab assignments (keep first occurrence)
            cab_allocations = await self.db.cab_allocations.find().to_list(1000)
            seen_employees = set()
            fixed_cabs = []
            
            for cab in cab_allocations:
                original_members = cab["assignedMembers"]
                unique_members = []
                for emp_id in original_members:
                    if emp_id not in seen_employees:
                        unique_members.append(emp_id)
                        seen_employees.add(emp_id)
                
                if len(unique_members) != len(original_members):
                    # Update cab with unique members
                    await self.db.cab_allocations.update_one(
                        {"cabId": cab["cabId"]},
                        {"$set": {"assignedMembers": unique_members}}
                    )
                    fixed_cabs.append(cab["cabNumber"])
            
            if fixed_cabs:
                fix_report["fixes_applied"].append({
                    "type": "duplicate_cab_assignments",
                    "description": f"Removed duplicate assignments from cabs: {', '.join(map(str, fixed_cabs))}"
                })
            
        except Exception as e:
            fix_report["success"] = False
            fix_report["error"] = str(e)
        
        return fix_report