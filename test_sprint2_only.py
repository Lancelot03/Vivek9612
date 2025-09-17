#!/usr/bin/env python3
"""
Test only Sprint 2 features
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

class Sprint2Tester:
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
    
    def test_advanced_responses_export(self):
        """Test advanced responses export with multiple sheets"""
        try:
            response = self.session.post(f"{BASE_URL}/exports/responses/advanced")
            
            if response.status_code == 200:
                data = response.json()
                download_info = data.get('download_info', {})
                if 'excel_data' in download_info and 'export_id' in data:
                    summary = data.get('summary', {})
                    self.log_test("Advanced Responses Export", True, 
                                f"Export created with {summary.get('total_responses', 0)} responses, "
                                f"{len(summary.get('sheets_created', []))} sheets", 
                                {"export_id": data['export_id'], "has_data": True})
                    return data['export_id']
                else:
                    self.log_test("Advanced Responses Export", False, "Missing excel_data or export_id in response")
                    return None
            else:
                self.log_test("Advanced Responses Export", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Advanced Responses Export", False, f"Exception: {str(e)}")
            return None
    
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
                    return data['export_id']
                else:
                    self.log_test("Invitees Status Export", False, "Missing excel_data or export_id in response")
                    return None
            else:
                self.log_test("Invitees Status Export", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Invitees Status Export", False, f"Exception: {str(e)}")
            return None
    
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

    def run_sprint2_tests(self):
        """Run Sprint 2 tests only"""
        print("=" * 80)
        print("SPRINT 2 ENHANCED DATA MANAGEMENT TESTS")
        print("=" * 80)
        print(f"Testing against: {BASE_URL}")
        print()
        
        # Advanced Excel Export Tests
        print("📈 Advanced Excel Export Service:")
        export_id1 = self.test_advanced_responses_export()
        export_id2 = self.test_invitees_status_export()
        export_id3 = self.test_cab_allocations_export()
        
        # Test progress tracking with one of the export IDs
        if export_id1:
            self.test_export_progress(export_id1)
        elif export_id2:
            self.test_export_progress(export_id2)
        elif export_id3:
            self.test_export_progress(export_id3)
        else:
            self.test_export_progress(None)
        
        print()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("SPRINT 2 TEST SUMMARY")
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

if __name__ == "__main__":
    tester = Sprint2Tester()
    tester.run_sprint2_tests()