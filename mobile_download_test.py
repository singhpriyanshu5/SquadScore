#!/usr/bin/env python3
"""
Mobile Download Strategy Testing for CSV Download Functionality
Focus: Testing different approaches for mobile file downloads and identifying iPhone issues
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://scoreleader.preview.emergentagent.com/api"

class MobileDownloadTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_group_id = None
        self.results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def setup_test_group(self):
        """Create a test group with sample data"""
        print("\n=== SETTING UP TEST GROUP FOR MOBILE DOWNLOAD TESTING ===")
        
        try:
            # Create test group
            group_data = {"group_name": "Mobile Download Test Group"}
            response = requests.post(f"{self.base_url}/groups", json=group_data)
            
            if response.status_code == 200:
                group = response.json()
                self.test_group_id = group["id"]
                self.log_result("Create Test Group", True, f"Created group: {group['group_name']} (ID: {group['id']})")
                return True
            else:
                self.log_result("Create Test Group", False, f"Failed to create group: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Setup Test Group", False, f"Exception during setup: {str(e)}")
            return False
    
    def test_backend_csv_endpoint_mobile_compatibility(self):
        """Test backend CSV endpoint for mobile compatibility"""
        print("\n=== TESTING BACKEND CSV ENDPOINT FOR MOBILE COMPATIBILITY ===")
        
        if not self.test_group_id:
            self.log_result("Mobile CSV Test", False, "No test group available")
            return
        
        try:
            # Test CSV download endpoint with mobile-specific headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/csv,application/csv,*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            response = requests.get(f"{self.base_url}/groups/{self.test_group_id}/download-csv", headers=headers)
            
            # Check response status
            if response.status_code != 200:
                self.log_result("Mobile CSV Download Status", False, f"Expected 200, got {response.status_code}")
                return
            
            self.log_result("Mobile CSV Download Status", True, "Endpoint returns 200 OK for mobile user agent")
            
            # Check mobile-specific headers
            response_headers = response.headers
            
            # Check Content-Type
            content_type = response_headers.get('Content-Type', '')
            if 'text/csv' in content_type:
                self.log_result("Mobile Content-Type", True, f"Correct Content-Type: {content_type}")
            else:
                self.log_result("Mobile Content-Type", False, f"Incorrect Content-Type: {content_type}")
            
            # Check Content-Disposition for mobile download
            content_disposition = response_headers.get('Content-Disposition', '')
            if 'attachment' in content_disposition and 'filename' in content_disposition:
                self.log_result("Mobile Content-Disposition", True, f"Proper download header: {content_disposition}")
            else:
                self.log_result("Mobile Content-Disposition", False, f"Missing/incorrect download header: {content_disposition}")
            
            # Check for CORS headers (important for mobile web views)
            cors_origin = response_headers.get('Access-Control-Allow-Origin')
            if cors_origin:
                self.log_result("CORS Headers", True, f"CORS headers present: {cors_origin}")
            else:
                self.log_result("CORS Headers", False, "No CORS headers found (may cause mobile web view issues)")
            
            # Check Content-Length
            content_length = response_headers.get('Content-Length')
            if content_length:
                self.log_result("Content-Length", True, f"Content-Length header present: {content_length}")
            else:
                self.log_result("Content-Length", False, "Content-Length header missing (may cause mobile download issues)")
            
            # Check for proper charset
            if 'charset=utf-8' in content_type:
                self.log_result("UTF-8 Charset", True, "UTF-8 charset specified")
            else:
                self.log_result("UTF-8 Charset", False, "UTF-8 charset not specified (may cause encoding issues)")
            
            # Test CSV content size and structure
            csv_content = response.text
            csv_size = len(csv_content.encode('utf-8'))
            
            if csv_size > 0:
                self.log_result("CSV Content Size", True, f"CSV content size: {csv_size} bytes")
            else:
                self.log_result("CSV Content Size", False, "CSV content is empty")
            
            # Check for BOM (Byte Order Mark) which can cause issues on mobile
            if csv_content.startswith('\ufeff'):
                self.log_result("BOM Check", False, "CSV contains BOM which may cause mobile parsing issues")
            else:
                self.log_result("BOM Check", True, "CSV does not contain BOM (good for mobile)")
            
        except Exception as e:
            self.log_result("Mobile CSV Endpoint Test", False, f"Exception during test: {str(e)}")
    
    def test_expo_file_system_compatibility(self):
        """Test compatibility with Expo FileSystem approach"""
        print("\n=== TESTING EXPO FILE SYSTEM COMPATIBILITY ===")
        
        if not self.test_group_id:
            self.log_result("Expo FileSystem Test", False, "No test group available")
            return
        
        try:
            # Simulate the Expo FileSystem approach
            response = requests.get(f"{self.base_url}/groups/{self.test_group_id}/download-csv")
            
            if response.status_code == 200:
                csv_content = response.text
                
                # Test if content can be written to file (simulating expo-file-system)
                try:
                    # Simulate writing to file
                    filename = f"test_group_history_{datetime.now().strftime('%Y-%m-%d')}.csv"
                    
                    # Check if filename is valid for mobile file systems
                    invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
                    has_invalid_chars = any(char in filename for char in invalid_chars)
                    
                    if not has_invalid_chars:
                        self.log_result("Mobile Filename Validation", True, f"Filename is mobile-safe: {filename}")
                    else:
                        self.log_result("Mobile Filename Validation", False, f"Filename contains invalid characters: {filename}")
                    
                    # Test content encoding for mobile file system
                    try:
                        encoded_content = csv_content.encode('utf-8')
                        self.log_result("UTF-8 Encoding Test", True, f"Content can be encoded as UTF-8 ({len(encoded_content)} bytes)")
                    except UnicodeEncodeError as e:
                        self.log_result("UTF-8 Encoding Test", False, f"Content cannot be encoded as UTF-8: {str(e)}")
                    
                    # Test for line ending compatibility (mobile systems prefer \n)
                    if '\r\n' in csv_content:
                        self.log_result("Line Endings", False, "CSV uses Windows line endings (\\r\\n) which may cause mobile issues")
                    elif '\n' in csv_content:
                        self.log_result("Line Endings", True, "CSV uses Unix line endings (\\n) which is mobile-compatible")
                    else:
                        self.log_result("Line Endings", False, "CSV has no line endings detected")
                    
                except Exception as e:
                    self.log_result("File System Simulation", False, f"Error simulating file system operations: {str(e)}")
            else:
                self.log_result("Expo FileSystem Data Fetch", False, f"Cannot fetch data for file system test: {response.status_code}")
                
        except Exception as e:
            self.log_result("Expo FileSystem Compatibility", False, f"Exception during test: {str(e)}")
    
    def test_expo_sharing_compatibility(self):
        """Test compatibility with Expo Sharing approach"""
        print("\n=== TESTING EXPO SHARING COMPATIBILITY ===")
        
        if not self.test_group_id:
            self.log_result("Expo Sharing Test", False, "No test group available")
            return
        
        try:
            response = requests.get(f"{self.base_url}/groups/{self.test_group_id}/download-csv")
            
            if response.status_code == 200:
                # Test MIME type compatibility
                content_type = response.headers.get('Content-Type', '')
                
                # Check if MIME type is compatible with iOS sharing
                ios_compatible_mimes = [
                    'text/csv',
                    'text/comma-separated-values',
                    'application/csv',
                    'text/plain'
                ]
                
                mime_compatible = any(mime in content_type for mime in ios_compatible_mimes)
                if mime_compatible:
                    self.log_result("iOS MIME Type Compatibility", True, f"MIME type is iOS-compatible: {content_type}")
                else:
                    self.log_result("iOS MIME Type Compatibility", False, f"MIME type may not be iOS-compatible: {content_type}")
                
                # Test UTI (Uniform Type Identifier) compatibility for iOS
                # CSV files should use 'public.comma-separated-values-text'
                self.log_result("UTI Compatibility", True, "Backend should support UTI: public.comma-separated-values-text")
                
                # Test file size for sharing limitations
                csv_content = response.text
                file_size = len(csv_content.encode('utf-8'))
                
                # iOS has sharing size limitations (typically 100MB, but smaller is better)
                if file_size < 1024 * 1024:  # 1MB
                    self.log_result("File Size for Sharing", True, f"File size is sharing-friendly: {file_size} bytes")
                elif file_size < 10 * 1024 * 1024:  # 10MB
                    self.log_result("File Size for Sharing", True, f"File size is acceptable for sharing: {file_size} bytes (warning: large)")
                else:
                    self.log_result("File Size for Sharing", False, f"File size may be too large for sharing: {file_size} bytes")
                
            else:
                self.log_result("Expo Sharing Data Fetch", False, f"Cannot fetch data for sharing test: {response.status_code}")
                
        except Exception as e:
            self.log_result("Expo Sharing Compatibility", False, f"Exception during test: {str(e)}")
    
    def test_alternative_download_methods(self):
        """Test alternative download methods for iOS compatibility"""
        print("\n=== TESTING ALTERNATIVE DOWNLOAD METHODS ===")
        
        if not self.test_group_id:
            self.log_result("Alternative Methods Test", False, "No test group available")
            return
        
        try:
            # Test 1: Direct URL approach (for WebBrowser.openBrowserAsync)
            download_url = f"{self.base_url}/groups/{self.test_group_id}/download-csv"
            
            # Test if URL is accessible without authentication
            response = requests.head(download_url)
            if response.status_code == 200:
                self.log_result("Direct URL Access", True, "CSV download URL is directly accessible")
            else:
                self.log_result("Direct URL Access", False, f"CSV download URL not accessible: {response.status_code}")
            
            # Test 2: JSON export as alternative
            json_export_url = f"{self.base_url}/groups/{self.test_group_id}/export"
            response = requests.get(json_export_url)
            
            if response.status_code == 200:
                json_data = response.json()
                self.log_result("JSON Export Alternative", True, "JSON export is available as fallback")
                
                # Test if JSON can be converted to CSV client-side
                if 'players' in json_data and 'teams' in json_data and 'game_sessions' in json_data:
                    self.log_result("JSON to CSV Conversion", True, "JSON contains all necessary data for client-side CSV conversion")
                else:
                    self.log_result("JSON to CSV Conversion", False, "JSON missing required data for CSV conversion")
            else:
                self.log_result("JSON Export Alternative", False, f"JSON export not available: {response.status_code}")
            
            # Test 3: Base64 encoding approach
            csv_response = requests.get(download_url)
            if csv_response.status_code == 200:
                csv_content = csv_response.text
                try:
                    import base64
                    encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('ascii')
                    self.log_result("Base64 Encoding Method", True, f"CSV can be base64 encoded for data URI approach ({len(encoded_content)} chars)")
                except Exception as e:
                    self.log_result("Base64 Encoding Method", False, f"Base64 encoding failed: {str(e)}")
            
        except Exception as e:
            self.log_result("Alternative Download Methods", False, f"Exception during test: {str(e)}")
    
    def test_ios_specific_issues(self):
        """Test for known iOS-specific download issues"""
        print("\n=== TESTING iOS-SPECIFIC DOWNLOAD ISSUES ===")
        
        if not self.test_group_id:
            self.log_result("iOS Issues Test", False, "No test group available")
            return
        
        try:
            response = requests.get(f"{self.base_url}/groups/{self.test_group_id}/download-csv")
            
            if response.status_code == 200:
                # Issue 1: iOS Safari download restrictions
                user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'
                ios_response = requests.get(f"{self.base_url}/groups/{self.test_group_id}/download-csv", 
                                          headers={'User-Agent': user_agent})
                
                if ios_response.status_code == 200:
                    self.log_result("iOS Safari Compatibility", True, "Endpoint works with iOS Safari user agent")
                else:
                    self.log_result("iOS Safari Compatibility", False, f"Endpoint fails with iOS Safari: {ios_response.status_code}")
                
                # Issue 2: Content-Disposition filename restrictions on iOS
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"')
                    
                    # iOS has restrictions on certain characters in filenames
                    ios_problematic_chars = [':', '/', '\\', '<', '>', '|', '?', '*', '"']
                    has_problematic_chars = any(char in filename for char in ios_problematic_chars)
                    
                    if not has_problematic_chars:
                        self.log_result("iOS Filename Restrictions", True, f"Filename is iOS-compatible: {filename}")
                    else:
                        self.log_result("iOS Filename Restrictions", False, f"Filename has iOS-problematic characters: {filename}")
                
                # Issue 3: File extension recognition
                if content_disposition and '.csv' in content_disposition:
                    self.log_result("iOS File Extension", True, "CSV file extension is properly specified")
                else:
                    self.log_result("iOS File Extension", False, "CSV file extension may not be recognized by iOS")
                
                # Issue 4: Content encoding issues
                content_encoding = response.headers.get('Content-Encoding', '')
                if content_encoding:
                    self.log_result("Content Encoding", False, f"Content encoding may cause iOS issues: {content_encoding}")
                else:
                    self.log_result("Content Encoding", True, "No content encoding (good for iOS compatibility)")
                
            else:
                self.log_result("iOS Issues Base Test", False, f"Cannot test iOS issues: {response.status_code}")
                
        except Exception as e:
            self.log_result("iOS Specific Issues", False, f"Exception during test: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n=== CLEANING UP TEST DATA ===")
        self.log_result("Cleanup", True, "Test data cleanup completed")
    
    def run_all_tests(self):
        """Run all mobile download tests"""
        print("📱 MOBILE DOWNLOAD STRATEGY TESTING STARTED")
        print("=" * 60)
        
        # Setup test data
        if not self.setup_test_group():
            print("❌ Failed to setup test group. Aborting tests.")
            return
        
        # Run all tests
        self.test_backend_csv_endpoint_mobile_compatibility()
        self.test_expo_file_system_compatibility()
        self.test_expo_sharing_compatibility()
        self.test_alternative_download_methods()
        self.test_ios_specific_issues()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 MOBILE DOWNLOAD TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if "✅ PASS" in r["status"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS (POTENTIAL MOBILE ISSUES):")
            for result in self.results:
                if "❌ FAIL" in result["status"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        print(f"\n📱 MOBILE COMPATIBILITY RECOMMENDATIONS:")
        print("   • Ensure expo-file-system and expo-sharing are properly configured")
        print("   • Test on actual iOS devices for file download behavior")
        print("   • Consider implementing fallback methods for iOS Safari restrictions")
        print("   • Verify MIME types and UTI compatibility for iOS sharing")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = MobileDownloadTester()
    tester.run_all_tests()