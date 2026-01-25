#!/usr/bin/env python3
"""
Backend API Testing for Infographic MVP
Tests the Gemini Blueprint → Prompt Compiler → Nano Banana Pro pipeline
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class InfographicAPITester:
    def __init__(self, base_url="https://graphgen-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def test_health_check(self):
        """Test /api/health endpoint"""
        print(f"\n🔍 Testing Health Check...")
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Health Check", True, f"Status: {data}")
                    return True
                else:
                    self.log_test("Health Check", False, f"Unexpected response: {data}")
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
        return False

    def test_root_endpoint(self):
        """Test /api/ root endpoint"""
        print(f"\n🔍 Testing Root API Endpoint...")
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "Infographic MVP API" in data.get("message", ""):
                    self.log_test("Root API Endpoint", True, f"Message: {data.get('message')}")
                    return True
                else:
                    self.log_test("Root API Endpoint", False, f"Unexpected message: {data}")
            else:
                self.log_test("Root API Endpoint", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Root API Endpoint", False, f"Exception: {str(e)}")
        return False

    def test_generate_with_text(self):
        """Test /api/generate endpoint with text input"""
        print(f"\n🔍 Testing Generate Endpoint with Text...")
        
        # Sample report text for testing
        test_text = """
        Network Infrastructure Assessment Report
        
        Executive Summary:
        During our site visit to the corporate office, we identified several critical network infrastructure issues that require immediate attention.
        
        Key Findings:
        - Network rack organization is poor with tangled cables
        - Power management lacks UPS backup for critical devices
        - CCTV system has water ingress issues
        - Several cameras show rust and corrosion
        
        Actions Taken:
        - Reorganized network rack with proper cable management
        - Installed UPS for all network devices
        - Re-crimped all network connections
        - Cleaned and tested CCTV cameras
        
        Recommendations:
        - Install dedicated 8-port PoE switch
        - Upgrade to outdoor-rated PoE cameras
        - Use waterproof junction boxes for all outdoor connections
        - Implement regular maintenance schedule
        
        Expected Outcomes:
        - Improved network reliability and uptime
        - Better CCTV coverage and image quality
        - Reduced maintenance costs
        - Enhanced security monitoring capabilities
        """
        
        try:
            # Prepare form data
            data = {"prompt": test_text}
            
            print("   Sending request to generate endpoint...")
            response = requests.post(
                f"{self.api_url}/generate", 
                data=data,
                timeout=120  # 2 minute timeout for AI processing
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if response has expected structure
                if result.get("ok") == True:
                    # Check for required fields
                    has_image = "image" in result and result["image"].get("data")
                    has_blueprint = "blueprint" in result
                    has_prompt_preview = "compiled_prompt_preview" in result
                    
                    details = f"Image: {'✓' if has_image else '✗'}, Blueprint: {'✓' if has_blueprint else '✗'}, Prompt: {'✓' if has_prompt_preview else '✗'}"
                    
                    if has_image and has_blueprint:
                        # Check blueprint structure
                        blueprint = result["blueprint"]
                        bp_valid = all(key in blueprint for key in ["title", "sections"])
                        
                        if bp_valid:
                            self.log_test("Generate with Text", True, 
                                        f"Full pipeline success. {details}. Blueprint title: {blueprint.get('title', 'N/A')}")
                            return True
                        else:
                            self.log_test("Generate with Text", False, 
                                        f"Invalid blueprint structure: {blueprint}")
                    else:
                        self.log_test("Generate with Text", False, f"Missing required fields. {details}")
                else:
                    error_msg = result.get("error", "Unknown error")
                    self.log_test("Generate with Text", False, f"API returned ok:false - {error_msg}")
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", f"HTTP {response.status_code}")
                except:
                    error_msg = f"HTTP {response.status_code}"
                self.log_test("Generate with Text", False, f"Request failed: {error_msg}")
                
        except requests.exceptions.Timeout:
            self.log_test("Generate with Text", False, "Request timeout (>120s)")
        except Exception as e:
            self.log_test("Generate with Text", False, f"Exception: {str(e)}")
        
        return False

    def test_generate_empty_input(self):
        """Test /api/generate endpoint with empty input (should fail)"""
        print(f"\n🔍 Testing Generate Endpoint with Empty Input...")
        try:
            data = {"prompt": ""}
            response = requests.post(f"{self.api_url}/generate", data=data, timeout=30)
            
            if response.status_code == 400:
                self.log_test("Generate Empty Input Validation", True, "Correctly rejected empty input")
                return True
            else:
                result = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                self.log_test("Generate Empty Input Validation", False, 
                            f"Expected 400, got {response.status_code}: {result}")
        except Exception as e:
            self.log_test("Generate Empty Input Validation", False, f"Exception: {str(e)}")
        return False

    def test_debug_endpoints(self):
        """Test debug endpoints if available"""
        print(f"\n🔍 Testing Debug Endpoints...")
        
        # Test blueprint debug endpoint
        try:
            response = requests.get(f"{self.api_url}/debug/blueprint", timeout=10)
            if response.status_code == 200:
                self.log_test("Debug Blueprint Endpoint", True, "Accessible")
            else:
                self.log_test("Debug Blueprint Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Debug Blueprint Endpoint", False, f"Exception: {str(e)}")
        
        # Test prompt debug endpoint
        try:
            response = requests.get(f"{self.api_url}/debug/prompt", timeout=10)
            if response.status_code == 200:
                self.log_test("Debug Prompt Endpoint", True, "Accessible")
            else:
                self.log_test("Debug Prompt Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Debug Prompt Endpoint", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all backend API tests"""
        print("=" * 60)
        print("🚀 INFOGRAPHIC MVP BACKEND API TESTING")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run tests in order
        self.test_health_check()
        self.test_root_endpoint()
        self.test_generate_empty_input()
        self.test_generate_with_text()  # This is the main test
        self.test_debug_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            return 0
        else:
            print("⚠️  SOME TESTS FAILED")
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
            return 1

def main():
    """Main test execution"""
    tester = InfographicAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())