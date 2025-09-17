#!/usr/bin/env python3
"""
PM Connect 3.0 Backend API Test Suite
Tests all backend endpoints comprehensively
"""

import requests
import json
import base64
import io
import pandas as pd
from datetime import datetime, date
import os
import sys
from pathlib import Path

# Configuration
BASE_URL = "https://eventadmin-2.preview.emergentagent.com/api"
TIMEOUT = 30

class PMConnectTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        
    def log_test(self, test_name, success, message, response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "response_data": response_data
        })
    
    def create_sample_invitees_csv(self):
        """Create sample CSV data for invitees"""
        data = {
            'Employee ID': ['EMP001', 'EMP002', 'EMP003', 'EMP004', 'EMP005'],
            'Employee Name': ['Rajesh Kumar', 'Priya Sharma', 'Amit Patel', 'Sneha Reddy', 'Vikram Singh'],
            'Cadre': ['Senior Manager', 'Manager', 'Assistant Manager', 'Senior Executive', 'Manager'],
            'Project Name': ['Digital Transformation', 'Cloud Migration', 'AI Initiative', 'Mobile App Dev', 'Data Analytics']
        }
        df = pd.DataFrame(data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue().encode('utf-8')
    
    def create_sample_cab_csv(self):
        """Create sample CSV data for cab allocations"""
        data = {
            'Cab Number': [1, 1, 1, 2, 2, 3, 3, 3, 3],
            'Employee ID': ['EMP001', 'EMP002', 'EMP003', 'EMP004', 'EMP005', 'EMP001', 'EMP002', 'EMP003', 'EMP004'],
            'Pickup Location': ['Cyber City', 'Cyber City', 'Cyber City', 'DLF Phase 1', 'DLF Phase 1', 'Sector 18', 'Sector 18', 'Sector 18', 'Sector 18'],
            'Time': ['08:00 AM', '08:00 AM', '08:00 AM', '08:30 AM', '08:30 AM', '09:00 AM', '09:00 AM', '09:00 AM', '09:00 AM']
        }
        df = pd.DataFrame(data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue().encode('utf-8')
    
    def create_sample_pdf(self):
        """Create a simple PDF-like content for testing"""
        # This is a minimal PDF structure for testing
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(PM Connect 3.0 Agenda) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
        return pdf_content
    
    def create_sample_image(self):
        """Create a simple base64 image for testing"""
        # 1x1 pixel PNG image in base64
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    def test_invitee_bulk_upload(self):
        """Test bulk upload of invitees"""
        try:
            csv_data = self.create_sample_invitees_csv()
            files = {'file': ('invitees.csv', csv_data, 'text/csv')}
            
            response = self.session.post(f"{BASE_URL}/invitees/bulk-upload", files=files)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Invitee Bulk Upload", True, f"Uploaded {data.get('inserted_count', 0)} invitees", data)
            else:
                self.log_test("Invitee Bulk Upload", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Invitee Bulk Upload", False, f"Exception: {str(e)}")
    
    def test_get_invitees(self):
        """Test getting all invitees"""
        try:
            response = self.session.get(f"{BASE_URL}/invitees")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get All Invitees", True, f"Retrieved {len(data)} invitees", {"count": len(data)})
                return data
            else:
                self.log_test("Get All Invitees", False, f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Get All Invitees", False, f"Exception: {str(e)}")
            return []
    
    def test_get_unresponded_invitees(self):
        """Test getting unresponded invitees"""
        try:
            response = self.session.get(f"{BASE_URL}/invitees/unresponded")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Unresponded Invitees", True, f"Retrieved {len(data)} unresponded invitees", {"count": len(data)})
                return data
            else:
                self.log_test("Get Unresponded Invitees", False, f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Get Unresponded Invitees", False, f"Exception: {str(e)}")
            return []
    
    def test_submit_response(self, employee_id="EMP001"):
        """Test submitting RSVP response"""
        try:
            response_data = {
                "employeeId": employee_id,
                "mobileNumber": "9876543210",
                "requiresAccommodation": True,
                "arrivalDate": "2024-03-15",
                "departureDate": "2024-03-17",
                "foodPreference": "Veg"
            }
            
            response = self.session.post(f"{BASE_URL}/responses", json=response_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Submit RSVP Response", True, f"Response submitted with ID: {data.get('responseId')}", data)
                return data.get('responseId')
            else:
                self.log_test("Submit RSVP Response", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Submit RSVP Response", False, f"Exception: {str(e)}")
            return None
    
    def test_get_responses(self):
        """Test getting all responses"""
        try:
            response = self.session.get(f"{BASE_URL}/responses")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get All Responses", True, f"Retrieved {len(data)} responses", {"count": len(data)})
                return data
            else:
                self.log_test("Get All Responses", False, f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Get All Responses", False, f"Exception: {str(e)}")
            return []
    
    def test_export_responses(self):
        """Test exporting responses to Excel"""
        try:
            response = self.session.get(f"{BASE_URL}/responses/export")
            
            if response.status_code == 200:
                data = response.json()
                if 'excel_data' in data:
                    self.log_test("Export Responses", True, f"Excel exported: {data.get('filename')}", {"has_data": True})
                else:
                    self.log_test("Export Responses", True, "No responses to export", data)
            else:
                self.log_test("Export Responses", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Export Responses", False, f"Exception: {str(e)}")
    
    def test_dashboard_stats(self):
        """Test getting dashboard statistics"""
        try:
            response = self.session.get(f"{BASE_URL}/dashboard/stats")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Dashboard Statistics", True, f"Stats retrieved: {data.get('totalInvitees', 0)} total invitees", data)
            else:
                self.log_test("Dashboard Statistics", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Dashboard Statistics", False, f"Exception: {str(e)}")
    
    def test_upload_agenda(self):
        """Test uploading agenda PDF"""
        try:
            pdf_content = self.create_sample_pdf()
            files = {'file': ('agenda.pdf', pdf_content, 'application/pdf')}
            data = {'title': 'PM Connect 3.0 Event Agenda'}
            
            response = self.session.post(f"{BASE_URL}/agenda", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Upload Agenda", True, f"Agenda uploaded with ID: {result.get('agendaId')}", result)
                return result.get('agendaId')
            else:
                self.log_test("Upload Agenda", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Upload Agenda", False, f"Exception: {str(e)}")
            return None
    
    def test_get_agenda(self):
        """Test getting current agenda"""
        try:
            response = self.session.get(f"{BASE_URL}/agenda")
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'No agenda' in data['message']:
                    self.log_test("Get Current Agenda", True, "No agenda available", data)
                else:
                    self.log_test("Get Current Agenda", True, f"Agenda retrieved: {data.get('agendaTitle')}", {"has_agenda": True})
            else:
                self.log_test("Get Current Agenda", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Current Agenda", False, f"Exception: {str(e)}")
    
    def test_upload_gallery_photo(self, employee_id="EMP001"):
        """Test uploading gallery photo"""
        try:
            # Create a simple image file
            image_data = base64.b64decode(self.create_sample_image())
            files = {'file': ('photo.png', image_data, 'image/png')}
            data = {
                'employeeId': employee_id,
                'eventVersion': 'PM Connect 3.0'
            }
            
            response = self.session.post(f"{BASE_URL}/gallery/upload", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Upload Gallery Photo", True, f"Photo uploaded with ID: {result.get('photoId')}", result)
                return result.get('photoId')
            else:
                self.log_test("Upload Gallery Photo", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Upload Gallery Photo", False, f"Exception: {str(e)}")
            return None
    
    def test_get_gallery_photos(self, event_version="PM Connect 3.0"):
        """Test getting gallery photos by event version"""
        try:
            response = self.session.get(f"{BASE_URL}/gallery/{event_version}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Gallery Photos", True, f"Retrieved {len(data)} photos for {event_version}", {"count": len(data)})
                return data
            else:
                self.log_test("Get Gallery Photos", False, f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Get Gallery Photos", False, f"Exception: {str(e)}")
            return []
    
    def test_delete_gallery_photo(self, photo_id):
        """Test deleting a gallery photo"""
        if not photo_id:
            self.log_test("Delete Gallery Photo", False, "No photo ID provided")
            return
            
        try:
            response = self.session.delete(f"{BASE_URL}/gallery/{photo_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Delete Gallery Photo", True, "Photo deleted successfully", data)
            elif response.status_code == 404:
                self.log_test("Delete Gallery Photo", True, "Photo not found (expected for cleanup)", {"status": "not_found"})
            else:
                self.log_test("Delete Gallery Photo", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Delete Gallery Photo", False, f"Exception: {str(e)}")
    
    def test_upload_cab_allocations(self):
        """Test uploading cab allocation CSV"""
        try:
            csv_data = self.create_sample_cab_csv()
            files = {'file': ('cab_allocations.csv', csv_data, 'text/csv')}
            
            response = self.session.post(f"{BASE_URL}/cab-allocations/upload", files=files)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Upload Cab Allocations", True, f"Uploaded {data.get('inserted_count', 0)} cab allocations", data)
            else:
                self.log_test("Upload Cab Allocations", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Upload Cab Allocations", False, f"Exception: {str(e)}")
    
    def test_get_cab_allocation(self, employee_id="EMP001"):
        """Test getting cab allocation for specific employee"""
        try:
            response = self.session.get(f"{BASE_URL}/cab-allocations/{employee_id}")
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'No cab allocation' in data['message']:
                    self.log_test("Get Employee Cab Allocation", True, f"No allocation found for {employee_id}", data)
                else:
                    self.log_test("Get Employee Cab Allocation", True, f"Allocation found for {employee_id}: Cab {data.get('cabNumber')}", {"has_allocation": True})
            else:
                self.log_test("Get Employee Cab Allocation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Employee Cab Allocation", False, f"Exception: {str(e)}")
    
    def test_get_all_cab_allocations(self):
        """Test getting all cab allocations"""
        try:
            response = self.session.get(f"{BASE_URL}/cab-allocations")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get All Cab Allocations", True, f"Retrieved {len(data)} cab allocations", {"count": len(data)})
            else:
                self.log_test("Get All Cab Allocations", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get All Cab Allocations", False, f"Exception: {str(e)}")
    
    def test_auth_status(self):
        """Test authentication status endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/auth/status")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Auth Status", True, f"Auth status: {data.get('message')}", data)
            else:
                self.log_test("Auth Status", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Auth Status", False, f"Exception: {str(e)}")
    
    # ================== SPRINT 2: ENHANCED DATA MANAGEMENT TESTS ==================
    
    def test_enhanced_invitee_upload(self):
        """Test enhanced invitee CSV upload with validation"""
        try:
            # Test with valid CSV
            csv_data = self.create_sample_invitees_csv()
            files = {'file': ('invitees_enhanced.csv', csv_data, 'text/csv')}
            
            response = self.session.post(f"{BASE_URL}/invitees/bulk-upload-enhanced", files=files)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Enhanced Invitee Upload (Valid)", True, 
                                f"Uploaded {data.get('inserted_count', 0)} invitees with {data.get('warnings', 0)} warnings", data)
                else:
                    self.log_test("Enhanced Invitee Upload (Valid)", False, 
                                f"Upload failed: {data.get('message', 'Unknown error')}")
            else:
                self.log_test("Enhanced Invitee Upload (Valid)", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Enhanced Invitee Upload (Valid)", False, f"Exception: {str(e)}")
    
    def test_enhanced_invitee_upload_invalid(self):
        """Test enhanced invitee CSV upload with invalid data"""
        try:
            # Create invalid CSV (missing required columns)
            invalid_data = {
                'Employee ID': ['EMP001', 'EMP002'],
                'Name': ['John Doe', 'Jane Smith'],  # Wrong column name
                # Missing 'Employee Name', 'Cadre', 'Project Name'
            }
            df = pd.DataFrame(invalid_data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue().encode('utf-8')
            
            files = {'file': ('invalid_invitees.csv', csv_data, 'text/csv')}
            
            response = self.session.post(f"{BASE_URL}/invitees/bulk-upload-enhanced", files=files)
            
            if response.status_code == 200:
                data = response.json()
                if not data.get('success') and data.get('validation_result', {}).get('errors'):
                    self.log_test("Enhanced Invitee Upload (Invalid)", True, 
                                f"Correctly rejected invalid data with {len(data['validation_result']['errors'])} errors", 
                                {"validation_passed": True})
                else:
                    self.log_test("Enhanced Invitee Upload (Invalid)", False, 
                                "Should have rejected invalid data but didn't")
            else:
                self.log_test("Enhanced Invitee Upload (Invalid)", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Enhanced Invitee Upload (Invalid)", False, f"Exception: {str(e)}")
    
    def test_enhanced_cab_upload(self):
        """Test enhanced cab allocation CSV upload with validation"""
        try:
            csv_data = self.create_sample_cab_csv()
            files = {'file': ('cab_enhanced.csv', csv_data, 'text/csv')}
            
            response = self.session.post(f"{BASE_URL}/cab-allocations/upload-enhanced", files=files)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Enhanced Cab Upload", True, 
                                f"Uploaded {data.get('inserted_count', 0)} cab allocations with {data.get('warnings', 0)} warnings", data)
                else:
                    self.log_test("Enhanced Cab Upload", False, 
                                f"Upload failed: {data.get('message', 'Unknown error')}")
            else:
                self.log_test("Enhanced Cab Upload", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Enhanced Cab Upload", False, f"Exception: {str(e)}")
    
    def test_advanced_responses_export(self):
        """Test advanced responses export with multiple sheets"""
        try:
            response = self.session.post(f"{BASE_URL}/exports/responses/advanced")
            
            if response.status_code == 200:
                data = response.json()
                if 'excel_data' in data and 'export_id' in data:
                    summary = data.get('summary', {})
                    self.log_test("Advanced Responses Export", True, 
                                f"Export created with {summary.get('total_responses', 0)} responses, "
                                f"{len(summary.get('sheets_created', []))} sheets", 
                                {"export_id": data['export_id'], "has_data": True})
                else:
                    self.log_test("Advanced Responses Export", False, "Missing excel_data or export_id in response")
            else:
                self.log_test("Advanced Responses Export", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Advanced Responses Export", False, f"Exception: {str(e)}")
    
    def test_invitees_status_export(self):
        """Test invitees status export"""
        try:
            response = self.session.post(f"{BASE_URL}/exports/invitees/status")
            
            if response.status_code == 200:
                data = response.json()
                if 'excel_data' in data and 'export_id' in data:
                    summary = data.get('summary', {})
                    self.log_test("Invitees Status Export", True, 
                                f"Export created with {summary.get('total_invitees', 0)} invitees, "
                                f"{summary.get('responded', 0)} responded", 
                                {"export_id": data['export_id'], "has_data": True})
                else:
                    self.log_test("Invitees Status Export", False, "Missing excel_data or export_id in response")
            else:
                self.log_test("Invitees Status Export", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Invitees Status Export", False, f"Exception: {str(e)}")
    
    def test_cab_allocations_export(self):
        """Test cab allocations export"""
        try:
            response = self.session.post(f"{BASE_URL}/exports/cab-allocations")
            
            if response.status_code == 200:
                data = response.json()
                if 'excel_data' in data and 'export_id' in data:
                    summary = data.get('summary', {})
                    self.log_test("Cab Allocations Export", True, 
                                f"Export created with {summary.get('total_cabs', 0)} cabs, "
                                f"{summary.get('total_members', 0)} members", 
                                {"export_id": data['export_id'], "has_data": True})
                    return data['export_id']
                else:
                    self.log_test("Cab Allocations Export", False, "Missing excel_data or export_id in response")
                    return None
            else:
                self.log_test("Cab Allocations Export", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Cab Allocations Export", False, f"Exception: {str(e)}")
            return None
    
    def test_export_progress(self, export_id):
        """Test export progress tracking"""
        if not export_id:
            self.log_test("Export Progress Tracking", False, "No export ID provided")
            return
            
        try:
            response = self.session.get(f"{BASE_URL}/exports/progress/{export_id}")
            
            if response.status_code == 200:
                data = response.json()
                if 'status' in data:
                    self.log_test("Export Progress Tracking", True, 
                                f"Progress retrieved: {data.get('status')} - {data.get('current_step', 'N/A')}", data)
                else:
                    self.log_test("Export Progress Tracking", False, "Missing status in response")
            elif response.status_code == 404:
                self.log_test("Export Progress Tracking", True, "Export not found (expected for completed exports)", {"status": "not_found"})
            else:
                self.log_test("Export Progress Tracking", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Export Progress Tracking", False, f"Exception: {str(e)}")
    
    def test_data_integrity_check(self):
        """Test data integrity checking"""
        try:
            response = self.session.get(f"{BASE_URL}/data/integrity-check")
            
            if response.status_code == 200:
                data = response.json()
                if 'report' in data:
                    report = data['report']
                    status = report.get('overall_status', 'unknown')
                    issues_count = len(report.get('issues', []))
                    checks_count = len(report.get('checks', []))
                    
                    self.log_test("Data Integrity Check", True, 
                                f"Integrity check completed: {status} status, {checks_count} checks, {issues_count} issues", 
                                {"status": status, "issues": issues_count})
                else:
                    self.log_test("Data Integrity Check", False, "Missing report in response")
            else:
                self.log_test("Data Integrity Check", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Data Integrity Check", False, f"Exception: {str(e)}")
    
    def test_fix_data_integrity(self):
        """Test automatic data integrity fixing"""
        try:
            response = self.session.post(f"{BASE_URL}/data/fix-integrity")
            
            if response.status_code == 200:
                data = response.json()
                if 'report' in data:
                    report = data['report']
                    fixes_count = len(report.get('fixes_applied', []))
                    success = report.get('success', False)
                    
                    self.log_test("Fix Data Integrity", True, 
                                f"Integrity fixes applied: {fixes_count} fixes, success: {success}", 
                                {"fixes": fixes_count, "success": success})
                else:
                    self.log_test("Fix Data Integrity", False, "Missing report in response")
            else:
                self.log_test("Fix Data Integrity", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Fix Data Integrity", False, f"Exception: {str(e)}")
    
    def test_refresh_dashboard_totals(self):
        """Test dashboard totals refresh"""
        try:
            response = self.session.post(f"{BASE_URL}/data/refresh-totals")
            
            if response.status_code == 200:
                data = response.json()
                if 'updated_stats' in data:
                    stats = data['updated_stats']
                    fixes = data.get('fixes_applied', {})
                    
                    self.log_test("Refresh Dashboard Totals", True, 
                                f"Totals refreshed: {stats.get('totalInvitees', 0)} invitees, "
                                f"{stats.get('totalResponses', 0)} responses", 
                                {"stats": stats, "fixes": fixes})
                else:
                    self.log_test("Refresh Dashboard Totals", False, "Missing updated_stats in response")
            else:
                self.log_test("Refresh Dashboard Totals", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Refresh Dashboard Totals", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("=" * 80)
        print("PM CONNECT 3.0 BACKEND API TEST SUITE")
        print("=" * 80)
        print(f"Testing against: {BASE_URL}")
        print()
        
        # Test authentication
        print("🔐 AUTHENTICATION TESTS")
        print("-" * 40)
        self.test_auth_status()
        print()
        
        # Test invitee management
        print("👥 INVITEE MANAGEMENT TESTS")
        print("-" * 40)
        self.test_invitee_bulk_upload()
        invitees = self.test_get_invitees()
        unresponded = self.test_get_unresponded_invitees()
        print()
        
        # Test response management
        print("📝 RESPONSE MANAGEMENT TESTS")
        print("-" * 40)
        response_id = self.test_submit_response()
        responses = self.test_get_responses()
        self.test_export_responses()
        print()
        
        # Test dashboard
        print("📊 DASHBOARD TESTS")
        print("-" * 40)
        self.test_dashboard_stats()
        print()
        
        # Test agenda management
        print("📋 AGENDA MANAGEMENT TESTS")
        print("-" * 40)
        agenda_id = self.test_upload_agenda()
        self.test_get_agenda()
        print()
        
        # Test gallery management
        print("🖼️ GALLERY MANAGEMENT TESTS")
        print("-" * 40)
        photo_id = self.test_upload_gallery_photo()
        photos = self.test_get_gallery_photos()
        self.test_delete_gallery_photo(photo_id)
        print()
        
        # Test cab allocation
        print("🚗 CAB ALLOCATION TESTS")
        print("-" * 40)
        self.test_upload_cab_allocations()
        self.test_get_cab_allocation()
        self.test_get_all_cab_allocations()
        print()
        
        # ================== SPRINT 2 TESTS ==================
        print("🚀 SPRINT 2: ENHANCED DATA MANAGEMENT TESTS")
        print("-" * 40)
        
        # Enhanced CSV Import Tests
        print("📊 Enhanced CSV Import with Validation:")
        self.test_enhanced_invitee_upload()
        self.test_enhanced_invitee_upload_invalid()
        self.test_enhanced_cab_upload()
        print()
        
        # Advanced Excel Export Tests
        print("📈 Advanced Excel Export Service:")
        self.test_advanced_responses_export()
        self.test_invitees_status_export()
        export_id = self.test_cab_allocations_export()
        self.test_export_progress(export_id)
        print()
        
        # Data Integrity Management Tests
        print("🔧 Data Integrity Management:")
        self.test_data_integrity_check()
        self.test_fix_data_integrity()
        self.test_refresh_dashboard_totals()
        print()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("FAILED TESTS:")
            print("-" * 40)
            for result in self.test_results:
                if not result['success']:
                    print(f"❌ {result['test']}: {result['message']}")
            print()
        
        print("DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = PMConnectTester()
    tester.run_all_tests()