#!/usr/bin/env python3
"""
Player Creation and Retrieval Investigation Test Suite
Investigates specific issues with player creation and retrieval endpoints
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://scoreleader.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class PlayerCreationRetrievalTest:
    def __init__(self):
        self.session = None
        self.test_group_id = None
        self.created_players = []
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def setup_test_data(self):
        """Setup comprehensive test data for CSV download testing"""
        print("\n🔧 Setting up test data for Enhanced CSV Download tests...")
        
        # Step 1: Create test group
        group_data = {"group_name": "Enhanced CSV Test Group"}
        data, status = self.make_request("POST", "/groups", group_data)
        
        if not data or status != 200:
            self.log_test("Setup - Create Group", False, f"Status: {status}")
            return False
        
        self.test_data['group'] = data
        group_id = data['id']
        self.log_test("Setup - Create Group", True, f"Code: {data['group_code']}")
        
        # Step 2: Create test players
        players = []
        player_names = ["Emma Watson", "Ryan Reynolds", "Zendaya Coleman", "Chris Evans"]
        emojis = ["🎭", "😎", "🌟", "🛡️"]
        
        for i, name in enumerate(player_names):
            player_data = {
                "player_name": name,
                "group_id": group_id,
                "emoji": emojis[i]
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
            {"name": "Hollywood Stars", "players": [players[0]['id'], players[1]['id']]},
            {"name": "Marvel Heroes", "players": [players[2]['id'], players[3]['id']]}
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
        
        # Step 4: Create diverse game sessions with different score ranges
        print("\n🎯 Creating game sessions with different score ranges...")
        
        game_sessions = [
            # High-scoring game (Fishbowl)
            {
                "group_id": group_id,
                "game_name": "Fishbowl",
                "game_date": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
                "player_scores": [
                    {"player_id": players[0]['id'], "player_name": players[0]['player_name'], "score": 850},
                    {"player_id": players[1]['id'], "player_name": players[1]['player_name'], "score": 920}
                ],
                "team_scores": []
            },
            # Low-scoring game (Word Puzzle)
            {
                "group_id": group_id,
                "game_name": "Word Puzzle",
                "game_date": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
                "player_scores": [
                    {"player_id": players[0]['id'], "player_name": players[0]['player_name'], "score": 7},
                    {"player_id": players[1]['id'], "player_name": players[1]['player_name'], "score": 5},
                    {"player_id": players[2]['id'], "player_name": players[2]['player_name'], "score": 9},
                    {"player_id": players[3]['id'], "player_name": players[3]['player_name'], "score": 6}
                ],
                "team_scores": []
            },
            # Team game (Dungeons & Dragons)
            {
                "group_id": group_id,
                "game_name": "Dungeons & Dragons",
                "game_date": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
                "player_scores": [],
                "team_scores": [
                    {
                        "team_id": teams[0]['id'], 
                        "team_name": teams[0]['team_name'], 
                        "score": 150,
                        "player_ids": teams[0]['player_ids']
                    },
                    {
                        "team_id": teams[1]['id'], 
                        "team_name": teams[1]['team_name'], 
                        "score": 180,
                        "player_ids": teams[1]['player_ids']
                    }
                ]
            },
            # Mixed scoring game (Board Game Night)
            {
                "group_id": group_id,
                "game_name": "Board Game Night",
                "game_date": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
                "player_scores": [
                    {"player_id": players[2]['id'], "player_name": players[2]['player_name'], "score": 45}
                ],
                "team_scores": [
                    {
                        "team_id": teams[0]['id'], 
                        "team_name": teams[0]['team_name'], 
                        "score": 60,
                        "player_ids": teams[0]['player_ids']
                    }
                ]
            }
        ]
        
        for i, session_data in enumerate(game_sessions):
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
        print(f"   - Game Sessions: {len(game_sessions)}")
        print(f"   - Score Ranges: Word Puzzle (5-9), Fishbowl (850-920), Team games (150-180)")
        
        return True
    
    def test_csv_download_endpoint(self):
        """Test the CSV download endpoint functionality"""
        print("\n📥 Testing CSV Download Endpoint...")
        
        group_id = self.test_data['group']['id']
        
        # Test CSV download
        csv_content, status = self.make_request("GET", f"/groups/{group_id}/download-csv")
        
        if status != 200:
            self.log_test("CSV Download Endpoint", False, f"Status: {status}")
            return None
        
        self.log_test("CSV Download Endpoint", True, f"Status: {status}")
        
        # Store CSV content for further testing
        self.csv_content = csv_content
        return csv_content
    
    def test_csv_headers_and_structure(self):
        """Test CSV headers include both raw and normalized scores"""
        print("\n📊 Testing CSV Headers and Structure...")
        
        if not hasattr(self, 'csv_content'):
            self.log_test("CSV Headers Test", False, "No CSV content available")
            return False
        
        lines = self.csv_content.strip().split('\n')
        
        # Test 1: Verify CSV structure sections
        expected_sections = ['GROUP INFORMATION', 'PLAYERS', 'TEAMS', 'GAME SESSIONS']
        found_sections = []
        
        for line in lines:
            if line.strip() in expected_sections:
                found_sections.append(line.strip())
        
        if len(found_sections) == len(expected_sections):
            self.log_test("CSV Structure Sections", True, f"Found all sections: {found_sections}")
        else:
            self.log_test("CSV Structure Sections", False, f"Missing sections. Expected: {expected_sections}, Found: {found_sections}")
        
        # Test 2: Verify PLAYERS section headers
        players_header_line = None
        for i, line in enumerate(lines):
            if line.strip() == 'PLAYERS' and i + 1 < len(lines):
                players_header_line = lines[i + 1]
                break
        
        if not players_header_line:
            self.log_test("Players Header Line", False, "Could not find PLAYERS header line")
            return False
        
        expected_player_headers = [
            'Player Name', 'Emoji', 'Raw Total Score', 'Games Played', 
            'Raw Average Score', 'Normalized Total Score', 'Normalized Average Score', 'Joined Date'
        ]
        
        print(f"   Players header: {players_header_line}")
        
        missing_headers = []
        for header in expected_player_headers:
            if header not in players_header_line:
                missing_headers.append(header)
        
        if not missing_headers:
            self.log_test("Players Header Content", True, "All required headers present")
        else:
            self.log_test("Players Header Content", False, f"Missing headers: {missing_headers}")
        
        # Test 3: Verify TEAMS section headers
        teams_header_line = None
        for i, line in enumerate(lines):
            if line.strip() == 'TEAMS' and i + 1 < len(lines):
                teams_header_line = lines[i + 1]
                break
        
        if not teams_header_line:
            self.log_test("Teams Header Line", False, "Could not find TEAMS header line")
            return False
        
        expected_team_headers = [
            'Team Name', 'Players', 'Raw Total Score', 'Games Played',
            'Raw Average Score', 'Normalized Total Score', 'Normalized Average Score', 'Created Date'
        ]
        
        print(f"   Teams header: {teams_header_line}")
        
        missing_team_headers = []
        for header in expected_team_headers:
            if header not in teams_header_line:
                missing_team_headers.append(header)
        
        if not missing_team_headers:
            self.log_test("Teams Header Content", True, "All required headers present")
        else:
            self.log_test("Teams Header Content", False, f"Missing headers: {missing_team_headers}")
        
        return True
    
    def test_csv_player_data_format(self):
        """Test CSV player data includes both raw and normalized scores"""
        print("\n👤 Testing CSV Player Data Format...")
        
        if not hasattr(self, 'csv_content'):
            self.log_test("CSV Player Data Test", False, "No CSV content available")
            return False
        
        lines = self.csv_content.strip().split('\n')
        
        # Parse player data lines
        player_data_lines = []
        in_players_section = False
        
        for line in lines:
            if line.strip() == 'PLAYERS':
                in_players_section = True
                continue
            elif line.strip() in ['TEAMS', 'GAME SESSIONS', ''] and in_players_section:
                break
            elif in_players_section and line.strip() and not line.startswith('Player Name'):
                player_data_lines.append(line)
        
        if len(player_data_lines) == 0:
            self.log_test("CSV Player Data Lines", False, "No player data found in CSV")
            return False
        
        self.log_test("CSV Player Data Lines", True, f"Found {len(player_data_lines)} player data lines")
        
        # Parse and verify first player data
        try:
            reader = csv.reader([player_data_lines[0]])
            first_player_row = next(reader)
            
            if len(first_player_row) < 8:
                self.log_test("Player Data Columns", False, f"Player row has insufficient columns: {len(first_player_row)}")
                return False
            
            # Extract data
            player_name = first_player_row[0]
            emoji = first_player_row[1]
            raw_total_score = float(first_player_row[2])
            games_played = int(first_player_row[3])
            raw_avg_score = float(first_player_row[4])
            normalized_total = float(first_player_row[5])
            normalized_avg = float(first_player_row[6])
            joined_date = first_player_row[7]
            
            print(f"   Sample player data:")
            print(f"     - Name: {player_name}")
            print(f"     - Emoji: {emoji}")
            print(f"     - Raw Total Score: {raw_total_score}")
            print(f"     - Games Played: {games_played}")
            print(f"     - Raw Average Score: {raw_avg_score}")
            print(f"     - Normalized Total Score: {normalized_total}")
            print(f"     - Normalized Average Score: {normalized_avg}")
            print(f"     - Joined Date: {joined_date}")
            
            # Verify data types and ranges
            if normalized_avg < 0 or normalized_avg > 1:
                self.log_test("Player Normalized Average Range", False, f"Normalized average score out of range [0,1]: {normalized_avg}")
            else:
                self.log_test("Player Normalized Average Range", True, f"Normalized average {normalized_avg:.3f} within range")
            
            if normalized_total < 0:
                self.log_test("Player Normalized Total Range", False, f"Normalized total score should be non-negative: {normalized_total}")
            else:
                self.log_test("Player Normalized Total Range", True, f"Normalized total {normalized_total:.3f} is non-negative")
            
            if raw_total_score < 0:
                self.log_test("Player Raw Total Range", False, f"Raw total score should be non-negative: {raw_total_score}")
            else:
                self.log_test("Player Raw Total Range", True, f"Raw total {raw_total_score} is non-negative")
            
            # Verify all players have both score types
            all_players_valid = True
            for i, line in enumerate(player_data_lines):
                try:
                    reader = csv.reader([line])
                    row = next(reader)
                    if len(row) >= 7:
                        norm_total = float(row[5])
                        norm_avg = float(row[6])
                        if norm_total < 0 or norm_avg < 0 or norm_avg > 1:
                            all_players_valid = False
                            break
                except (ValueError, IndexError):
                    all_players_valid = False
                    break
            
            if all_players_valid:
                self.log_test("All Players Score Validation", True, f"All {len(player_data_lines)} players have valid normalized scores")
            else:
                self.log_test("All Players Score Validation", False, "Some players have invalid normalized scores")
            
        except (ValueError, IndexError) as e:
            self.log_test("Player Data Parsing", False, f"Error parsing player data: {e}")
            return False
        
        return True
    
    def test_csv_team_data_format(self):
        """Test CSV team data includes both raw and normalized scores"""
        print("\n👥 Testing CSV Team Data Format...")
        
        if not hasattr(self, 'csv_content'):
            self.log_test("CSV Team Data Test", False, "No CSV content available")
            return False
        
        lines = self.csv_content.strip().split('\n')
        
        # Parse team data lines
        team_data_lines = []
        in_teams_section = False
        
        for line in lines:
            if line.strip() == 'TEAMS':
                in_teams_section = True
                continue
            elif line.strip() in ['GAME SESSIONS', ''] and in_teams_section:
                break
            elif in_teams_section and line.strip() and not line.startswith('Team Name'):
                team_data_lines.append(line)
        
        if len(team_data_lines) == 0:
            self.log_test("CSV Team Data Lines", True, "No team data found (expected if no team games)")
            return True
        
        self.log_test("CSV Team Data Lines", True, f"Found {len(team_data_lines)} team data lines")
        
        # Parse and verify first team data
        try:
            reader = csv.reader([team_data_lines[0]])
            first_team_row = next(reader)
            
            if len(first_team_row) < 8:
                self.log_test("Team Data Columns", False, f"Team row has insufficient columns: {len(first_team_row)}")
                return False
            
            team_name = first_team_row[0]
            players_str = first_team_row[1]
            team_raw_total = float(first_team_row[2])
            team_games_played = int(first_team_row[3])
            team_raw_avg = float(first_team_row[4])
            team_normalized_total = float(first_team_row[5])
            team_normalized_avg = float(first_team_row[6])
            team_created_date = first_team_row[7]
            
            print(f"   Sample team data:")
            print(f"     - Team Name: {team_name}")
            print(f"     - Players: {players_str}")
            print(f"     - Raw Total Score: {team_raw_total}")
            print(f"     - Games Played: {team_games_played}")
            print(f"     - Raw Average Score: {team_raw_avg}")
            print(f"     - Normalized Total Score: {team_normalized_total}")
            print(f"     - Normalized Average Score: {team_normalized_avg}")
            print(f"     - Created Date: {team_created_date}")
            
            # Verify team normalized scores
            if team_normalized_avg < 0 or team_normalized_avg > 1:
                self.log_test("Team Normalized Average Range", False, f"Team normalized average score out of range [0,1]: {team_normalized_avg}")
            else:
                self.log_test("Team Normalized Average Range", True, f"Team normalized average {team_normalized_avg:.3f} within range")
            
            if team_normalized_total < 0:
                self.log_test("Team Normalized Total Range", False, f"Team normalized total score should be non-negative: {team_normalized_total}")
            else:
                self.log_test("Team Normalized Total Range", True, f"Team normalized total {team_normalized_total:.3f} is non-negative")
            
        except (ValueError, IndexError) as e:
            self.log_test("Team Data Parsing", False, f"Error parsing team data: {e}")
            return False
        
        return True
    
    def test_csv_game_sessions_preserve_raw_scores(self):
        """Test that game sessions preserve original raw score data"""
        print("\n🎮 Testing Game Sessions Preserve Raw Scores...")
        
        if not hasattr(self, 'csv_content'):
            self.log_test("CSV Game Sessions Test", False, "No CSV content available")
            return False
        
        lines = self.csv_content.strip().split('\n')
        
        # Parse game sessions lines
        game_sessions_lines = []
        in_sessions_section = False
        
        for line in lines:
            if line.strip() == 'GAME SESSIONS':
                in_sessions_section = True
                continue
            elif line.strip() == '' and in_sessions_section:
                break
            elif in_sessions_section and line.strip() and not line.startswith('Game Name'):
                game_sessions_lines.append(line)
        
        if len(game_sessions_lines) == 0:
            self.log_test("CSV Game Sessions Lines", False, "No game session data found in CSV")
            return False
        
        self.log_test("CSV Game Sessions Lines", True, f"Found {len(game_sessions_lines)} game session lines")
        
        # Verify game sessions contain original raw scores
        high_score_found = False
        low_score_found = False
        team_score_found = False
        
        for line in game_sessions_lines:
            try:
                reader = csv.reader([line])
                row = next(reader)
                if len(row) >= 4:
                    score = int(row[3])
                    game_name = row[0]
                    score_type = row[4] if len(row) > 4 else "Unknown"
                    
                    if score > 800:  # High score from Fishbowl
                        high_score_found = True
                    elif score < 10:  # Low score from Word Puzzle
                        low_score_found = True
                    elif score_type == "Team" and score > 100:  # Team scores
                        team_score_found = True
                        
            except (ValueError, IndexError):
                continue
        
        if high_score_found:
            self.log_test("High Scores Preserved", True, "High scores (>800) found in game sessions")
        else:
            self.log_test("High Scores Preserved", False, "No high scores found in game sessions")
        
        if low_score_found:
            self.log_test("Low Scores Preserved", True, "Low scores (<10) found in game sessions")
        else:
            self.log_test("Low Scores Preserved", False, "No low scores found in game sessions")
        
        if team_score_found:
            self.log_test("Team Scores Preserved", True, "Team scores found in game sessions")
        else:
            self.log_test("Team Scores Preserved", False, "No team scores found in game sessions")
        
        return True
    
    def test_data_accuracy_vs_leaderboard(self):
        """Test that CSV data matches leaderboard data for accuracy"""
        print("\n🔍 Testing Data Accuracy vs Leaderboard...")
        
        group_id = self.test_data['group']['id']
        
        # Get leaderboard data for comparison
        leaderboard_data, status = self.make_request("GET", f"/groups/{group_id}/leaderboard/players")
        if status != 200:
            self.log_test("Get Leaderboard for Comparison", False, f"Status: {status}")
            return False
        
        self.log_test("Get Leaderboard for Comparison", True, f"Retrieved {len(leaderboard_data)} players")
        
        if not hasattr(self, 'csv_content'):
            self.log_test("CSV Data Accuracy Test", False, "No CSV content available")
            return False
        
        # Parse CSV to extract player data
        lines = self.csv_content.strip().split('\n')
        csv_players = {}
        
        in_players_section = False
        for line in lines:
            if line.strip() == 'PLAYERS':
                in_players_section = True
                continue
            elif line.strip() in ['TEAMS', 'GAME SESSIONS', ''] and in_players_section:
                break
            elif in_players_section and line.strip() and not line.startswith('Player Name'):
                try:
                    reader = csv.reader([line])
                    row = next(reader)
                    if len(row) >= 7:
                        player_name = row[0]
                        csv_players[player_name] = {
                            'raw_total': float(row[2]),
                            'games_played': int(row[3]),
                            'raw_avg': float(row[4]),
                            'normalized_total': float(row[5]),
                            'normalized_avg': float(row[6])
                        }
                except (ValueError, IndexError):
                    continue
        
        self.log_test("Parse CSV Player Data", True, f"Parsed {len(csv_players)} players from CSV")
        
        # Compare CSV data with leaderboard data
        accuracy_issues = []
        for leaderboard_entry in leaderboard_data:
            player_name = leaderboard_entry['name']
            if player_name in csv_players:
                csv_data = csv_players[player_name]
                
                # Compare normalized scores (should match leaderboard)
                if abs(csv_data['normalized_total'] - leaderboard_entry['total_score']) > 0.01:
                    accuracy_issues.append(f"{player_name}: Normalized total mismatch CSV={csv_data['normalized_total']}, Leaderboard={leaderboard_entry['total_score']}")
                
                if abs(csv_data['normalized_avg'] - leaderboard_entry['average_score']) > 0.001:
                    accuracy_issues.append(f"{player_name}: Normalized average mismatch CSV={csv_data['normalized_avg']}, Leaderboard={leaderboard_entry['average_score']}")
                
                # Compare raw scores
                if abs(csv_data['raw_total'] - leaderboard_entry['raw_total_score']) > 0.01:
                    accuracy_issues.append(f"{player_name}: Raw total mismatch CSV={csv_data['raw_total']}, Leaderboard={leaderboard_entry['raw_total_score']}")
        
        if not accuracy_issues:
            self.log_test("CSV vs Leaderboard Accuracy", True, "All player scores match between CSV and leaderboard")
        else:
            self.log_test("CSV vs Leaderboard Accuracy", False, f"Accuracy issues: {accuracy_issues[:3]}")  # Show first 3 issues
        
        return len(accuracy_issues) == 0
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        if 'players' in self.test_data:
            for player in self.test_data['players']:
                self.make_request("DELETE", f"/players/{player['id']}", expected_status=200)
                print(f"   Deleted player: {player['player_name']}")
        
        print("🧹 Cleanup complete!")
    
    def run_enhanced_csv_tests(self):
        """Run all enhanced CSV download tests"""
        print("🧪 ENHANCED CSV DOWNLOAD TEST SUITE")
        print("=" * 70)
        print("Testing the ENHANCED CSV download functionality with both raw and normalized scores")
        print("=" * 70)
        
        # Setup test data
        if not self.setup_test_data():
            print("\n❌ Failed to setup test data. Stopping tests.")
            return False
        
        # Run CSV download tests
        test_results = []
        
        # Test CSV download endpoint
        csv_content = self.test_csv_download_endpoint()
        if csv_content:
            test_results.append(True)
            
            # Test CSV format and headers
            test_results.append(self.test_csv_headers_and_structure())
            
            # Test player data format
            test_results.append(self.test_csv_player_data_format())
            
            # Test team data format
            test_results.append(self.test_csv_team_data_format())
            
            # Test game sessions preserve raw scores
            test_results.append(self.test_csv_game_sessions_preserve_raw_scores())
            
            # Test data accuracy vs leaderboard
            test_results.append(self.test_data_accuracy_vs_leaderboard())
        else:
            test_results.append(False)
        
        # Cleanup
        try:
            self.cleanup_test_data()
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 ENHANCED CSV DOWNLOAD TEST SUMMARY")
        print("=" * 70)
        
        print(f"✅ Passed: {len(self.passed_tests)}")
        print(f"❌ Failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print("\nFailed Tests:")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        success_rate = len(self.passed_tests) / (len(self.passed_tests) + len(self.failed_tests)) * 100 if (len(self.passed_tests) + len(self.failed_tests)) > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        # Key findings summary
        print("\n🔍 KEY FINDINGS:")
        if len(self.failed_tests) == 0:
            print("✅ Enhanced CSV download functionality is working correctly")
            print("✅ CSV contains both raw and normalized scores for players and teams")
            print("✅ Headers include all required score types")
            print("✅ Game sessions preserve original score data")
            print("✅ Data accuracy verified against leaderboard")
        else:
            print("⚠️  Some issues found with the enhanced CSV download functionality")
            print("   Check failed tests above for details")
        
        return len(self.failed_tests) == 0

if __name__ == "__main__":
    tester = CSVDownloadTester()
    success = tester.run_enhanced_csv_tests()
    
    if success:
        print("\n🎉 All enhanced CSV download tests passed! The functionality is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some enhanced CSV download tests failed. Check the details above.")
        sys.exit(1)
