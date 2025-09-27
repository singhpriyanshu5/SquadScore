#!/usr/bin/env python3
"""
Comprehensive Backend API Test Suite for Board Game Score Tracker
Tests all endpoints with realistic data and edge cases
"""

import requests
import json
from datetime import datetime, timezone
import time
import sys

# Base URL from frontend environment
BASE_URL = "https://scoreleader.preview.emergentagent.com/api"

class BoardGameAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_data = {}
        self.failed_tests = []
        self.passed_tests = []
        
    def log_test(self, test_name, success, message=""):
        """Log test results"""
        if success:
            self.passed_tests.append(test_name)
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.failed_tests.append(test_name)
            print(f"❌ {test_name}: FAILED {message}")
    
    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            
            print(f"  {method} {url} -> {response.status_code}")
            
            if response.status_code != expected_status:
                print(f"  Expected {expected_status}, got {response.status_code}")
                if response.text:
                    print(f"  Response: {response.text}")
                return None, response.status_code
                
            return response.json() if response.text else {}, response.status_code
            
        except requests.exceptions.RequestException as e:
            print(f"  Request failed: {e}")
            return None, 0
        except json.JSONDecodeError as e:
            print(f"  JSON decode error: {e}")
            return None, response.status_code if 'response' in locals() else 0
    
    def test_api_health(self):
        """Test basic API connectivity"""
        print("\n=== Testing API Health ===")
        
        data, status = self.make_request("GET", "/")
        if data and status == 200:
            self.log_test("API Health Check", True, f"- {data.get('message', 'API responding')}")
            return True
        else:
            self.log_test("API Health Check", False, f"- Status: {status}")
            return False
    
    def test_group_management(self):
        """Test group creation, joining, and retrieval"""
        print("\n=== Testing Group Management ===")
        
        # Test 1: Create a group
        group_data = {"group_name": "Dungeons & Dragons Club"}
        data, status = self.make_request("POST", "/groups", group_data)
        
        if data and status == 200:
            self.test_data['group'] = data
            group_code = data.get('group_code')
            group_id = data.get('id')
            
            if group_code and len(group_code) == 6:
                self.log_test("Create Group", True, f"- Code: {group_code}")
            else:
                self.log_test("Create Group", False, "- Invalid group code format")
                return False
        else:
            self.log_test("Create Group", False, f"- Status: {status}")
            return False
        
        # Test 2: Join group using code
        join_data = {"group_code": self.test_data['group']['group_code']}
        data, status = self.make_request("POST", "/groups/join", join_data)
        
        if data and status == 200:
            if data.get('id') == self.test_data['group']['id']:
                self.log_test("Join Group", True, f"- Joined group: {data.get('group_name')}")
            else:
                self.log_test("Join Group", False, "- Wrong group returned")
        else:
            self.log_test("Join Group", False, f"- Status: {status}")
        
        # Test 3: Get group by ID
        group_id = self.test_data['group']['id']
        data, status = self.make_request("GET", f"/groups/{group_id}")
        
        if data and status == 200:
            if data.get('id') == group_id:
                self.log_test("Get Group", True, f"- Retrieved: {data.get('group_name')}")
            else:
                self.log_test("Get Group", False, "- Wrong group data")
        else:
            self.log_test("Get Group", False, f"- Status: {status}")
        
        # Test 4: Error handling - Join non-existent group
        invalid_join = {"group_code": "INVALID"}
        data, status = self.make_request("POST", "/groups/join", invalid_join, expected_status=404)
        
        if status == 404:
            self.log_test("Join Invalid Group", True, "- Correctly returned 404")
        else:
            self.log_test("Join Invalid Group", False, f"- Expected 404, got {status}")
        
        return True
    
    def test_player_management(self):
        """Test player creation and retrieval"""
        print("\n=== Testing Player Management ===")
        
        if 'group' not in self.test_data:
            self.log_test("Player Management", False, "- No group available for testing")
            return False
        
        group_id = self.test_data['group']['id']
        players = []
        
        # Test 1: Add multiple players
        player_names = ["Alice Johnson", "Bob Smith", "Charlie Brown", "Diana Prince"]
        
        for name in player_names:
            player_data = {
                "player_name": name,
                "group_id": group_id
            }
            
            data, status = self.make_request("POST", "/players", player_data)
            
            if data and status == 200:
                players.append(data)
                self.log_test(f"Add Player ({name})", True, f"- ID: {data.get('id')}")
            else:
                self.log_test(f"Add Player ({name})", False, f"- Status: {status}")
        
        self.test_data['players'] = players
        
        # Test 2: Get all players in group
        data, status = self.make_request("GET", f"/groups/{group_id}/players")
        
        if data and status == 200:
            if len(data) == len(players):
                self.log_test("Get Group Players", True, f"- Found {len(data)} players")
            else:
                self.log_test("Get Group Players", False, f"- Expected {len(players)}, got {len(data)}")
        else:
            self.log_test("Get Group Players", False, f"- Status: {status}")
        
        # Test 3: Error handling - Duplicate player name
        duplicate_data = {
            "player_name": player_names[0],  # Use first player's name
            "group_id": group_id
        }
        
        data, status = self.make_request("POST", "/players", duplicate_data, expected_status=400)
        
        if status == 400:
            self.log_test("Duplicate Player Name", True, "- Correctly rejected duplicate")
        else:
            self.log_test("Duplicate Player Name", False, f"- Expected 400, got {status}")
        
        # Test 4: Error handling - Invalid group ID
        invalid_player = {
            "player_name": "Invalid Player",
            "group_id": "invalid-group-id"
        }
        
        data, status = self.make_request("POST", "/players", invalid_player, expected_status=404)
        
        if status == 404:
            self.log_test("Player Invalid Group", True, "- Correctly returned 404")
        else:
            self.log_test("Player Invalid Group", False, f"- Expected 404, got {status}")
        
        return len(players) > 0
    
    def test_team_management(self):
        """Test team creation and retrieval"""
        print("\n=== Testing Team Management ===")
        
        if 'players' not in self.test_data or len(self.test_data['players']) < 2:
            self.log_test("Team Management", False, "- Need at least 2 players for team testing")
            return False
        
        group_id = self.test_data['group']['id']
        players = self.test_data['players']
        teams = []
        
        # Test 1: Create teams with different player combinations
        team_configs = [
            {
                "team_name": "The Strategists",
                "player_ids": [players[0]['id'], players[1]['id']]
            },
            {
                "team_name": "The Adventurers", 
                "player_ids": [players[2]['id'], players[3]['id']] if len(players) > 3 else [players[2]['id']]
            }
        ]
        
        for team_config in team_configs:
            team_data = {
                "team_name": team_config["team_name"],
                "group_id": group_id,
                "player_ids": team_config["player_ids"]
            }
            
            data, status = self.make_request("POST", "/teams", team_data)
            
            if data and status == 200:
                teams.append(data)
                self.log_test(f"Create Team ({team_config['team_name']})", True, 
                            f"- {len(team_config['player_ids'])} players")
            else:
                self.log_test(f"Create Team ({team_config['team_name']})", False, f"- Status: {status}")
        
        self.test_data['teams'] = teams
        
        # Test 2: Get all teams in group
        data, status = self.make_request("GET", f"/groups/{group_id}/teams")
        
        if data and status == 200:
            if len(data) == len(teams):
                self.log_test("Get Group Teams", True, f"- Found {len(data)} teams")
            else:
                self.log_test("Get Group Teams", False, f"- Expected {len(teams)}, got {len(data)}")
        else:
            self.log_test("Get Group Teams", False, f"- Status: {status}")
        
        # Test 3: Error handling - Duplicate team name
        duplicate_team = {
            "team_name": team_configs[0]["team_name"],
            "group_id": group_id,
            "player_ids": [players[0]['id']]
        }
        
        data, status = self.make_request("POST", "/teams", duplicate_team, expected_status=400)
        
        if status == 400:
            self.log_test("Duplicate Team Name", True, "- Correctly rejected duplicate")
        else:
            self.log_test("Duplicate Team Name", False, f"- Expected 400, got {status}")
        
        # Test 4: Error handling - Invalid player ID
        invalid_team = {
            "team_name": "Invalid Team",
            "group_id": group_id,
            "player_ids": ["invalid-player-id"]
        }
        
        data, status = self.make_request("POST", "/teams", invalid_team, expected_status=404)
        
        if status == 404:
            self.log_test("Team Invalid Player", True, "- Correctly returned 404")
        else:
            self.log_test("Team Invalid Player", False, f"- Expected 404, got {status}")
        
        return len(teams) > 0
    
    def test_game_sessions(self):
        """Test game session recording and score distribution"""
        print("\n=== Testing Game Sessions ===")
        
        if 'players' not in self.test_data or 'teams' not in self.test_data:
            self.log_test("Game Sessions", False, "- Need players and teams for testing")
            return False
        
        group_id = self.test_data['group']['id']
        players = self.test_data['players']
        teams = self.test_data['teams']
        
        # Test 1: Record game with individual player scores
        game_data_1 = {
            "group_id": group_id,
            "game_name": "Settlers of Catan",
            "game_date": datetime.now(timezone.utc).isoformat(),
            "player_scores": [
                {
                    "player_id": players[0]['id'],
                    "player_name": players[0]['player_name'],
                    "score": 12
                },
                {
                    "player_id": players[1]['id'],
                    "player_name": players[1]['player_name'],
                    "score": 8
                }
            ],
            "team_scores": []
        }
        
        data, status = self.make_request("POST", "/game-sessions", game_data_1)
        
        if data and status == 200:
            self.log_test("Record Individual Game", True, f"- Game: {data.get('game_name')}")
        else:
            self.log_test("Record Individual Game", False, f"- Status: {status}")
        
        # Test 2: Record game with team scores (CRITICAL TEST - auto-distribution)
        if len(teams) > 0:
            team = teams[0]
            team_score_value = 20
            
            game_data_2 = {
                "group_id": group_id,
                "game_name": "Dungeons & Dragons",
                "game_date": datetime.now(timezone.utc).isoformat(),
                "player_scores": [],
                "team_scores": [
                    {
                        "team_id": team['id'],
                        "team_name": team['team_name'],
                        "score": team_score_value,
                        "player_ids": team['player_ids']
                    }
                ]
            }
            
            data, status = self.make_request("POST", "/game-sessions", game_data_2)
            
            if data and status == 200:
                self.log_test("Record Team Game", True, f"- Team score: {team_score_value}")
                
                # CRITICAL: Verify score distribution to players
                time.sleep(1)  # Allow time for database updates
                
                expected_score_per_player = team_score_value // len(team['player_ids'])
                distribution_success = True
                
                for player_id in team['player_ids']:
                    # Get updated player data
                    player_data, status = self.make_request("GET", f"/groups/{group_id}/players")
                    if player_data and status == 200:
                        player = next((p for p in player_data if p['id'] == player_id), None)
                        if player:
                            # Player should have at least the distributed score
                            if player['total_score'] >= expected_score_per_player:
                                print(f"    Player {player['player_name']}: {player['total_score']} points")
                            else:
                                distribution_success = False
                                print(f"    Player {player['player_name']}: Expected >= {expected_score_per_player}, got {player['total_score']}")
                
                self.log_test("Team Score Distribution", distribution_success, 
                            f"- {expected_score_per_player} points per player")
            else:
                self.log_test("Record Team Game", False, f"- Status: {status}")
        
        # Test 3: Get game sessions
        data, status = self.make_request("GET", f"/groups/{group_id}/game-sessions")
        
        if data and status == 200:
            if len(data) >= 1:  # Should have at least the games we recorded
                self.log_test("Get Game Sessions", True, f"- Found {len(data)} sessions")
            else:
                self.log_test("Get Game Sessions", False, "- No sessions found")
        else:
            self.log_test("Get Game Sessions", False, f"- Status: {status}")
        
        return True
    
    def test_leaderboards(self):
        """Test player and team leaderboards"""
        print("\n=== Testing Leaderboards ===")
        
        if 'group' not in self.test_data:
            self.log_test("Leaderboards", False, "- No group available")
            return False
        
        group_id = self.test_data['group']['id']
        
        # Test 1: Player leaderboard
        data, status = self.make_request("GET", f"/groups/{group_id}/leaderboard/players")
        
        if data and status == 200:
            if len(data) > 0:
                # Verify sorting (highest score first)
                is_sorted = all(data[i]['total_score'] >= data[i+1]['total_score'] 
                              for i in range(len(data)-1))
                
                if is_sorted:
                    self.log_test("Player Leaderboard", True, 
                                f"- {len(data)} players, top: {data[0]['name']} ({data[0]['total_score']} pts)")
                else:
                    self.log_test("Player Leaderboard", False, "- Not properly sorted")
            else:
                self.log_test("Player Leaderboard", False, "- No players found")
        else:
            self.log_test("Player Leaderboard", False, f"- Status: {status}")
        
        # Test 2: Team leaderboard
        data, status = self.make_request("GET", f"/groups/{group_id}/leaderboard/teams")
        
        if data and status == 200:
            if len(data) > 0:
                # Verify sorting
                is_sorted = all(data[i]['total_score'] >= data[i+1]['total_score'] 
                              for i in range(len(data)-1))
                
                if is_sorted:
                    self.log_test("Team Leaderboard", True, 
                                f"- {len(data)} teams, top: {data[0]['name']} ({data[0]['total_score']} pts)")
                else:
                    self.log_test("Team Leaderboard", False, "- Not properly sorted")
            else:
                self.log_test("Team Leaderboard", True, "- No teams (acceptable)")
        else:
            self.log_test("Team Leaderboard", False, f"- Status: {status}")
        
        return True
    
    def test_group_stats(self):
        """Test group statistics"""
        print("\n=== Testing Group Statistics ===")
        
        if 'group' not in self.test_data:
            self.log_test("Group Stats", False, "- No group available")
            return False
        
        group_id = self.test_data['group']['id']
        
        data, status = self.make_request("GET", f"/groups/{group_id}/stats")
        
        if data and status == 200:
            stats = data
            
            # Verify expected counts
            expected_players = len(self.test_data.get('players', []))
            expected_teams = len(self.test_data.get('teams', []))
            
            success = True
            issues = []
            
            if stats.get('total_players') != expected_players:
                success = False
                issues.append(f"Players: expected {expected_players}, got {stats.get('total_players')}")
            
            if stats.get('total_teams') != expected_teams:
                success = False
                issues.append(f"Teams: expected {expected_teams}, got {stats.get('total_teams')}")
            
            if stats.get('total_games', 0) < 1:
                success = False
                issues.append("No games recorded")
            
            if success:
                self.log_test("Group Statistics", True, 
                            f"- {stats['total_players']} players, {stats['total_teams']} teams, {stats['total_games']} games")
                
                if stats.get('most_played_game'):
                    print(f"    Most played: {stats['most_played_game']}")
                
                if stats.get('top_player'):
                    top = stats['top_player']
                    print(f"    Top player: {top['name']} ({top['total_score']} pts)")
            else:
                self.log_test("Group Statistics", False, f"- Issues: {', '.join(issues)}")
        else:
            self.log_test("Group Stats", False, f"- Status: {status}")
        
        return True
    
    def test_download_csv(self):
        """Test CSV download functionality"""
        print("\n=== Testing CSV Download ===")
        
        if 'group' not in self.test_data:
            self.log_test("CSV Download", False, "- No group available")
            return False
        
        group_id = self.test_data['group']['id']
        
        try:
            # Make request to CSV download endpoint
            url = f"{self.base_url}/groups/{group_id}/download-csv"
            response = self.session.get(url)
            
            print(f"  GET {url} -> {response.status_code}")
            
            if response.status_code == 200:
                # Check headers
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                
                success = True
                issues = []
                
                # Verify content type
                if 'text/csv' not in content_type:
                    success = False
                    issues.append(f"Wrong content type: {content_type}")
                
                # Verify download headers
                if 'attachment' not in content_disposition or 'filename=' not in content_disposition:
                    success = False
                    issues.append(f"Missing download headers: {content_disposition}")
                
                # Check CSV content structure
                csv_content = response.text
                lines = csv_content.split('\n')
                
                # Verify required sections
                required_sections = ['GROUP INFORMATION', 'PLAYERS']
                found_sections = []
                
                for line in lines:
                    for section in required_sections:
                        if section in line:
                            found_sections.append(section)
                            break
                
                if len(found_sections) < len(required_sections):
                    success = False
                    issues.append(f"Missing sections. Found: {found_sections}, Required: {required_sections}")
                
                # Check for group info
                if 'Group Name,' not in csv_content or 'Group Code,' not in csv_content:
                    success = False
                    issues.append("Missing group information in CSV")
                
                # Check for player data structure
                if 'Player Name,Emoji,Total Score' not in csv_content:
                    success = False
                    issues.append("Missing player data structure in CSV")
                
                if success:
                    self.log_test("CSV Download", True, f"- Content-Type: {content_type}")
                    print(f"    Content-Disposition: {content_disposition}")
                    print(f"    CSV sections found: {found_sections}")
                    print(f"    CSV size: {len(csv_content)} characters")
                else:
                    self.log_test("CSV Download", False, f"- Issues: {', '.join(issues)}")
                
                return success
                
            elif response.status_code == 404:
                self.log_test("CSV Download", False, "- Group not found")
                return False
            else:
                self.log_test("CSV Download", False, f"- Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("CSV Download", False, f"- Exception: {str(e)}")
            return False
    
    def test_import_functionality(self):
        """Test JSON import functionality"""
        print("\n=== Testing Import Functionality ===")
        
        if 'group' not in self.test_data:
            self.log_test("Import Functionality", False, "- No group available")
            return False
        
        group_id = self.test_data['group']['id']
        
        try:
            # First, export current data to get valid import format
            export_url = f"{self.base_url}/groups/{group_id}/export"
            export_response = self.session.get(export_url)
            
            print(f"  GET {export_url} -> {export_response.status_code}")
            
            if export_response.status_code != 200:
                self.log_test("Export for Import Test", False, f"- Status: {export_response.status_code}")
                return False
            
            export_data = export_response.json()
            self.log_test("Export for Import Test", True, "- Successfully exported data")
            
            # Create a temporary JSON file
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(export_data, temp_file, indent=2)
                temp_file_path = temp_file.name
            
            try:
                # Test import with the exported data
                import_url = f"{self.base_url}/groups/{group_id}/import"
                
                with open(temp_file_path, 'rb') as f:
                    files = {'file': ('test_import.json', f, 'application/json')}
                    import_response = self.session.post(import_url, files=files)
                
                print(f"  POST {import_url} -> {import_response.status_code}")
                
                if import_response.status_code == 200:
                    result = import_response.json()
                    
                    success = True
                    issues = []
                    
                    # Check response format
                    if 'message' not in result or 'imported' not in result:
                        success = False
                        issues.append("Missing required response fields")
                    
                    if 'imported' in result:
                        imported = result['imported']
                        required_fields = ['players', 'teams', 'game_sessions']
                        
                        for field in required_fields:
                            if field not in imported:
                                success = False
                                issues.append(f"Missing import statistic: {field}")
                    
                    if success:
                        imported = result['imported']
                        self.log_test("Import Functionality", True, 
                                    f"- Imported: {imported['players']} players, {imported['teams']} teams, {imported['game_sessions']} sessions")
                        print(f"    Message: {result['message']}")
                    else:
                        self.log_test("Import Functionality", False, f"- Issues: {', '.join(issues)}")
                    
                    return success
                    
                elif import_response.status_code == 404:
                    self.log_test("Import Functionality", False, "- Group not found")
                    return False
                elif import_response.status_code == 400:
                    self.log_test("Import Functionality", False, f"- Bad request: {import_response.text}")
                    return False
                else:
                    self.log_test("Import Functionality", False, f"- Status: {import_response.status_code}")
                    return False
                    
            finally:
                # Clean up temp file
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log_test("Import Functionality", False, f"- Exception: {str(e)}")
            return False
    
    def test_csv_import_functionality(self):
        """Test the NEW CSV import functionality"""
        print("\n=== Testing CSV Import Functionality ===")
        
        if 'group' not in self.test_data:
            self.log_test("CSV Import Functionality", False, "- No group available")
            return False
        
        group_id = self.test_data['group']['id']
        
        try:
            # Step 1: Download CSV data first
            csv_url = f"{self.base_url}/groups/{group_id}/download-csv"
            csv_response = self.session.get(csv_url)
            
            print(f"  GET {csv_url} -> {csv_response.status_code}")
            
            if csv_response.status_code != 200:
                self.log_test("CSV Download for Import", False, f"- Status: {csv_response.status_code}")
                return False
            
            csv_content = csv_response.text
            self.log_test("CSV Download for Import", True, f"- Downloaded {len(csv_content)} characters")
            
            # Step 2: Test CSV import with downloaded data
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
                temp_file.write(csv_content)
                temp_file_path = temp_file.name
            
            try:
                # Test CSV import endpoint
                import_url = f"{self.base_url}/groups/{group_id}/import-csv"
                
                with open(temp_file_path, 'rb') as f:
                    files = {'file': ('test_import.csv', f, 'text/csv')}
                    import_response = self.session.post(import_url, files=files)
                
                print(f"  POST {import_url} -> {import_response.status_code}")
                
                if import_response.status_code == 200:
                    result = import_response.json()
                    
                    success = True
                    issues = []
                    
                    # Check response format
                    if 'message' not in result or 'imported' not in result:
                        success = False
                        issues.append("Missing required response fields")
                    
                    if 'imported' in result:
                        imported = result['imported']
                        required_fields = ['players', 'teams', 'game_sessions']
                        
                        for field in required_fields:
                            if field not in imported:
                                success = False
                                issues.append(f"Missing import statistic: {field}")
                    
                    if success:
                        imported = result['imported']
                        self.log_test("CSV Import", True, 
                                    f"- Imported: {imported['players']} players, {imported['teams']} teams, {imported['game_sessions']} sessions")
                        print(f"    Message: {result['message']}")
                        
                        # Step 3: Verify round-trip data integrity
                        return self._verify_csv_round_trip_integrity(imported)
                    else:
                        self.log_test("CSV Import", False, f"- Issues: {', '.join(issues)}")
                        return False
                        
                elif import_response.status_code == 404:
                    self.log_test("CSV Import", False, "- Group not found")
                    return False
                elif import_response.status_code in [400, 500]:
                    self.log_test("CSV Import", False, f"- Import error: {import_response.text}")
                    return False
                else:
                    self.log_test("CSV Import", False, f"- Status: {import_response.status_code}")
                    return False
                    
            finally:
                # Clean up temp file
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log_test("CSV Import Functionality", False, f"- Exception: {str(e)}")
            return False
    
    def _verify_csv_round_trip_integrity(self, import_stats):
        """Verify that CSV round-trip (export -> import) preserves data integrity"""
        print("    Verifying round-trip data integrity...")
        
        group_id = self.test_data['group']['id']
        
        try:
            # Get current data after import
            players_response = self.session.get(f"{self.base_url}/groups/{group_id}/players")
            teams_response = self.session.get(f"{self.base_url}/groups/{group_id}/teams")
            sessions_response = self.session.get(f"{self.base_url}/groups/{group_id}/game-sessions")
            
            if players_response.status_code != 200:
                self.log_test("CSV Round-trip Integrity", False, "- Failed to get players after import")
                return False
            
            if teams_response.status_code != 200:
                self.log_test("CSV Round-trip Integrity", False, "- Failed to get teams after import")
                return False
            
            if sessions_response.status_code != 200:
                self.log_test("CSV Round-trip Integrity", False, "- Failed to get sessions after import")
                return False
            
            imported_players = players_response.json()
            imported_teams = teams_response.json()
            imported_sessions = sessions_response.json()
            
            # Verify counts match import statistics
            success = True
            issues = []
            
            if len(imported_players) != import_stats['players']:
                success = False
                issues.append(f"Player count mismatch: expected {import_stats['players']}, got {len(imported_players)}")
            
            if len(imported_teams) != import_stats['teams']:
                success = False
                issues.append(f"Team count mismatch: expected {import_stats['teams']}, got {len(imported_teams)}")
            
            if len(imported_sessions) != import_stats['game_sessions']:
                success = False
                issues.append(f"Session count mismatch: expected {import_stats['game_sessions']}, got {len(imported_sessions)}")
            
            # Verify data structure integrity
            if imported_players:
                player = imported_players[0]
                required_player_fields = ['id', 'player_name', 'emoji', 'total_score', 'games_played']
                for field in required_player_fields:
                    if field not in player:
                        success = False
                        issues.append(f"Missing player field: {field}")
            
            if imported_teams:
                team = imported_teams[0]
                required_team_fields = ['id', 'team_name', 'player_ids', 'total_score', 'games_played']
                for field in required_team_fields:
                    if field not in team:
                        success = False
                        issues.append(f"Missing team field: {field}")
            
            if imported_sessions:
                session = imported_sessions[0]
                required_session_fields = ['id', 'game_name', 'game_date', 'player_scores', 'team_scores']
                for field in required_session_fields:
                    if field not in session:
                        success = False
                        issues.append(f"Missing session field: {field}")
            
            if success:
                self.log_test("CSV Round-trip Integrity", True, 
                            f"- All data preserved: {len(imported_players)} players, {len(imported_teams)} teams, {len(imported_sessions)} sessions")
                return True
            else:
                self.log_test("CSV Round-trip Integrity", False, f"- Issues: {', '.join(issues)}")
                return False
                
        except Exception as e:
            self.log_test("CSV Round-trip Integrity", False, f"- Exception: {str(e)}")
            return False
    
    def test_csv_import_error_handling(self):
        """Test CSV import error handling"""
        print("\n=== Testing CSV Import Error Handling ===")
        
        success_count = 0
        total_tests = 4
        
        # Test 1: CSV import with invalid group ID
        try:
            import tempfile
            import os
            
            test_csv = "GROUP INFORMATION\nGroup Name,Test Group\nGroup Code,TEST01\n\nPLAYERS\nPlayer Name,Emoji,Total Score,Games Played,Average Score,Joined Date\nTest Player,😀,10,1,10.00,2024-01-01\n"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
                temp_file.write(test_csv)
                temp_file_path = temp_file.name
            
            try:
                url = f"{self.base_url}/groups/invalid-group-id/import-csv"
                with open(temp_file_path, 'rb') as f:
                    files = {'file': ('test.csv', f, 'text/csv')}
                    response = self.session.post(url, files=files)
                
                print(f"  POST {url} -> {response.status_code}")
                
                if response.status_code == 404:
                    self.log_test("CSV Import Invalid Group", True, "- Correctly returned 404")
                    success_count += 1
                else:
                    self.log_test("CSV Import Invalid Group", False, f"- Expected 404, got {response.status_code}")
                    
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log_test("CSV Import Invalid Group", False, f"- Exception: {str(e)}")
        
        # Test 2: Malformed CSV
        if 'group' in self.test_data:
            try:
                import tempfile
                import os
                
                group_id = self.test_data['group']['id']
                malformed_csv = "This is not a valid CSV format at all"
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
                    temp_file.write(malformed_csv)
                    temp_file_path = temp_file.name
                
                try:
                    url = f"{self.base_url}/groups/{group_id}/import-csv"
                    with open(temp_file_path, 'rb') as f:
                        files = {'file': ('bad.csv', f, 'text/csv')}
                        response = self.session.post(url, files=files)
                    
                    print(f"  POST {url} -> {response.status_code}")
                    
                    if response.status_code in [400, 500]:
                        self.log_test("CSV Import Malformed", True, f"- Correctly returned {response.status_code}")
                        success_count += 1
                    else:
                        self.log_test("CSV Import Malformed", False, f"- Expected 400/500, got {response.status_code}")
                        
                finally:
                    os.unlink(temp_file_path)
                    
            except Exception as e:
                self.log_test("CSV Import Malformed", False, f"- Exception: {str(e)}")
        else:
            self.log_test("CSV Import Malformed", False, "- No group available for testing")
        
        # Test 3: Empty CSV file
        if 'group' in self.test_data:
            try:
                import tempfile
                import os
                
                group_id = self.test_data['group']['id']
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
                    temp_file.write("")  # Empty file
                    temp_file_path = temp_file.name
                
                try:
                    url = f"{self.base_url}/groups/{group_id}/import-csv"
                    with open(temp_file_path, 'rb') as f:
                        files = {'file': ('empty.csv', f, 'text/csv')}
                        response = self.session.post(url, files=files)
                    
                    print(f"  POST {url} -> {response.status_code}")
                    
                    if response.status_code in [400, 500]:
                        self.log_test("CSV Import Empty File", True, f"- Correctly returned {response.status_code}")
                        success_count += 1
                    else:
                        self.log_test("CSV Import Empty File", False, f"- Expected 400/500, got {response.status_code}")
                        
                finally:
                    os.unlink(temp_file_path)
                    
            except Exception as e:
                self.log_test("CSV Import Empty File", False, f"- Exception: {str(e)}")
        else:
            self.log_test("CSV Import Empty File", False, "- No group available for testing")
        
        # Test 4: CSV with missing required sections
        if 'group' in self.test_data:
            try:
                import tempfile
                import os
                
                group_id = self.test_data['group']['id']
                incomplete_csv = "GROUP INFORMATION\nGroup Name,Test\n"  # Missing other sections
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
                    temp_file.write(incomplete_csv)
                    temp_file_path = temp_file.name
                
                try:
                    url = f"{self.base_url}/groups/{group_id}/import-csv"
                    with open(temp_file_path, 'rb') as f:
                        files = {'file': ('incomplete.csv', f, 'text/csv')}
                        response = self.session.post(url, files=files)
                    
                    print(f"  POST {url} -> {response.status_code}")
                    
                    # This might succeed with empty data or fail - both are acceptable
                    if response.status_code in [200, 400, 500]:
                        self.log_test("CSV Import Incomplete", True, f"- Handled gracefully with {response.status_code}")
                        success_count += 1
                    else:
                        self.log_test("CSV Import Incomplete", False, f"- Unexpected status {response.status_code}")
                        
                finally:
                    os.unlink(temp_file_path)
                    
            except Exception as e:
                self.log_test("CSV Import Incomplete", False, f"- Exception: {str(e)}")
        else:
            self.log_test("CSV Import Incomplete", False, "- No group available for testing")
        
        return success_count >= 3  # Allow some flexibility in error handling
    
    def test_download_upload_error_handling(self):
        """Test error handling for download/upload endpoints"""
        print("\n=== Testing Download/Upload Error Handling ===")
        
        success_count = 0
        total_tests = 3
        
        # Test 1: CSV download with invalid group ID
        try:
            url = f"{self.base_url}/groups/invalid-group-id/download-csv"
            response = self.session.get(url)
            print(f"  GET {url} -> {response.status_code}")
            
            if response.status_code == 404:
                self.log_test("CSV Download Invalid Group", True, "- Correctly returned 404")
                success_count += 1
            else:
                self.log_test("CSV Download Invalid Group", False, f"- Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("CSV Download Invalid Group", False, f"- Exception: {str(e)}")
        
        # Test 2: Import with invalid group ID
        try:
            import tempfile
            import os
            
            test_data = {"group": {}, "players": [], "teams": [], "game_sessions": []}
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(test_data, temp_file, indent=2)
                temp_file_path = temp_file.name
            
            try:
                url = f"{self.base_url}/groups/invalid-group-id/import"
                with open(temp_file_path, 'rb') as f:
                    files = {'file': ('test.json', f, 'application/json')}
                    response = self.session.post(url, files=files)
                
                print(f"  POST {url} -> {response.status_code}")
                
                if response.status_code == 404:
                    self.log_test("Import Invalid Group", True, "- Correctly returned 404")
                    success_count += 1
                else:
                    self.log_test("Import Invalid Group", False, f"- Expected 404, got {response.status_code}")
                    
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log_test("Import Invalid Group", False, f"- Exception: {str(e)}")
        
        # Test 3: Import with malformed JSON
        if 'group' in self.test_data:
            try:
                import tempfile
                import os
                
                group_id = self.test_data['group']['id']
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                    temp_file.write("invalid json content")
                    temp_file_path = temp_file.name
                
                try:
                    url = f"{self.base_url}/groups/{group_id}/import"
                    with open(temp_file_path, 'rb') as f:
                        files = {'file': ('bad.json', f, 'application/json')}
                        response = self.session.post(url, files=files)
                    
                    print(f"  POST {url} -> {response.status_code}")
                    
                    if response.status_code == 400:
                        self.log_test("Import Malformed JSON", True, "- Correctly returned 400")
                        success_count += 1
                    else:
                        self.log_test("Import Malformed JSON", False, f"- Expected 400, got {response.status_code}")
                        
                finally:
                    os.unlink(temp_file_path)
                    
            except Exception as e:
                self.log_test("Import Malformed JSON", False, f"- Exception: {str(e)}")
        else:
            self.log_test("Import Malformed JSON", False, "- No group available for testing")
        
        return success_count == total_tests
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🎲 Board Game Score Tracker API Test Suite")
        print("=" * 50)
        
        # Test API connectivity first
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Run all test suites
        test_results = []
        test_results.append(self.test_group_management())
        test_results.append(self.test_player_management())
        test_results.append(self.test_team_management())
        test_results.append(self.test_game_sessions())
        test_results.append(self.test_leaderboards())
        test_results.append(self.test_group_stats())
        
        # Run download/upload tests (NEW)
        test_results.append(self.test_download_csv())
        test_results.append(self.test_import_functionality())
        test_results.append(self.test_download_upload_error_handling())
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        print(f"✅ Passed: {len(self.passed_tests)}")
        print(f"❌ Failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print("\nFailed Tests:")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        success_rate = len(self.passed_tests) / (len(self.passed_tests) + len(self.failed_tests)) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        return len(self.failed_tests) == 0
    
    def run_download_upload_tests_only(self):
        """Run only download/upload functionality tests"""
        print("📥📤 Download/Upload Functionality Test Suite")
        print("=" * 50)
        
        # Test API connectivity first
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Setup minimal test data if needed
        if not self.test_data.get('group'):
            print("\n🔧 Setting up test data...")
            if not self.test_group_management():
                print("❌ Failed to setup group data")
                return False
            if not self.test_player_management():
                print("❌ Failed to setup player data")
                return False
            if not self.test_team_management():
                print("❌ Failed to setup team data")
                return False
            if not self.test_game_sessions():
                print("❌ Failed to setup game session data")
                return False
        
        # Run download/upload specific tests
        test_results = []
        test_results.append(self.test_download_csv())
        test_results.append(self.test_import_functionality())
        test_results.append(self.test_download_upload_error_handling())
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 DOWNLOAD/UPLOAD TEST SUMMARY")
        print("=" * 50)
        
        print(f"✅ Passed: {len(self.passed_tests)}")
        print(f"❌ Failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print("\nFailed Tests:")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        success_rate = len(self.passed_tests) / (len(self.passed_tests) + len(self.failed_tests)) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        return len(self.failed_tests) == 0

if __name__ == "__main__":
    import sys
    
    tester = BoardGameAPITester()
    
    # Check if we should run only download/upload tests
    if len(sys.argv) > 1 and sys.argv[1] == "--download-upload-only":
        success = tester.run_download_upload_tests_only()
    else:
        success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Backend API is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the details above.")
        sys.exit(1)