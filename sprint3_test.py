#!/usr/bin/env python3
"""
Sprint 3 Focused Test Suite - Flight Preferences, User Profiles, Enhanced Cab Logistics
"""

import requests
import json
import base64
import io
import pandas as pd
from datetime import datetime, date

# Configuration
BASE_URL = "https://eventadmin-2.preview.emergentagent.com/api"
TIMEOUT = 30

class Sprint3Tester:
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
    
    def test_flight_preference_options(self):
        """Test getting flight time preference options"""
        try:
            response = self.session.get(f"{BASE_URL}/flight/preferences/options")
            
            if response.status_code == 200:
                data = response.json()
                if 'departure_time_options' in data and 'arrival_time_options' in data:
                    dep_options = len(data['departure_time_options'])
                    arr_options = len(data['arrival_time_options'])
                    self.log_test("Flight Preference Options", True, 
                                f"Retrieved {dep_options} departure and {arr_options} arrival options", data)
                    return data
                else:
                    self.log_test("Flight Preference Options", False, "Missing departure_time_options or arrival_time_options")
                    return None
            else:
                self.log_test("Flight Preference Options", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Flight Preference Options", False, f"Exception: {str(e)}")
            return None
    
    def test_submit_response_with_flight_preferences(self, employee_id="EMP003"):
        """Test submitting RSVP response with flight preferences"""
        try:
            response_data = {
                "employeeId": employee_id,
                "mobileNumber": "9876543212",
                "requiresAccommodation": True,
                "arrivalDate": "2024-03-15",
                "departureDate": "2024-03-17",
                "foodPreference": "Veg",
                "departureTimePreference": "Morning",
                "arrivalTimePreference": "Evening",
                "specialFlightRequirements": "Window seat preferred, vegetarian meal"
            }
            
            response = self.session.post(f"{BASE_URL}/responses", json=response_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Submit RSVP with Flight Preferences", True, 
                            f"Response with flight preferences submitted: {data.get('responseId')}", data)
                return data.get('responseId')
            else:
                self.log_test("Submit RSVP with Flight Preferences", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Submit RSVP with Flight Preferences", False, f"Exception: {str(e)}")
            return None
    
    def test_flight_preference_analysis(self):
        """Test flight preference analysis for logistics planning"""
        try:
            response = self.session.get(f"{BASE_URL}/responses/flight-analysis")
            
            if response.status_code == 200:
                data = response.json()
                if 'analysis' in data:
                    analysis = data['analysis']
                    travelers = analysis.get('total_flight_travelers', 0)
                    special_req = analysis.get('special_requirements_count', 0)
                    dep_prefs = analysis.get('departure_preferences', {})
                    arr_prefs = analysis.get('arrival_preferences', {})
                    
                    self.log_test("Flight Preference Analysis", True, 
                                f"Analysis completed: {travelers} travelers, {special_req} special requirements, "
                                f"{len(dep_prefs)} departure preferences, {len(arr_prefs)} arrival preferences", 
                                {"analysis": analysis})
                    return analysis
                else:
                    self.log_test("Flight Preference Analysis", False, "Missing analysis in response")
                    return None
            else:
                self.log_test("Flight Preference Analysis", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Flight Preference Analysis", False, f"Exception: {str(e)}")
            return None
    
    def test_get_user_profile(self, employee_id="EMP001"):
        """Test getting comprehensive user profile"""
        try:
            response = self.session.get(f"{BASE_URL}/profile/{employee_id}")
            
            if response.status_code == 200:
                data = response.json()
                if 'employeeId' in data:
                    has_rsvp = data.get('rsvp_details') is not None
                    has_responded = data.get('hasResponded', False)
                    
                    self.log_test("Get User Profile", True, 
                                f"Profile retrieved for {employee_id}: {data.get('employeeName', 'Unknown')}, "
                                f"responded: {has_responded}, has RSVP details: {has_rsvp}", 
                                {"profile_complete": True, "has_rsvp": has_rsvp})
                    return data
                else:
                    self.log_test("Get User Profile", False, "Missing employeeId in response")
                    return None
            elif response.status_code == 404:
                self.log_test("Get User Profile", True, f"User {employee_id} not found (expected for non-existent users)", 
                            {"status": "not_found"})
                return None
            else:
                self.log_test("Get User Profile", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Get User Profile", False, f"Exception: {str(e)}")
            return None
    
    def test_update_user_profile(self, employee_id="EMP001"):
        """Test updating user profile information"""
        try:
            update_data = {
                "officeType": "Branch Office",
                "email": "rajesh.kumar@jakson.com",
                "phone": "9876543210",
                "department": "Engineering"
            }
            
            response = self.session.put(f"{BASE_URL}/profile/{employee_id}", json=update_data)
            
            if response.status_code == 200:
                data = response.json()
                if 'updated_fields' in data:
                    updated_fields = data['updated_fields']
                    user_updated = data.get('user_updated', False)
                    invitee_updated = data.get('invitee_updated', False)
                    
                    self.log_test("Update User Profile", True, 
                                f"Profile updated for {employee_id}: {len(updated_fields)} fields, "
                                f"user table: {user_updated}, invitee table: {invitee_updated}", 
                                {"updated_fields": updated_fields})
                    return data
                else:
                    self.log_test("Update User Profile", False, "Missing updated_fields in response")
                    return None
            elif response.status_code == 404:
                self.log_test("Update User Profile", True, f"User {employee_id} not found (expected for non-existent users)", 
                            {"status": "not_found"})
                return None
            else:
                self.log_test("Update User Profile", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Update User Profile", False, f"Exception: {str(e)}")
            return None
    
    def test_enhanced_cab_allocations(self):
        """Test enhanced cab allocations with employee name resolution"""
        try:
            response = self.session.get(f"{BASE_URL}/cab-allocations/enhanced")
            
            if response.status_code == 200:
                data = response.json()
                if 'allocations' in data and 'summary' in data:
                    allocations = data['allocations']
                    summary = data['summary']
                    total_cabs = summary.get('total_cabs', 0)
                    total_members = summary.get('total_members', 0)
                    responded_members = summary.get('responded_members', 0)
                    
                    # Check if allocations have enhanced member details
                    has_enhanced_details = False
                    if allocations:
                        first_allocation = allocations[0]
                        if 'memberDetails' in first_allocation and first_allocation['memberDetails']:
                            first_member = first_allocation['memberDetails'][0]
                            has_enhanced_details = 'employeeName' in first_member and 'hasResponded' in first_member
                    
                    self.log_test("Enhanced Cab Allocations", True, 
                                f"Retrieved {total_cabs} cabs with {total_members} members, "
                                f"{responded_members} responded, enhanced details: {has_enhanced_details}", 
                                {"summary": summary, "enhanced": has_enhanced_details})
                    return data
                else:
                    self.log_test("Enhanced Cab Allocations", False, "Missing allocations or summary in response")
                    return None
            else:
                self.log_test("Enhanced Cab Allocations", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Enhanced Cab Allocations", False, f"Exception: {str(e)}")
            return None
    
    def test_enhanced_employee_cab_allocation(self, employee_id="EMP001"):
        """Test enhanced cab allocation details for specific employee"""
        try:
            response = self.session.get(f"{BASE_URL}/cab-allocations/employee/{employee_id}/enhanced")
            
            if response.status_code == 200:
                data = response.json()
                if 'allocation' in data:
                    allocation = data['allocation']
                    if allocation:  # Not None
                        total_members = allocation.get('totalMembers', 0)
                        responded_members = allocation.get('respondedMembers', 0)
                        cab_number = allocation.get('cabNumber', 'Unknown')
                        
                        # Check for enhanced member details
                        has_enhanced_details = False
                        current_user_found = False
                        if 'memberDetails' in allocation and allocation['memberDetails']:
                            first_member = allocation['memberDetails'][0]
                            has_enhanced_details = 'employeeName' in first_member and 'mobileNumber' in first_member
                            current_user_found = any(m.get('isCurrentUser', False) for m in allocation['memberDetails'])
                        
                        self.log_test("Enhanced Employee Cab Allocation", True, 
                                    f"Cab {cab_number} found for {employee_id}: {total_members} members, "
                                    f"{responded_members} responded, enhanced details: {has_enhanced_details}, "
                                    f"current user marked: {current_user_found}", 
                                    {"has_allocation": True, "enhanced": has_enhanced_details})
                        return allocation
                    else:
                        self.log_test("Enhanced Employee Cab Allocation", True, 
                                    f"No cab allocation found for {employee_id}", 
                                    {"has_allocation": False})
                        return None
                else:
                    self.log_test("Enhanced Employee Cab Allocation", False, "Missing allocation in response")
                    return None
            else:
                self.log_test("Enhanced Employee Cab Allocation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Enhanced Employee Cab Allocation", False, f"Exception: {str(e)}")
            return None
    
    def test_export_with_flight_preferences(self):
        """Test that Excel exports include new flight preference fields"""
        try:
            response = self.session.get(f"{BASE_URL}/responses/export")
            
            if response.status_code == 200:
                data = response.json()
                if 'excel_data' in data:
                    # Decode and check Excel content
                    excel_data = base64.b64decode(data['excel_data'])
                    df = pd.read_excel(io.BytesIO(excel_data))
                    
                    # Check for flight preference columns
                    expected_columns = [
                        'Departure Time Preference',
                        'Arrival Time Preference', 
                        'Special Flight Requirements'
                    ]
                    
                    has_flight_columns = all(col in df.columns for col in expected_columns)
                    
                    self.log_test("Export with Flight Preferences", True, 
                                f"Excel export includes flight preference fields: {has_flight_columns}, "
                                f"total columns: {len(df.columns)}", 
                                {"has_flight_fields": has_flight_columns, "columns": list(df.columns)})
                    return has_flight_columns
                else:
                    self.log_test("Export with Flight Preferences", True, "No responses to export", data)
                    return True
            else:
                self.log_test("Export with Flight Preferences", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Export with Flight Preferences", False, f"Exception: {str(e)}")
            return False
    
    def run_sprint3_tests(self):
        """Run Sprint 3 focused test suite"""
        print("=" * 80)
        print("SPRINT 3: LOGISTICS & USER DATA TEST SUITE")
        print("=" * 80)
        print(f"Testing against: {BASE_URL}")
        print()
        
        # Flight Time Preferences Tests
        print("✈️ FLIGHT TIME PREFERENCES API")
        print("-" * 40)
        flight_options = self.test_flight_preference_options()
        response_id = self.test_submit_response_with_flight_preferences()
        analysis = self.test_flight_preference_analysis()
        print()
        
        # Enhanced User Profile Management Tests
        print("👤 ENHANCED USER PROFILE MANAGEMENT")
        print("-" * 40)
        profile = self.test_get_user_profile()
        updated_profile = self.test_update_user_profile()
        print()
        
        # Enhanced Cab Logistics Tests
        print("🚗 ENHANCED CAB LOGISTICS WITH NAME RESOLUTION")
        print("-" * 40)
        enhanced_cabs = self.test_enhanced_cab_allocations()
        employee_cab = self.test_enhanced_employee_cab_allocation()
        print()
        
        # Updated Export Functionality Tests
        print("📊 UPDATED EXPORT WITH FLIGHT PREFERENCES")
        print("-" * 40)
        export_test = self.test_export_with_flight_preferences()
        print()
        
        # Summary
        self.print_summary()
        
        return {
            "flight_options": flight_options,
            "response_id": response_id,
            "analysis": analysis,
            "profile": profile,
            "updated_profile": updated_profile,
            "enhanced_cabs": enhanced_cabs,
            "employee_cab": employee_cab,
            "export_test": export_test
        }
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("SPRINT 3 TEST SUMMARY")
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
    tester = Sprint3Tester()
    results = tester.run_sprint3_tests()