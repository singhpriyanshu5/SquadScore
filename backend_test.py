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

if __name__ == "__main__":
    tester = BoardGameAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Backend API is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the details above.")
        sys.exit(1)