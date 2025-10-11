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
        
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        
    def setup_test_data(self):
        """Create comprehensive test data with multiple games and score ranges"""
        print("\n=== SETTING UP TEST DATA ===")
        
        # 1. Create test group
        group_data = {"group_name": "CSV Test Group"}
        response = requests.post(f"{API_BASE}/groups", json=group_data)
        if response.status_code != 200:
            self.log_test("Create test group", False, f"Status: {response.status_code}")
            return False
            
        self.group_id = response.json()["id"]
        self.log_test("Create test group", True, f"Group ID: {self.group_id}")
        
        # 2. Create players with realistic names
        players = [
            {"player_name": "Emma Watson", "emoji": "🎭"},
            {"player_name": "Michael Jordan", "emoji": "🏀"},
            {"player_name": "Sarah Connor", "emoji": "🤖"},
            {"player_name": "Tony Stark", "emoji": "⚡"}
        ]
        
        for player in players:
            player["group_id"] = self.group_id
            response = requests.post(f"{API_BASE}/players", json=player)
            if response.status_code == 200:
                self.player_ids.append(response.json()["id"])
                self.log_test(f"Create player {player['player_name']}", True)
            else:
                self.log_test(f"Create player {player['player_name']}", False, f"Status: {response.status_code}")
                
        # 3. Create teams
        teams = [
            {"team_name": "The Strategists", "player_ids": self.player_ids[:2]},
            {"team_name": "The Champions", "player_ids": self.player_ids[2:]}
        ]
        
        for team in teams:
            team["group_id"] = self.group_id
            response = requests.post(f"{API_BASE}/teams", json=team)
            if response.status_code == 200:
                self.team_ids.append(response.json()["id"])
                self.log_test(f"Create team {team['team_name']}", True)
            else:
                self.log_test(f"Create team {team['team_name']}", False, f"Status: {response.status_code}")
                
        # 4. Create game sessions with different score ranges for normalization testing
        game_sessions = [
            {
                "game_name": "High Score Game",
                "game_date": "2024-01-15T19:00:00",
                "player_scores": [
                    {"player_id": self.player_ids[0], "player_name": "Emma Watson", "score": 850},
                    {"player_id": self.player_ids[1], "player_name": "Michael Jordan", "score": 920},
                    {"player_id": self.player_ids[2], "player_name": "Sarah Connor", "score": 780}
                ]
            },
            {
                "game_name": "Low Score Game", 
                "game_date": "2024-01-16T20:00:00",
                "player_scores": [
                    {"player_id": self.player_ids[0], "player_name": "Emma Watson", "score": 3},
                    {"player_id": self.player_ids[1], "player_name": "Michael Jordan", "score": 7},
                    {"player_id": self.player_ids[3], "player_name": "Tony Stark", "score": 5}
                ]
            },
            {
                "game_name": "Team Game",
                "game_date": "2024-01-17T18:00:00", 
                "team_scores": [
                    {"team_id": self.team_ids[0], "team_name": "The Strategists", "score": 45, "player_ids": self.player_ids[:2]},
                    {"team_id": self.team_ids[1], "team_name": "The Champions", "score": 38, "player_ids": self.player_ids[2:]}
                ]
            },
            {
                "game_name": "Mixed Game",
                "game_date": "2024-01-18T19:30:00",
                "player_scores": [
                    {"player_id": self.player_ids[2], "player_name": "Sarah Connor", "score": 150}
                ],
                "team_scores": [
                    {"team_id": self.team_ids[0], "team_name": "The Strategists", "score": 200, "player_ids": self.player_ids[:2]}
                ]
            }
        ]
        
        for session in game_sessions:
            session["group_id"] = self.group_id
            response = requests.post(f"{API_BASE}/game-sessions", json=session)
            if response.status_code == 200:
                self.session_ids.append(response.json()["id"])
                self.log_test(f"Create game session {session['game_name']}", True)
            else:
                self.log_test(f"Create game session {session['game_name']}", False, f"Status: {response.status_code}")
                
        return len(self.player_ids) == 4 and len(self.team_ids) == 2 and len(self.session_ids) == 4
        
    def test_csv_download_endpoint(self):
        """Test the CSV download endpoint functionality"""
        print("\n=== TESTING CSV DOWNLOAD ENDPOINT ===")
        
        # Test CSV download
        response = requests.get(f"{API_BASE}/groups/{self.group_id}/download-csv")
        
        # Check response status
        if response.status_code != 200:
            self.log_test("CSV download endpoint response", False, f"Status: {response.status_code}")
            return False
            
        self.log_test("CSV download endpoint response", True, "Status: 200")
        
        # Check headers
        content_type = response.headers.get('content-type', '')
        content_disposition = response.headers.get('content-disposition', '')
        
        self.log_test("CSV content-type header", 'text/csv' in content_type, f"Content-Type: {content_type}")
        self.log_test("CSV attachment header", 'attachment' in content_disposition, f"Content-Disposition: {content_disposition}")
        
        # Store CSV content for further testing
        self.csv_content = response.text
        return True
        
    def test_csv_structure(self):
        """Test complete CSV structure with all required sections"""
        print("\n=== TESTING CSV STRUCTURE ===")
        
        lines = self.csv_content.strip().split('\n')
        
        # Check for required sections
        required_sections = ['GROUP INFORMATION', 'PLAYERS', 'TEAMS', 'GAME SESSIONS']
        found_sections = []
        
        for line in lines:
            if line.strip() in required_sections:
                found_sections.append(line.strip())
                
        for section in required_sections:
            found = section in found_sections
            self.log_test(f"CSV contains {section} section", found)
            
        return len(found_sections) == len(required_sections)
        
    def test_players_section_normalized_scores(self):
        """Test PLAYERS section contains both raw and normalized scores"""
        print("\n=== TESTING PLAYERS SECTION WITH NORMALIZED SCORES ===")
        
        lines = self.csv_content.strip().split('\n')
        
        # Find PLAYERS section
        players_start = -1
        for i, line in enumerate(lines):
            if line.strip() == 'PLAYERS':
                players_start = i
                break
                
        if players_start == -1:
            self.log_test("Find PLAYERS section", False, "Section not found")
            return False
            
        # Check header line
        header_line = lines[players_start + 1]
        expected_headers = [
            'Player Name', 'Emoji', 'Raw Total Score', 'Games Played', 
            'Raw Average Score', 'Normalized Total Score', 'Normalized Average Score', 'Joined Date'
        ]
        
        header_correct = all(header in header_line for header in expected_headers)
        self.log_test("PLAYERS section header contains all score types", header_correct, f"Header: {header_line}")
        
        # Parse player data
        player_data_lines = []
        for i in range(players_start + 2, len(lines)):
            if lines[i].strip() == '' or lines[i].strip() in ['TEAMS', 'GAME SESSIONS']:
                break
            player_data_lines.append(lines[i])
            
        # Check each player has both raw and normalized scores
        players_with_scores = 0
        for line in player_data_lines:
            reader = csv.reader([line])
            row = next(reader)
            if len(row) >= 7:  # Should have at least 7 columns including normalized scores
                raw_total = float(row[2])
                normalized_total = float(row[5])
                normalized_avg = float(row[6])
                
                # Normalized scores should be in 0-1 range (or 0 for players with no games)
                normalized_valid = (0 <= normalized_total <= 10) and (0 <= normalized_avg <= 1)  # Allow some flexibility for totals
                players_with_scores += 1
                
                self.log_test(f"Player {row[0]} has valid normalized scores", normalized_valid, 
                            f"Raw: {raw_total}, Norm Total: {normalized_total}, Norm Avg: {normalized_avg}")
                            
        self.log_test("All players have normalized score data", players_with_scores == 4)
        return players_with_scores == 4
        
    def test_teams_section_normalized_scores(self):
        """Test TEAMS section contains both raw and normalized scores"""
        print("\n=== TESTING TEAMS SECTION WITH NORMALIZED SCORES ===")
        
        lines = self.csv_content.strip().split('\n')
        
        # Find TEAMS section
        teams_start = -1
        for i, line in enumerate(lines):
            if line.strip() == 'TEAMS':
                teams_start = i
                break
                
        if teams_start == -1:
            self.log_test("Find TEAMS section", False, "Section not found")
            return False
            
        # Check header line
        header_line = lines[teams_start + 1]
        expected_headers = [
            'Team Name', 'Players', 'Raw Total Score', 'Games Played',
            'Raw Average Score', 'Normalized Total Score', 'Normalized Average Score', 'Created Date'
        ]
        
        header_correct = all(header in header_line for header in expected_headers)
        self.log_test("TEAMS section header contains all score types", header_correct, f"Header: {header_line}")
        
        # Parse team data
        team_data_lines = []
        for i in range(teams_start + 2, len(lines)):
            if lines[i].strip() == '' or lines[i].strip() == 'GAME SESSIONS':
                break
            team_data_lines.append(lines[i])
            
        # Check each team has both raw and normalized scores
        teams_with_scores = 0
        for line in team_data_lines:
            reader = csv.reader([line])
            row = next(reader)
            if len(row) >= 7:
                raw_total = float(row[2])
                normalized_total = float(row[5])
                normalized_avg = float(row[6])
                
                # Normalized scores should be reasonable
                normalized_valid = (0 <= normalized_total <= 10) and (0 <= normalized_avg <= 1)
                teams_with_scores += 1
                
                self.log_test(f"Team {row[0]} has valid normalized scores", normalized_valid,
                            f"Raw: {raw_total}, Norm Total: {normalized_total}, Norm Avg: {normalized_avg}")
                            
        self.log_test("All teams have normalized score data", teams_with_scores == 2)
        return teams_with_scores == 2
        
    def test_game_sessions_section_enhanced(self):
        """Test GAME SESSIONS section with enhanced normalized scores"""
        print("\n=== TESTING ENHANCED GAME SESSIONS SECTION ===")
        
        lines = self.csv_content.strip().split('\n')
        
        # Find GAME SESSIONS section
        sessions_start = -1
        for i, line in enumerate(lines):
            if line.strip() == 'GAME SESSIONS':
                sessions_start = i
                break
                
        if sessions_start == -1:
            self.log_test("Find GAME SESSIONS section", False, "Section not found")
            return False
            
        # Check header line matches expected format
        header_line = lines[sessions_start + 1]
        expected_header = 'Game Name,Date,Player/Team,Raw Score,Normalized Score,Type'
        
        header_correct = header_line.strip() == expected_header
        self.log_test("GAME SESSIONS header format correct", header_correct, f"Expected: {expected_header}, Got: {header_line}")
        
        # Parse game session data
        session_data_lines = []
        for i in range(sessions_start + 2, len(lines)):
            if lines[i].strip() == '':
                break
            session_data_lines.append(lines[i])
            
        # Check each game session entry has both raw and normalized scores
        valid_entries = 0
        individual_entries = 0
        team_entries = 0
        
        for line in session_data_lines:
            reader = csv.reader([line])
            row = next(reader)
            if len(row) >= 6:
                game_name = row[0]
                date = row[1]
                participant = row[2]
                raw_score = float(row[3])
                normalized_score = float(row[4])
                entry_type = row[5]
                
                # Normalized score should be in 0-1 range with 3 decimal precision
                normalized_valid = (0 <= normalized_score <= 1)
                precision_check = len(str(normalized_score).split('.')[-1]) <= 3
                
                if entry_type == 'Individual':
                    individual_entries += 1
                elif entry_type == 'Team':
                    team_entries += 1
                    
                if normalized_valid and precision_check:
                    valid_entries += 1
                    
                self.log_test(f"Game session entry {participant} in {game_name}", 
                            normalized_valid and precision_check,
                            f"Raw: {raw_score}, Normalized: {normalized_score}, Type: {entry_type}")
                            
        self.log_test("All game session entries have valid normalized scores", valid_entries == len(session_data_lines))
        self.log_test("Game sessions contain individual player entries", individual_entries > 0)
        self.log_test("Game sessions contain team entries", team_entries > 0)
        
        return valid_entries == len(session_data_lines) and individual_entries > 0 and team_entries > 0
        
    def test_normalization_consistency(self):
        """Test that normalization is consistent across different games"""
        print("\n=== TESTING NORMALIZATION CONSISTENCY ===")
        
        lines = self.csv_content.strip().split('\n')
        
        # Find GAME SESSIONS section and parse data
        sessions_start = -1
        for i, line in enumerate(lines):
            if line.strip() == 'GAME SESSIONS':
                sessions_start = i
                break
                
        if sessions_start == -1:
            return False
            
        # Group entries by game
        game_entries = {}
        for i in range(sessions_start + 2, len(lines)):
            if lines[i].strip() == '':
                break
            reader = csv.reader([lines[i]])
            row = next(reader)
            if len(row) >= 6:
                game_name = row[0]
                raw_score = float(row[3])
                normalized_score = float(row[4])
                
                if game_name not in game_entries:
                    game_entries[game_name] = []
                game_entries[game_name].append((raw_score, normalized_score))
                
        # Test normalization per game
        consistent_games = 0
        for game_name, entries in game_entries.items():
            raw_scores = [entry[0] for entry in entries]
            normalized_scores = [entry[1] for entry in entries]
            
            if len(raw_scores) > 1:
                # Check that highest raw score gets highest normalized score
                max_raw_idx = raw_scores.index(max(raw_scores))
                min_raw_idx = raw_scores.index(min(raw_scores))
                
                max_norm = normalized_scores[max_raw_idx]
                min_norm = normalized_scores[min_raw_idx]
                
                # For proper normalization, max should be close to 1.0, min close to 0.0
                normalization_correct = max_norm >= min_norm
                consistent_games += 1 if normalization_correct else 0
                
                self.log_test(f"Game {game_name} normalization consistency", normalization_correct,
                            f"Max raw: {max(raw_scores)} -> {max_norm}, Min raw: {min(raw_scores)} -> {min_norm}")
            else:
                # Single score should default to 0.5
                single_norm = normalized_scores[0]
                single_correct = single_norm == 0.5
                consistent_games += 1 if single_correct else 0
                
                self.log_test(f"Game {game_name} single score normalization", single_correct,
                            f"Single score: {raw_scores[0]} -> {single_norm} (should be 0.5)")
                            
        total_games = len(game_entries)
        self.log_test("All games have consistent normalization", consistent_games == total_games,
                     f"{consistent_games}/{total_games} games consistent")
                     
        return consistent_games == total_games
        
    def test_complete_data_transparency(self):
        """Test that CSV provides complete transparency for analysis"""
        print("\n=== TESTING COMPLETE DATA TRANSPARENCY ===")
        
        # Check that we can parse the entire CSV successfully
        try:
            reader = csv.reader(StringIO(self.csv_content))
            total_lines = sum(1 for row in reader)
            self.log_test("CSV is fully parseable", True, f"Total lines: {total_lines}")
        except Exception as e:
            self.log_test("CSV is fully parseable", False, f"Parse error: {str(e)}")
            return False
            
        # Check that both raw and normalized data is present throughout
        raw_score_count = self.csv_content.count('Raw Score') + self.csv_content.count('Raw Total Score')
        normalized_score_count = self.csv_content.count('Normalized Score') + self.csv_content.count('Normalized Total Score')
        
        self.log_test("CSV contains raw score references", raw_score_count >= 3, f"Raw score references: {raw_score_count}")
        self.log_test("CSV contains normalized score references", normalized_score_count >= 3, f"Normalized score references: {normalized_score_count}")
        
        # Check that we have data for analysis in Excel/Google Sheets
        has_player_summary = 'PLAYERS' in self.csv_content
        has_team_summary = 'TEAMS' in self.csv_content  
        has_detailed_sessions = 'GAME SESSIONS' in self.csv_content
        
        self.log_test("CSV has player summary data", has_player_summary)
        self.log_test("CSV has team summary data", has_team_summary)
        self.log_test("CSV has detailed session data", has_detailed_sessions)
        
        return raw_score_count >= 3 and normalized_score_count >= 3 and has_player_summary and has_team_summary and has_detailed_sessions
        
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n=== CLEANING UP TEST DATA ===")
        
        # Delete game sessions
        for session_id in self.session_ids:
            response = requests.delete(f"{API_BASE}/game-sessions/{session_id}")
            self.log_test(f"Delete game session {session_id}", response.status_code == 200)
            
        # Delete players (this will also clean up teams)
        for player_id in self.player_ids:
            response = requests.delete(f"{API_BASE}/players/{player_id}")
            self.log_test(f"Delete player {player_id}", response.status_code == 200)
            
    def run_all_tests(self):
        """Run all CSV download tests"""
        print("🧪 ENHANCED CSV DOWNLOAD WITH NORMALIZED SCORES - COMPREHENSIVE TESTING")
        print("=" * 80)
        
        # Setup
        if not self.setup_test_data():
            print("❌ CRITICAL: Test data setup failed. Cannot proceed with testing.")
            return False
            
        try:
            # Core functionality tests
            if not self.test_csv_download_endpoint():
                print("❌ CRITICAL: CSV download endpoint failed. Cannot proceed with content testing.")
                return False
                
            # Structure and content tests
            self.test_csv_structure()
            self.test_players_section_normalized_scores()
            self.test_teams_section_normalized_scores()
            self.test_game_sessions_section_enhanced()
            self.test_normalization_consistency()
            self.test_complete_data_transparency()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
            
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 ENHANCED CSV DOWNLOAD FUNCTIONALITY: EXCELLENT")
        elif success_rate >= 75:
            print("✅ ENHANCED CSV DOWNLOAD FUNCTIONALITY: GOOD")
        else:
            print("⚠️  ENHANCED CSV DOWNLOAD FUNCTIONALITY: NEEDS ATTENTION")
            
        return success_rate >= 90

if __name__ == "__main__":
    tester = CSVDownloadTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)