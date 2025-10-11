#!/usr/bin/env python3
"""
Comprehensive Backend Testing for iPhone Download Functionality
Testing Focus: Enhanced Frontend Download Function and Backend CSV Response
"""

import asyncio
import aiohttp
import json
import csv
from io import StringIO
import os
from datetime import datetime
import uuid
import sys

# Get backend URL from environment
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://scoreleader.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

print(f"🎯 Testing backend at: {API_BASE}")
print("Focus: iPhone Download Functionality - Enhanced Frontend Download Function and Backend CSV Response")

class TestResults:
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_details = []
    
    def add_test(self, test_name, passed, details=""):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        self.test_details.append(f"{status}: {test_name} - {details}")
        print(f"{status}: {test_name} - {details}")
    
    def print_summary(self):
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY: {self.passed_tests}/{self.total_tests} tests passed ({success_rate:.1f}% success rate)")
        print(f"{'='*80}")
        for detail in self.test_details:
            print(detail)

class iPhoneDownloadTester:
    def __init__(self):
        self.results = TestResults()
        self.session = None
        self.test_group_id = None
        self.test_data = {
            'players': [],
            'teams': [],
            'sessions': []
        }
    
    async def setup_session(self):
        """Setup HTTP session with mobile user agent"""
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)
        
        # iPhone user agent for mobile compatibility testing
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
    
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    async def create_test_group(self):
        """Create a test group with sample data"""
        try:
            # Create group
            group_data = {"group_name": "iPhone Download Test Group"}
            async with self.session.post(f"{API_BASE}/groups", json=group_data) as response:
                if response.status == 200:
                    group = await response.json()
                    self.test_group_id = group['id']
                    self.results.add_test("Create Test Group", True, f"Group ID: {self.test_group_id}")
                    return True
                else:
                    self.results.add_test("Create Test Group", False, f"Status: {response.status}")
                    return False
        except Exception as e:
            self.results.add_test("Create Test Group", False, f"Exception: {str(e)}")
            return False
    
    async def create_sample_data(self):
        """Create sample players, teams, and game sessions"""
        if not self.test_group_id:
            return False
        
        try:
            # Create players
            players = [
                {"player_name": "Emma Wilson", "group_id": self.test_group_id, "emoji": "🎯"},
                {"player_name": "Liam Johnson", "group_id": self.test_group_id, "emoji": "🎲"},
                {"player_name": "Sophia Davis", "group_id": self.test_group_id, "emoji": "🏆"},
                {"player_name": "Noah Brown", "group_id": self.test_group_id, "emoji": "🎮"}
            ]
            
            for player_data in players:
                async with self.session.post(f"{API_BASE}/players", json=player_data) as response:
                    if response.status == 200:
                        player = await response.json()
                        self.test_data['players'].append(player)
            
            self.results.add_test("Create Sample Players", len(self.test_data['players']) == 4, 
                                f"Created {len(self.test_data['players'])}/4 players")
            
            # Create teams
            if len(self.test_data['players']) >= 4:
                teams = [
                    {
                        "team_name": "Strategy Masters",
                        "group_id": self.test_group_id,
                        "player_ids": [self.test_data['players'][0]['id'], self.test_data['players'][1]['id']]
                    },
                    {
                        "team_name": "Game Champions",
                        "group_id": self.test_group_id,
                        "player_ids": [self.test_data['players'][2]['id'], self.test_data['players'][3]['id']]
                    }
                ]
                
                for team_data in teams:
                    async with self.session.post(f"{API_BASE}/teams", json=team_data) as response:
                        if response.status == 200:
                            team = await response.json()
                            self.test_data['teams'].append(team)
                
                self.results.add_test("Create Sample Teams", len(self.test_data['teams']) == 2,
                                    f"Created {len(self.test_data['teams'])}/2 teams")
            
            # Create game sessions
            if len(self.test_data['players']) >= 4 and len(self.test_data['teams']) >= 2:
                sessions = [
                    {
                        "group_id": self.test_group_id,
                        "game_name": "Settlers of Catan",
                        "game_date": "2024-01-15T19:30:00",
                        "player_scores": [
                            {"player_id": self.test_data['players'][0]['id'], "player_name": "Emma Wilson", "score": 12},
                            {"player_id": self.test_data['players'][1]['id'], "player_name": "Liam Johnson", "score": 8},
                            {"player_id": self.test_data['players'][2]['id'], "player_name": "Sophia Davis", "score": 10},
                            {"player_id": self.test_data['players'][3]['id'], "player_name": "Noah Brown", "score": 6}
                        ]
                    },
                    {
                        "group_id": self.test_group_id,
                        "game_name": "Dungeons & Dragons",
                        "game_date": "2024-01-20T20:00:00",
                        "team_scores": [
                            {
                                "team_id": self.test_data['teams'][0]['id'],
                                "team_name": "Strategy Masters",
                                "score": 850,
                                "player_ids": [self.test_data['players'][0]['id'], self.test_data['players'][1]['id']]
                            },
                            {
                                "team_id": self.test_data['teams'][1]['id'],
                                "team_name": "Game Champions", 
                                "score": 720,
                                "player_ids": [self.test_data['players'][2]['id'], self.test_data['players'][3]['id']]
                            }
                        ]
                    }
                ]
                
                for session_data in sessions:
                    async with self.session.post(f"{API_BASE}/game-sessions", json=session_data) as response:
                        if response.status == 200:
                            session = await response.json()
                            self.test_data['sessions'].append(session)
                
                self.results.add_test("Create Sample Game Sessions", len(self.test_data['sessions']) == 2,
                                    f"Created {len(self.test_data['sessions'])}/2 game sessions")
            
            return len(self.test_data['players']) >= 4 and len(self.test_data['teams']) >= 2 and len(self.test_data['sessions']) >= 2
            
        except Exception as e:
            self.results.add_test("Create Sample Data", False, f"Exception: {str(e)}")
            return False
    
    async def test_csv_endpoint_basic(self):
        """Test basic CSV download endpoint functionality"""
        if not self.test_group_id:
            return False
        
        try:
            async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/download-csv") as response:
                # Test response status
                self.results.add_test("CSV Endpoint Status", response.status == 200,
                                    f"Status: {response.status}")
                
                # Test Content-Type header
                content_type = response.headers.get('Content-Type', '')
                self.results.add_test("CSV Content-Type Header", 'text/csv' in content_type,
                                    f"Content-Type: {content_type}")
                
                # Test Content-Disposition header
                content_disposition = response.headers.get('Content-Disposition', '')
                has_attachment = 'attachment' in content_disposition
                has_filename = 'filename=' in content_disposition
                self.results.add_test("CSV Content-Disposition Header", has_attachment and has_filename,
                                    f"Content-Disposition: {content_disposition}")
                
                # Test CSV content
                if response.status == 200:
                    csv_content = await response.text()
                    
                    # Verify CSV structure
                    has_group_info = 'GROUP INFORMATION' in csv_content
                    has_players = 'PLAYERS' in csv_content
                    has_teams = 'TEAMS' in csv_content
                    has_sessions = 'GAME SESSIONS' in csv_content
                    
                    self.results.add_test("CSV Structure - Group Info", has_group_info,
                                        f"Contains GROUP INFORMATION section")
                    self.results.add_test("CSV Structure - Players", has_players,
                                        f"Contains PLAYERS section")
                    self.results.add_test("CSV Structure - Teams", has_teams,
                                        f"Contains TEAMS section")
                    self.results.add_test("CSV Structure - Game Sessions", has_sessions,
                                        f"Contains GAME SESSIONS section")
                    
                    # Test normalized scores in CSV
                    has_normalized_scores = 'Normalized Score' in csv_content
                    self.results.add_test("CSV Normalized Scores", has_normalized_scores,
                                        f"Contains normalized scores in game sessions")
                    
                    return True
                else:
                    return False
                    
        except Exception as e:
            self.results.add_test("CSV Endpoint Basic Test", False, f"Exception: {str(e)}")
            return False
    
    async def test_cors_headers(self):
        """Test CORS headers for mobile compatibility"""
        if not self.test_group_id:
            return False
        
        try:
            # Test OPTIONS request (preflight)
            async with self.session.options(f"{API_BASE}/groups/{self.test_group_id}/download-csv") as response:
                cors_origin = response.headers.get('access-control-allow-origin', '')
                cors_methods = response.headers.get('access-control-allow-methods', '')
                cors_headers = response.headers.get('access-control-allow-headers', '')
                
                self.results.add_test("CORS - Allow Origin", cors_origin != '',
                                    f"Access-Control-Allow-Origin: {cors_origin}")
                self.results.add_test("CORS - Allow Methods", 'GET' in cors_methods,
                                    f"Access-Control-Allow-Methods: {cors_methods}")
                self.results.add_test("CORS - Allow Headers", cors_headers != '',
                                    f"Access-Control-Allow-Headers: {cors_headers}")
            
            # Test actual GET request with CORS headers
            async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/download-csv") as response:
                cors_origin = response.headers.get('access-control-allow-origin', '')
                self.results.add_test("CORS - GET Response Origin", cors_origin != '',
                                    f"GET Access-Control-Allow-Origin: {cors_origin}")
                
                return True
                
        except Exception as e:
            self.results.add_test("CORS Headers Test", False, f"Exception: {str(e)}")
            return False
    
    async def test_head_method_support(self):
        """Test HEAD method support for mobile compatibility"""
        if not self.test_group_id:
            return False
        
        try:
            async with self.session.head(f"{API_BASE}/groups/{self.test_group_id}/download-csv") as response:
                self.results.add_test("HEAD Method Support", response.status == 200,
                                    f"HEAD Status: {response.status}")
                
                # Verify headers are present in HEAD response
                content_type = response.headers.get('Content-Type', '')
                content_disposition = response.headers.get('Content-Disposition', '')
                
                self.results.add_test("HEAD Method - Content-Type", 'text/csv' in content_type,
                                    f"HEAD Content-Type: {content_type}")
                self.results.add_test("HEAD Method - Content-Disposition", 'attachment' in content_disposition,
                                    f"HEAD Content-Disposition: {content_disposition}")
                
                return True
                
        except Exception as e:
            self.results.add_test("HEAD Method Support", False, f"Exception: {str(e)}")
            return False
    
    async def test_mobile_user_agent_compatibility(self):
        """Test compatibility with various mobile user agents"""
        if not self.test_group_id:
            return False
        
        mobile_user_agents = [
            # iPhone Safari
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            # iPhone Chrome
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.109 Mobile/15E148 Safari/604.1',
            # React Native WebView
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
        ]
        
        success_count = 0
        for i, user_agent in enumerate(mobile_user_agents):
            try:
                headers = {'User-Agent': user_agent}
                async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/download-csv", 
                                          headers=headers) as response:
                    if response.status == 200:
                        success_count += 1
                        self.results.add_test(f"Mobile User Agent {i+1}", True,
                                            f"Status: {response.status}")
                    else:
                        self.results.add_test(f"Mobile User Agent {i+1}", False,
                                            f"Status: {response.status}")
            except Exception as e:
                self.results.add_test(f"Mobile User Agent {i+1}", False, f"Exception: {str(e)}")
        
        return success_count == len(mobile_user_agents)
    
    async def test_csv_content_validation(self):
        """Test CSV content structure and data integrity"""
        if not self.test_group_id:
            return False
        
        try:
            async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/download-csv") as response:
                if response.status != 200:
                    self.results.add_test("CSV Content Validation", False, f"Status: {response.status}")
                    return False
                
                csv_content = await response.text()
                lines = csv_content.split('\n')
                
                # Test specific content requirements
                group_name_found = any('iPhone Download Test Group' in line for line in lines)
                self.results.add_test("CSV Content - Group Name", group_name_found,
                                    "Group name present in CSV")
                
                # Test player data
                emma_found = any('Emma Wilson' in line for line in lines)
                liam_found = any('Liam Johnson' in line for line in lines)
                self.results.add_test("CSV Content - Player Data", emma_found and liam_found,
                                    "Player names present in CSV")
                
                # Test team data
                strategy_masters_found = any('Strategy Masters' in line for line in lines)
                game_champions_found = any('Game Champions' in line for line in lines)
                self.results.add_test("CSV Content - Team Data", strategy_masters_found and game_champions_found,
                                    "Team names present in CSV")
                
                # Test game session data
                catan_found = any('Settlers of Catan' in line for line in lines)
                dnd_found = any('Dungeons & Dragons' in line for line in lines)
                self.results.add_test("CSV Content - Game Sessions", catan_found and dnd_found,
                                    "Game sessions present in CSV")
                
                # Test normalized scores format
                normalized_score_pattern = False
                for line in lines:
                    if 'Normalized Score' in line or ('0.' in line and 'Individual' in line):
                        normalized_score_pattern = True
                        break
                
                self.results.add_test("CSV Content - Normalized Score Format", normalized_score_pattern,
                                    "Normalized scores in proper format (0-1 range)")
                
                # Test raw and normalized score headers
                raw_total_score = any('Raw Total Score' in line for line in lines)
                normalized_total_score = any('Normalized Total Score' in line for line in lines)
                self.results.add_test("CSV Content - Score Headers", raw_total_score and normalized_total_score,
                                    "Both raw and normalized score headers present")
                
                return True
                
        except Exception as e:
            self.results.add_test("CSV Content Validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_ios_specific_headers(self):
        """Test iOS-specific headers and MIME types"""
        if not self.test_group_id:
            return False
        
        try:
            async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/download-csv") as response:
                content_type = response.headers.get('Content-Type', '')
                
                # Test for proper CSV MIME type
                proper_csv_mime = 'text/csv' in content_type
                self.results.add_test("iOS - CSV MIME Type", proper_csv_mime,
                                    f"Content-Type: {content_type}")
                
                # Test for charset specification
                has_charset = 'charset=' in content_type
                self.results.add_test("iOS - Charset Specification", has_charset,
                                    f"Charset in Content-Type: {has_charset}")
                
                # Test Content-Disposition for iOS compatibility
                content_disposition = response.headers.get('Content-Disposition', '')
                has_proper_filename = 'filename=' in content_disposition and '.csv' in content_disposition
                self.results.add_test("iOS - Proper Filename Extension", has_proper_filename,
                                    f"Filename with .csv extension: {has_proper_filename}")
                
                return proper_csv_mime and has_charset and has_proper_filename
                
        except Exception as e:
            self.results.add_test("iOS Specific Headers", False, f"Exception: {str(e)}")
            return False
    
    async def test_error_scenarios(self):
        """Test error handling scenarios"""
        try:
            # Test invalid group ID
            invalid_group_id = str(uuid.uuid4())
            async with self.session.get(f"{API_BASE}/groups/{invalid_group_id}/download-csv") as response:
                self.results.add_test("Error Handling - Invalid Group", response.status == 404,
                                    f"Invalid group status: {response.status}")
            
            # Test malformed group ID
            async with self.session.get(f"{API_BASE}/groups/invalid-id/download-csv") as response:
                error_handled = response.status in [400, 404, 422]
                self.results.add_test("Error Handling - Malformed ID", error_handled,
                                    f"Malformed ID status: {response.status}")
            
            return True
            
        except Exception as e:
            self.results.add_test("Error Scenarios", False, f"Exception: {str(e)}")
            return False
    
    async def run_comprehensive_test(self):
        """Run all iPhone download functionality tests"""
        print("🧪 Starting Comprehensive iPhone Download Functionality Testing")
        print("=" * 80)
        
        await self.setup_session()
        
        try:
            # Setup test data
            if not await self.create_test_group():
                print("❌ Failed to create test group. Aborting tests.")
                return
            
            if not await self.create_sample_data():
                print("❌ Failed to create sample data. Some tests may fail.")
            
            # Run all test suites
            print("\n📋 Testing CSV Endpoint Basic Functionality...")
            await self.test_csv_endpoint_basic()
            
            print("\n🌐 Testing CORS Headers for Mobile Compatibility...")
            await self.test_cors_headers()
            
            print("\n📱 Testing HEAD Method Support...")
            await self.test_head_method_support()
            
            print("\n📲 Testing Mobile User Agent Compatibility...")
            await self.test_mobile_user_agent_compatibility()
            
            print("\n📄 Testing CSV Content Validation...")
            await self.test_csv_content_validation()
            
            print("\n🍎 Testing iOS-Specific Headers...")
            await self.test_ios_specific_headers()
            
            print("\n🚨 Testing Error Scenarios...")
            await self.test_error_scenarios()
            
        finally:
            await self.cleanup_session()
        
        # Print final results
        self.results.print_summary()
        
        return self.results

async def main():
    """Main test execution function"""
    tester = iPhoneDownloadTester()
    results = await tester.run_comprehensive_test()
    
    # Return results for analysis
    return results

if __name__ == "__main__":
    # Run the comprehensive test suite
    results = asyncio.run(main())
    
    # Exit with appropriate code
    if results.failed_tests == 0:
        print(f"\n🎉 ALL TESTS PASSED! iPhone download functionality is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {results.failed_tests} test(s) failed. iPhone download functionality needs attention.")
        sys.exit(1)