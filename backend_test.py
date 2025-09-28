#!/usr/bin/env python3
"""
Normalized Scoring System Test Suite for Board Game Score Tracker
Tests the NEW normalized scoring system for leaderboard fairness
"""

import requests
import json
from datetime import datetime, timezone, timedelta
import time
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://scoreleader.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

class NormalizedScoringTester:
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
    
    def setup_test_data(self):
        """Setup test group, players, teams, and game sessions with different score ranges"""
        print("\n🔧 Setting up test data for normalized scoring tests...")
        
        # Step 1: Create test group
        group_data = {"group_name": "Normalized Scoring Test Group"}
        data, status = self.make_request("POST", "/groups", group_data)
        
        if not data or status != 200:
            self.log_test("Setup - Create Group", False, f"Status: {status}")
            return False
        
        self.test_data['group'] = data
        group_id = data['id']
        self.log_test("Setup - Create Group", True, f"Code: {data['group_code']}")
        
        # Step 2: Create test players
        players = []
        player_names = ["Alice Johnson", "Bob Smith", "Charlie Brown", "Diana Prince"]
        
        for name in player_names:
            player_data = {
                "player_name": name,
                "group_id": group_id,
                "emoji": "🎮"
            }
            data, status = self.make_request("POST", "/players", player_data)
            
            if data and status == 200:
                players.append(data)
                self.log_test(f"Setup - Create Player ({name})", True)
            else:
                self.log_test(f"Setup - Create Player ({name})", False, f"Status: {status}")
                return False
        
        self.test_data['players'] = players
        
        # Step 3: Create test teams
        teams = []
        team_configs = [
            {"name": "Team Alpha", "players": [players[0]['id'], players[1]['id']]},
            {"name": "Team Beta", "players": [players[2]['id'], players[3]['id']]}
        ]
        
        for config in team_configs:
            team_data = {
                "team_name": config["name"],
                "group_id": group_id,
                "player_ids": config["players"]
            }
            data, status = self.make_request("POST", "/teams", team_data)
            
            if data and status == 200:
                teams.append(data)
                self.log_test(f"Setup - Create Team ({config['name']})", True)
            else:
                self.log_test(f"Setup - Create Team ({config['name']})", False, f"Status: {status}")
                return False
        
        self.test_data['teams'] = teams
        
        # Step 4: Create game sessions with vastly different score ranges
        print("\n🎯 Creating game sessions with different score ranges...")
        
        # Game A: Low scoring game (1-10 range) - like word games
        low_score_sessions = [
            {
                "group_id": group_id,
                "game_name": "Word Puzzle",
                "game_date": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
                "player_scores": [
                    {"player_id": players[0]['id'], "player_name": players[0]['player_name'], "score": 8},
                    {"player_id": players[1]['id'], "player_name": players[1]['player_name'], "score": 6},
                    {"player_id": players[2]['id'], "player_name": players[2]['player_name'], "score": 10},
                    {"player_id": players[3]['id'], "player_name": players[3]['player_name'], "score": 4}
                ],
                "team_scores": []
            },
            {
                "group_id": group_id,
                "game_name": "Word Puzzle",
                "game_date": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
                "player_scores": [
                    {"player_id": players[0]['id'], "player_name": players[0]['player_name'], "score": 7},
                    {"player_id": players[1]['id'], "player_name": players[1]['player_name'], "score": 9},
                    {"player_id": players[2]['id'], "player_name": players[2]['player_name'], "score": 5},
                    {"player_id": players[3]['id'], "player_name": players[3]['player_name'], "score": 3}
                ],
                "team_scores": []
            }
        ]
        
        # Game B: High scoring game (100-1000 range) - like fishbowl
        high_score_sessions = [
            {
                "group_id": group_id,
                "game_name": "Fishbowl",
                "game_date": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
                "player_scores": [
                    {"player_id": players[0]['id'], "player_name": players[0]['player_name'], "score": 800},
                    {"player_id": players[1]['id'], "player_name": players[1]['player_name'], "score": 600},
                    {"player_id": players[2]['id'], "player_name": players[2]['player_name'], "score": 1000},
                    {"player_id": players[3]['id'], "player_name": players[3]['player_name'], "score": 400}
                ],
                "team_scores": []
            },
            {
                "group_id": group_id,
                "game_name": "Fishbowl",
                "game_date": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
                "player_scores": [
                    {"player_id": players[0]['id'], "player_name": players[0]['player_name'], "score": 700},
                    {"player_id": players[1]['id'], "player_name": players[1]['player_name'], "score": 900},
                    {"player_id": players[2]['id'], "player_name": players[2]['player_name'], "score": 500},
                    {"player_id": players[3]['id'], "player_name": players[3]['player_name'], "score": 300}
                ],
                "team_scores": []
            }
        ]
        
        # Team game sessions with different score ranges
        team_sessions = [
            {
                "group_id": group_id,
                "game_name": "Team Word Challenge",
                "game_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                "player_scores": [],
                "team_scores": [
                    {"team_id": teams[0]['id'], "team_name": teams[0]['team_name'], "score": 15, "player_ids": teams[0]['player_ids']},
                    {"team_id": teams[1]['id'], "team_name": teams[1]['team_name'], "score": 12, "player_ids": teams[1]['player_ids']}
                ]
            },
            {
                "group_id": group_id,
                "game_name": "Team Fishbowl",
                "game_date": datetime.now(timezone.utc).isoformat(),
                "player_scores": [],
                "team_scores": [
                    {"team_id": teams[0]['id'], "team_name": teams[0]['team_name'], "score": 1500, "player_ids": teams[0]['player_ids']},
                    {"team_id": teams[1]['id'], "team_name": teams[1]['team_name'], "score": 1200, "player_ids": teams[1]['player_ids']}
                ]
            }
        ]
        
        all_sessions = low_score_sessions + high_score_sessions + team_sessions
        
        for i, session_data in enumerate(all_sessions):
            data, status = self.make_request("POST", "/game-sessions", session_data)
            
            if data and status == 200:
                self.log_test(f"Setup - Game Session {i+1} ({session_data['game_name']})", True)
            else:
                self.log_test(f"Setup - Game Session {i+1} ({session_data['game_name']})", False, f"Status: {status}")
                return False
        
        print("\n✅ Test data setup complete!")
        print(f"   - Group: {self.test_data['group']['group_name']} ({self.test_data['group']['group_code']})")
        print(f"   - Players: {len(players)}")
        print(f"   - Teams: {len(teams)}")
        print(f"   - Game Sessions: {len(all_sessions)}")
        print(f"   - Score Ranges: Word Puzzle (3-10), Fishbowl (300-1000)")
        
        return True
    
    def test_normalized_player_leaderboard(self):
        """Test the normalized scoring system for player leaderboard"""
        print("\n📊 Testing Normalized Player Leaderboard...")
        
        group_id = self.test_data['group']['id']
        data, status = self.make_request("GET", f"/groups/{group_id}/leaderboard/players")
        
        if not data or status != 200:
            self.log_test("Get Player Leaderboard", False, f"Status: {status}")
            return False
        
        self.log_test("Get Player Leaderboard", True, f"Retrieved {len(data)} players")
        
        # Test 1: Verify scores are in reasonable normalized range
        print("\n🔍 Analyzing normalized scores...")
        
        # Each player played 4 individual games + 2 team games = 6 games total
        # Max possible normalized score would be 6.0 (perfect score in all games)
        max_expected_score = 6.0
        
        for player in data:
            if player['total_score'] < 0 or player['total_score'] > max_expected_score:
                self.log_test(f"Normalized score range for {player['name']}", False, 
                             f"Score {player['total_score']} outside expected range 0-{max_expected_score}")
            else:
                self.log_test(f"Normalized score range for {player['name']}", True, 
                             f"Score {player['total_score']} within expected range")
        
        # Test 2: Verify average scores are normalized (should be decimal values <= 1)
        for player in data:
            if player['games_played'] > 0:
                if player['average_score'] > 1.0:
                    self.log_test(f"Normalized average for {player['name']}", False, 
                                 f"Average {player['average_score']} > 1.0, should be normalized")
                else:
                    self.log_test(f"Normalized average for {player['name']}", True, 
                                 f"Average {player['average_score']} is properly normalized")
        
        # Test 3: Verify fairness - players who performed equally well should have similar normalized scores
        print("\n⚖️ Testing scoring fairness...")
        
        # Charlie performed best in both games (10/10 in Word Puzzle, 1000/1000 in Fishbowl)
        # Alice performed well in both (8/10 in Word Puzzle, 800/1000 in Fishbowl) 
        charlie = next((p for p in data if p['name'] == 'Charlie Brown'), None)
        alice = next((p for p in data if p['name'] == 'Alice Johnson'), None)
        
        if charlie and alice:
            # Charlie should be ranked higher due to better performance in both games
            if charlie['total_score'] > alice['total_score']:
                self.log_test("Fairness test - Charlie vs Alice", True, 
                             f"Charlie ({charlie['total_score']:.3f}) > Alice ({alice['total_score']:.3f}) - correct ranking")
            else:
                self.log_test("Fairness test - Charlie vs Alice", False, 
                             f"Charlie ({charlie['total_score']:.3f}) <= Alice ({alice['total_score']:.3f}) - incorrect ranking")
        
        # Test 4: Verify high-scoring games don't dominate
        print("\n🎯 Testing that high-scoring games don't dominate...")
        
        # Without normalization, Fishbowl scores (300-1000) would completely overshadow Word Puzzle (3-10)
        # With normalization, both games should contribute equally to the total
        
        # Diana performed worst in both games (4/10 in Word Puzzle, 400/1000 in Fishbowl)
        # Bob performed better (6/10 in Word Puzzle, 600/1000 in Fishbowl)
        diana = next((p for p in data if p['name'] == 'Diana Prince'), None)
        bob = next((p for p in data if p['name'] == 'Bob Smith'), None)
        
        if diana and bob:
            if bob['total_score'] > diana['total_score']:
                self.log_test("High-score dominance test", True, 
                             f"Bob ({bob['total_score']:.3f}) > Diana ({diana['total_score']:.3f}) - normalization working")
            else:
                self.log_test("High-score dominance test", False, 
                             f"Bob ({bob['total_score']:.3f}) <= Diana ({diana['total_score']:.3f}) - normalization may not be working")
        
        # Test 5: Detailed leaderboard analysis
        print("\n📈 DETAILED LEADERBOARD ANALYSIS:")
        print("-" * 50)
        print("PLAYER LEADERBOARD (Normalized Scores):")
        for i, player in enumerate(data, 1):
            print(f"{i}. {player['name']}: {player['total_score']:.3f} total, {player['average_score']:.3f} avg ({player['games_played']} games)")
        
        return True
    
    def test_normalized_team_leaderboard(self):
        """Test the normalized scoring system for team leaderboard"""
        print("\n🏆 Testing Normalized Team Leaderboard...")
        
        group_id = self.test_data['group']['id']
        data, status = self.make_request("GET", f"/groups/{group_id}/leaderboard/teams")
        
        if not data or status != 200:
            self.log_test("Get Team Leaderboard", False, f"Status: {status}")
            return False
        
        self.log_test("Get Team Leaderboard", True, f"Retrieved {len(data)} teams")
        
        # Verify team normalized scoring
        for team in data:
            if team['average_score'] > 1.0:
                self.log_test(f"Team normalized average for {team['name']}", False, 
                             f"Average {team['average_score']} > 1.0, should be normalized")
            else:
                self.log_test(f"Team normalized average for {team['name']}", True, 
                             f"Average {team['average_score']:.3f} is properly normalized")
        
        # Display team leaderboard
        print("\nTEAM LEADERBOARD (Normalized Scores):")
        for i, team in enumerate(data, 1):
            print(f"{i}. {team['name']}: {team['total_score']:.3f} total, {team['average_score']:.3f} avg ({team['games_played']} games)")
        
        return True
    
    def test_game_specific_leaderboards(self):
        """Test filtering by game name"""
        print("\n🔍 Testing Game-Specific Leaderboards...")
        
        group_id = self.test_data['group']['id']
        
        # Test Word Puzzle only
        data, status = self.make_request("GET", f"/groups/{group_id}/leaderboard/players?game_name=Word Puzzle")
        
        if data and status == 200:
            self.log_test("Game-specific leaderboard (Word Puzzle)", True, f"Retrieved {len(data)} players")
            
            # Verify only Word Puzzle games are included (each player should have 2 games)
            for player in data:
                if player['games_played'] != 2:
                    self.log_test(f"Word Puzzle game count for {player['name']}", False, 
                                 f"Expected 2 games, got {player['games_played']}")
                else:
                    self.log_test(f"Word Puzzle game count for {player['name']}", True, 
                                 f"Correct game count: {player['games_played']}")
        else:
            self.log_test("Game-specific leaderboard (Word Puzzle)", False, f"Status: {status}")
        
        # Test Fishbowl only
        data, status = self.make_request("GET", f"/groups/{group_id}/leaderboard/players?game_name=Fishbowl")
        
        if data and status == 200:
            self.log_test("Game-specific leaderboard (Fishbowl)", True, f"Retrieved {len(data)} players")
        else:
            self.log_test("Game-specific leaderboard (Fishbowl)", False, f"Status: {status}")
        
        return True
    
    def test_players_normalized_endpoint(self):
        """Test the NEW /api/groups/{group_id}/players-normalized endpoint"""
        print("\n🎯 Testing Players Normalized Endpoint...")
        
        group_id = self.test_data['group']['id']
        data, status = self.make_request("GET", f"/groups/{group_id}/players-normalized")
        
        if not data or status != 200:
            self.log_test("Players Normalized Endpoint", False, f"Status: {status}")
            return False
        
        self.log_test("Players Normalized Endpoint", True, f"Retrieved {len(data)} players")
        
        # Store for consistency testing
        self.players_normalized = data
        
        # Test required fields
        required_fields = ["id", "player_name", "emoji", "total_score", "games_played", "average_score"]
        for player in data:
            missing_fields = [field for field in required_fields if field not in player]
            if missing_fields:
                self.log_test(f"Players Normalized - Required Fields ({player.get('player_name', 'Unknown')})", 
                             False, f"Missing: {missing_fields}")
            else:
                self.log_test(f"Players Normalized - Required Fields ({player['player_name']})", True)
        
        # Test normalized score ranges
        for player in data:
            if player['average_score'] > 1.0:
                self.log_test(f"Players Normalized - Score Range ({player['player_name']})", 
                             False, f"Average {player['average_score']} > 1.0")
            else:
                self.log_test(f"Players Normalized - Score Range ({player['player_name']})", 
                             True, f"Average {player['average_score']:.3f} properly normalized")
        
        # Test sorting (should be by total_score descending)
        for i in range(len(data) - 1):
            if data[i]['total_score'] < data[i + 1]['total_score']:
                self.log_test("Players Normalized - Sorting", False, "Not sorted by total_score descending")
                break
        else:
            self.log_test("Players Normalized - Sorting", True, "Properly sorted by total_score descending")
        
        return True
    
    def test_teams_normalized_endpoint(self):
        """Test the NEW /api/groups/{group_id}/teams-normalized endpoint"""
        print("\n🏆 Testing Teams Normalized Endpoint...")
        
        group_id = self.test_data['group']['id']
        data, status = self.make_request("GET", f"/groups/{group_id}/teams-normalized")
        
        if not data or status != 200:
            self.log_test("Teams Normalized Endpoint", False, f"Status: {status}")
            return False
        
        self.log_test("Teams Normalized Endpoint", True, f"Retrieved {len(data)} teams")
        
        # Store for consistency testing
        self.teams_normalized = data
        
        if len(data) == 0:
            self.log_test("Teams Normalized - No Data", True, "No teams with scores (expected if no team games)")
            return True
        
        # Test required fields
        required_fields = ["id", "team_name", "player_ids", "total_score", "games_played", "average_score"]
        for team in data:
            missing_fields = [field for field in required_fields if field not in team]
            if missing_fields:
                self.log_test(f"Teams Normalized - Required Fields ({team.get('team_name', 'Unknown')})", 
                             False, f"Missing: {missing_fields}")
            else:
                self.log_test(f"Teams Normalized - Required Fields ({team['team_name']})", True)
        
        # Test normalized score ranges
        for team in data:
            if team['average_score'] > 1.0:
                self.log_test(f"Teams Normalized - Score Range ({team['team_name']})", 
                             False, f"Average {team['average_score']} > 1.0")
            else:
                self.log_test(f"Teams Normalized - Score Range ({team['team_name']})", 
                             True, f"Average {team['average_score']:.3f} properly normalized")
        
        return True
    
    def test_group_stats_consistency(self):
        """Test /api/groups/{group_id}/stats endpoint for normalized score consistency"""
        print("\n📊 Testing Group Stats Consistency...")
        
        group_id = self.test_data['group']['id']
        data, status = self.make_request("GET", f"/groups/{group_id}/stats")
        
        if not data or status != 200:
            self.log_test("Group Stats Endpoint", False, f"Status: {status}")
            return False
        
        self.log_test("Group Stats Endpoint", True, "Retrieved group statistics")
        
        # Store for consistency testing
        self.group_stats = data
        
        # Test top_player uses normalized scores
        top_player = data.get('top_player')
        if not top_player:
            self.log_test("Group Stats - Top Player", False, "No top player returned")
            return False
        
        if top_player['average_score'] > 1.0:
            self.log_test("Group Stats - Top Player Normalization", False, 
                         f"Top player avg {top_player['average_score']} > 1.0")
        else:
            self.log_test("Group Stats - Top Player Normalization", True, 
                         f"Top player {top_player['name']} avg {top_player['average_score']:.3f} normalized")
        
        return True
    
    def test_score_consistency_verification(self):
        """Test consistency between normalized endpoints and leaderboards"""
        print("\n🔍 Testing Score Consistency Between Endpoints...")
        
        group_id = self.test_data['group']['id']
        
        # Get leaderboard data for comparison
        player_leaderboard, status = self.make_request("GET", f"/groups/{group_id}/leaderboard/players")
        if not player_leaderboard or status != 200:
            self.log_test("Score Consistency - Get Player Leaderboard", False, f"Status: {status}")
            return False
        
        team_leaderboard, status = self.make_request("GET", f"/groups/{group_id}/leaderboard/teams")
        if status != 200:
            self.log_test("Score Consistency - Get Team Leaderboard", False, f"Status: {status}")
            return False
        
        # Test 1: Compare players-normalized vs player leaderboard
        if hasattr(self, 'players_normalized'):
            players_norm_dict = {p['id']: p for p in self.players_normalized}
            players_lead_dict = {p['id']: p for p in player_leaderboard}
            
            consistency_issues = []
            for player_id in players_norm_dict:
                if player_id in players_lead_dict:
                    norm_player = players_norm_dict[player_id]
                    lead_player = players_lead_dict[player_id]
                    
                    # Compare scores (allow small floating point differences)
                    if (abs(norm_player['total_score'] - lead_player['total_score']) > 0.01 or
                        abs(norm_player['average_score'] - lead_player['average_score']) > 0.001):
                        consistency_issues.append(f"{norm_player['player_name']}: norm({norm_player['total_score']:.3f}) vs lead({lead_player['total_score']:.3f})")
            
            if consistency_issues:
                self.log_test("Score Consistency - Player Scores", False, f"Mismatches: {consistency_issues}")
            else:
                self.log_test("Score Consistency - Player Scores", True, "Player scores match between endpoints")
        
        # Test 2: Compare teams-normalized vs team leaderboard
        if hasattr(self, 'teams_normalized') and team_leaderboard:
            teams_norm_dict = {t['id']: t for t in self.teams_normalized}
            teams_lead_dict = {t['id']: t for t in team_leaderboard}
            
            team_consistency_issues = []
            for team_id in teams_norm_dict:
                if team_id in teams_lead_dict:
                    norm_team = teams_norm_dict[team_id]
                    lead_team = teams_lead_dict[team_id]
                    
                    if (abs(norm_team['total_score'] - lead_team['total_score']) > 0.01 or
                        abs(norm_team['average_score'] - lead_team['average_score']) > 0.001):
                        team_consistency_issues.append(f"{norm_team['team_name']}: norm({norm_team['total_score']:.3f}) vs lead({lead_team['total_score']:.3f})")
            
            if team_consistency_issues:
                self.log_test("Score Consistency - Team Scores", False, f"Mismatches: {team_consistency_issues}")
            else:
                self.log_test("Score Consistency - Team Scores", True, "Team scores match between endpoints")
        
        # Test 3: Top player in stats vs #1 in player leaderboard
        if hasattr(self, 'group_stats') and player_leaderboard:
            top_player_stats = self.group_stats['top_player']
            top_player_leaderboard = player_leaderboard[0] if player_leaderboard else None
            
            if not top_player_leaderboard:
                self.log_test("Score Consistency - Top Player Match", False, "No top player in leaderboard")
            elif top_player_stats['id'] != top_player_leaderboard['id']:
                self.log_test("Score Consistency - Top Player Match", False, 
                             f"Different top players: stats={top_player_stats['name']}, leaderboard={top_player_leaderboard['name']}")
            else:
                self.log_test("Score Consistency - Top Player Match", True, 
                             f"Top player consistent: {top_player_stats['name']}")
        
        return True
    
    def test_normalization_verification(self):
        """Verify the normalization algorithm is working correctly"""
        print("\n🧮 Testing Normalization Algorithm Verification...")
        
        print("\n🎯 NORMALIZATION VERIFICATION:")
        print("- Word Puzzle scores: 3-10 (range: 7)")
        print("- Fishbowl scores: 300-1000 (range: 700)")
        print("- Without normalization, Fishbowl would dominate 100:1")
        print("- With normalization, both games contribute equally (0-1 range each)")
        
        # Manual calculation verification
        # Word Puzzle: Charlie got 10 and 5, normalized: (10-3)/7 = 1.0, (5-3)/7 = 0.286
        # Fishbowl: Charlie got 1000 and 500, normalized: (1000-300)/700 = 1.0, (500-300)/700 = 0.286
        # Total normalized for Charlie: 1.0 + 0.286 + 1.0 + 0.286 = 2.572 (plus team games)
        
        group_id = self.test_data['group']['id']
        data, status = self.make_request("GET", f"/groups/{group_id}/leaderboard/players")
        
        if data and status == 200:
            charlie = next((p for p in data if p['name'] == 'Charlie Brown'), None)
            if charlie:
                # Charlie should have a reasonable normalized score
                expected_min = 2.0  # At least 2 from individual games
                expected_max = 6.0  # Maximum possible with team games
                
                if expected_min <= charlie['total_score'] <= expected_max:
                    self.log_test("Normalization algorithm verification", True, 
                                 f"Charlie's score {charlie['total_score']:.3f} within expected range {expected_min}-{expected_max}")
                else:
                    self.log_test("Normalization algorithm verification", False, 
                                 f"Charlie's score {charlie['total_score']:.3f} outside expected range {expected_min}-{expected_max}")
            else:
                self.log_test("Normalization algorithm verification", False, "Charlie not found in leaderboard")
        else:
            self.log_test("Normalization algorithm verification", False, f"Failed to get leaderboard: {status}")
        
        return True
    
    def run_normalized_scoring_tests(self):
        """Run all normalized scoring tests"""
        print("🧪 NORMALIZED SCORING SYSTEM TEST SUITE")
        print("=" * 70)
        print("Testing the NEW normalized scoring system for leaderboard fairness")
        print("=" * 70)
        
        # Setup test data
        if not self.setup_test_data():
            print("\n❌ Failed to setup test data. Stopping tests.")
            return False
        
        # Run normalized scoring tests
        test_results = []
        test_results.append(self.test_normalized_player_leaderboard())
        test_results.append(self.test_normalized_team_leaderboard())
        test_results.append(self.test_game_specific_leaderboards())
        test_results.append(self.test_players_normalized_endpoint())
        test_results.append(self.test_teams_normalized_endpoint())
        test_results.append(self.test_group_stats_consistency())
        test_results.append(self.test_score_consistency_verification())
        test_results.append(self.test_normalization_verification())
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 NORMALIZED SCORING TEST SUMMARY")
        print("=" * 70)
        
        print(f"✅ Passed: {len(self.passed_tests)}")
        print(f"❌ Failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print("\nFailed Tests:")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        success_rate = len(self.passed_tests) / (len(self.passed_tests) + len(self.failed_tests)) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        # Key findings summary
        print("\n🔍 KEY FINDINGS:")
        if len(self.failed_tests) == 0:
            print("✅ Normalized scoring system is working correctly")
            print("✅ High-scoring games do not dominate the leaderboard")
            print("✅ Players are ranked fairly across different game types")
            print("✅ Both individual and team games use normalized scoring")
        else:
            print("⚠️  Some issues found with the normalized scoring system")
            print("   Check failed tests above for details")
        
        return len(self.failed_tests) == 0

if __name__ == "__main__":
    tester = NormalizedScoringTester()
    success = tester.run_normalized_scoring_tests()
    
    if success:
        print("\n🎉 All normalized scoring tests passed! The system is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some normalized scoring tests failed. Check the details above.")
        sys.exit(1)
