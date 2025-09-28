#!/usr/bin/env python3
"""
Backend API Testing for Board Game Score Tracker
Focus: Testing the fix for new player visibility issue in normalized endpoints
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
import sys
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://scoreleader.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

print(f"🎯 Testing backend at: {API_BASE}")
print("Focus: New Player Visibility Fix Verification")

class NewPlayerVisibilityTest:
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
            
    async def create_test_group(self):
        """Create a test group for player testing"""
        try:
            group_data = {
                "group_name": f"New Player Fix Test {uuid.uuid4().hex[:8]}"
            }
            
            async with self.session.post(f"{API_BASE}/groups", json=group_data) as response:
                if response.status == 200:
                    group = await response.json()
                    self.test_group_id = group["id"]
                    self.log_result("Create Test Group", True, f"Created group: {group['group_name']} (ID: {self.test_group_id})")
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("Create Test Group", False, f"Failed to create group: {response.status}", {"error": error_text})
                    return False
                    
        except Exception as e:
            self.log_result("Create Test Group", False, f"Exception creating group: {str(e)}")
            return False
            
    async def test_new_player_creation(self):
        """Test creating new players with realistic data"""
        test_players = [
            {"player_name": "Emma Watson", "emoji": "🎮", "group_id": self.test_group_id},
            {"player_name": "Ryan Reynolds", "emoji": "🎯", "group_id": self.test_group_id},
            {"player_name": "Scarlett Johansson", "emoji": "🏆", "group_id": self.test_group_id}
        ]
        
        for i, player_data in enumerate(test_players):
            try:
                async with self.session.post(f"{API_BASE}/players", json=player_data) as response:
                    if response.status == 200:
                        created_player = await response.json()
                        self.created_players.append(created_player)
                        self.log_result(
                            f"Create New Player {i+1}", 
                            True, 
                            f"Created player: {created_player['player_name']}", 
                            {
                                "player_id": created_player["id"],
                                "group_id": created_player["group_id"],
                                "emoji": created_player["emoji"]
                            }
                        )
                    else:
                        error_text = await response.text()
                        self.log_result(
                            f"Create New Player {i+1}", 
                            False, 
                            f"Failed to create player {player_data['player_name']}: {response.status}",
                            {"error": error_text}
                        )
                        
            except Exception as e:
                self.log_result(f"Create New Player {i+1}", False, f"Exception creating player: {str(e)}")
                
    async def test_standard_players_endpoint(self):
        """Test standard players endpoint (should work)"""
        try:
            async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/players") as response:
                if response.status == 200:
                    players = await response.json()
                    expected_count = len(self.created_players)
                    actual_count = len(players)
                    
                    success = actual_count == expected_count
                    self.log_result(
                        "Standard Players Endpoint", 
                        success, 
                        f"Retrieved {actual_count} players (expected {expected_count})",
                        {
                            "expected_count": expected_count,
                            "actual_count": actual_count,
                            "players": [{"name": p["player_name"], "id": p["id"]} for p in players]
                        }
                    )
                    return players
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Standard Players Endpoint", 
                        False, 
                        f"Failed to retrieve players: {response.status}",
                        {"error": error_text}
                    )
                    return []
                    
        except Exception as e:
            self.log_result("Standard Players Endpoint", False, f"Exception retrieving players: {str(e)}")
            return []
            
    async def test_normalized_players_endpoint_fix(self):
        """Test the MAIN FIX: normalized players endpoint should return ALL players including new ones"""
        try:
            async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/players-normalized") as response:
                if response.status == 200:
                    normalized_players = await response.json()
                    expected_count = len(self.created_players)
                    actual_count = len(normalized_players)
                    
                    # CRITICAL TEST: Should return ALL players (including new ones)
                    main_fix_success = actual_count == expected_count
                    self.log_result(
                        "🎯 MAIN FIX: Normalized Endpoint Returns All Players", 
                        main_fix_success, 
                        f"Retrieved {actual_count} normalized players (expected {expected_count})",
                        {
                            "expected_count": expected_count,
                            "actual_count": actual_count,
                            "fix_working": main_fix_success
                        }
                    )
                    
                    if actual_count > 0:
                        # Test each player's structure and values for new players
                        for i, player in enumerate(normalized_players):
                            player_name = player.get('player_name', 'Unknown')
                            
                            # Test required fields exist
                            required_fields = ['id', 'player_name', 'emoji', 'total_score', 'games_played', 'average_score']
                            missing_fields = [field for field in required_fields if field not in player]
                            
                            if not missing_fields:
                                self.log_result(
                                    f"Player {player_name} Structure", 
                                    True, 
                                    "All required fields present"
                                )
                            else:
                                self.log_result(
                                    f"Player {player_name} Structure", 
                                    False, 
                                    f"Missing fields: {', '.join(missing_fields)}",
                                    {"missing_fields": missing_fields}
                                )
                            
                            # Test new player values (should be zero since no games played)
                            total_score_correct = player.get('total_score') == 0.0
                            games_played_correct = player.get('games_played') == 0
                            average_score_correct = player.get('average_score') == 0.0
                            
                            self.log_result(
                                f"Player {player_name} Zero Scores", 
                                total_score_correct and games_played_correct and average_score_correct, 
                                f"total_score={player.get('total_score')}, games_played={player.get('games_played')}, avg={player.get('average_score')}",
                                {
                                    "total_score": player.get('total_score'),
                                    "games_played": player.get('games_played'),
                                    "average_score": player.get('average_score')
                                }
                            )
                    
                    return normalized_players
                else:
                    error_text = await response.text()
                    self.log_result(
                        "🎯 MAIN FIX: Normalized Endpoint Returns All Players", 
                        False, 
                        f"Failed to retrieve normalized players: {response.status}",
                        {"error": error_text}
                    )
                    return []
                    
        except Exception as e:
            self.log_result("🎯 MAIN FIX: Normalized Endpoint Returns All Players", False, f"Exception retrieving normalized players: {str(e)}")
            return []
            
    async def test_mixed_state_scenario(self):
        """Test mixed state: some players with games, some without"""
        if len(self.created_players) < 2:
            self.log_result("Mixed State Test", False, "Not enough players for mixed state test")
            return
            
        try:
            # Create a game session for the first player only
            game_data = {
                "group_id": self.test_group_id,
                "game_name": "Monopoly",
                "game_date": datetime.utcnow().isoformat(),
                "player_scores": [
                    {
                        "player_id": self.created_players[0]["id"],
                        "player_name": self.created_players[0]["player_name"],
                        "score": 150
                    }
                ],
                "team_scores": []
            }
            
            async with self.session.post(f"{API_BASE}/game-sessions", json=game_data) as response:
                if response.status == 200:
                    self.log_result(
                        "Create Game Session", 
                        True, 
                        f"Created game session for {self.created_players[0]['player_name']}"
                    )
                    
                    # Now test normalized endpoint again
                    async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/players-normalized") as get_response:
                        if get_response.status == 200:
                            mixed_players = await get_response.json()
                            expected_count = len(self.created_players)
                            actual_count = len(mixed_players)
                            
                            # Should still return all players
                            all_players_present = actual_count == expected_count
                            self.log_result(
                                "Mixed State: All Players Present", 
                                all_players_present, 
                                f"Retrieved {actual_count} players (expected {expected_count})"
                            )
                            
                            # Find the experienced player and new players
                            experienced_players = [p for p in mixed_players if p.get('games_played', 0) > 0]
                            new_players = [p for p in mixed_players if p.get('games_played', 0) == 0]
                            
                            # Test experienced player
                            experienced_correct = len(experienced_players) == 1
                            self.log_result(
                                "Mixed State: Experienced Player Count", 
                                experienced_correct, 
                                f"Found {len(experienced_players)} experienced players (expected 1)"
                            )
                            
                            if experienced_players:
                                exp_player = experienced_players[0]
                                has_score = exp_player.get('total_score', 0) > 0
                                has_games = exp_player.get('games_played', 0) == 1
                                self.log_result(
                                    "Mixed State: Experienced Player Stats", 
                                    has_score and has_games, 
                                    f"{exp_player.get('player_name')}: score={exp_player.get('total_score')}, games={exp_player.get('games_played')}"
                                )
                            
                            # Test new players still show zero scores
                            new_players_correct = len(new_players) == (expected_count - 1)
                            self.log_result(
                                "Mixed State: New Player Count", 
                                new_players_correct, 
                                f"Found {len(new_players)} new players (expected {expected_count - 1})"
                            )
                            
                            for new_player in new_players:
                                zero_score = new_player.get('total_score') == 0.0
                                zero_games = new_player.get('games_played') == 0
                                self.log_result(
                                    f"Mixed State: New Player {new_player.get('player_name')} Zeros", 
                                    zero_score and zero_games, 
                                    f"score={new_player.get('total_score')}, games={new_player.get('games_played')}"
                                )
                        else:
                            error_text = await get_response.text()
                            self.log_result(
                                "Mixed State: Normalized Endpoint After Game", 
                                False, 
                                f"Failed to retrieve players after game: {get_response.status}",
                                {"error": error_text}
                            )
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Create Game Session", 
                        False, 
                        f"Failed to create game session: {response.status}",
                        {"error": error_text}
                    )
                    
        except Exception as e:
            self.log_result("Mixed State Test", False, f"Exception in mixed state test: {str(e)}")
            
    async def test_data_structure_verification(self):
        """Verify data structure of normalized endpoint response"""
        try:
            async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/players-normalized") as response:
                if response.status == 200:
                    players_data = await response.json()
                    
                    if len(players_data) > 0:
                        sample_player = players_data[0]
                        
                        # Check all expected fields are present
                        expected_fields = {
                            'id': str,
                            'player_name': str,
                            'emoji': str,
                            'total_score': (int, float),
                            'games_played': int,
                            'average_score': (int, float),
                            'raw_total_score': (int, float),
                            'raw_average_score': (int, float),
                            'created_date': str
                        }
                        
                        all_fields_correct = True
                        for field, expected_type in expected_fields.items():
                            field_present = field in sample_player
                            if not field_present:
                                all_fields_correct = False
                                self.log_result(
                                    f"Data Structure: Field '{field}'", 
                                    False, 
                                    f"Missing field: {field}"
                                )
                            else:
                                field_value = sample_player[field]
                                if isinstance(expected_type, tuple):
                                    type_correct = isinstance(field_value, expected_type)
                                else:
                                    type_correct = isinstance(field_value, expected_type)
                                
                                if not type_correct:
                                    all_fields_correct = False
                                    self.log_result(
                                        f"Data Structure: Field '{field}' Type", 
                                        False, 
                                        f"Expected {expected_type}, got {type(field_value)}"
                                    )
                        
                        if all_fields_correct:
                            self.log_result(
                                "Data Structure Verification", 
                                True, 
                                "All fields present with correct types"
                            )
                    else:
                        self.log_result(
                            "Data Structure Verification", 
                            False, 
                            "No players returned to verify structure"
                        )
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Data Structure Verification", 
                        False, 
                        f"Failed to retrieve players for structure verification: {response.status}",
                        {"error": error_text}
                    )
                    
        except Exception as e:
            self.log_result("Data Structure Verification", False, f"Exception in structure verification: {str(e)}")
            
    async def test_immediate_consistency(self):
        """Test that new players appear immediately in normalized endpoint"""
        try:
            # Create a new player
            player_data = {
                "player_name": "Immediate Test Player",
                "emoji": "⚡",
                "group_id": self.test_group_id
            }
            
            async with self.session.post(f"{API_BASE}/players", json=player_data) as response:
                if response.status == 200:
                    created_player = await response.json()
                    
                    # Immediately try to retrieve it via normalized endpoint
                    async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/players-normalized") as get_response:
                        if get_response.status == 200:
                            players = await get_response.json()
                            found_player = next((p for p in players if p["id"] == created_player["id"]), None)
                            
                            if found_player:
                                self.log_result(
                                    "Immediate Consistency Test", 
                                    True, 
                                    "Player immediately available after creation",
                                    {"created_player": created_player["player_name"]}
                                )
                            else:
                                self.log_result(
                                    "Immediate Consistency Test", 
                                    False, 
                                    "Player not immediately available after creation",
                                    {"created_player_id": created_player["id"], "total_players_found": len(players)}
                                )
                        else:
                            error_text = await get_response.text()
                            self.log_result(
                                "Immediate Consistency Test", 
                                False, 
                                f"Failed to retrieve players immediately after creation: {get_response.status}",
                                {"error": error_text}
                            )
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Immediate Consistency Test", 
                        False, 
                        f"Failed to create player for consistency test: {response.status}",
                        {"error": error_text}
                    )
                    
        except Exception as e:
            self.log_result("Immediate Consistency Test", False, f"Exception in immediate consistency test: {str(e)}")
            
    async def run_all_tests(self):
        """Run all new player visibility fix tests"""
        print("🔍 TESTING NEW PLAYER VISIBILITY FIX")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Setup
            if not await self.create_test_group():
                print("❌ Cannot proceed without test group")
                return
                
            # Core tests for the fix
            await self.test_new_player_creation()
            await self.test_standard_players_endpoint()
            await self.test_normalized_players_endpoint_fix()  # MAIN FIX TEST
            await self.test_mixed_state_scenario()
            await self.test_data_structure_verification()
            await self.test_immediate_consistency()
            
        finally:
            await self.cleanup_session()
            
        # Summary
        print("\n" + "=" * 60)
        print("📊 NEW PLAYER VISIBILITY FIX TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅ PASS" in r["status"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Check if main fix is working
        main_fix_tests = [r for r in self.test_results if "MAIN FIX" in r["test"]]
        main_fix_passed = all("✅ PASS" in r["status"] for r in main_fix_tests)
        
        print(f"\n🎯 MAIN FIX STATUS: {'✅ WORKING' if main_fix_passed else '❌ NEEDS ATTENTION'}")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"  - {result['test']}: {result['message']}")
                    
        print("\n🔍 NEW PLAYER VISIBILITY FIX TESTING COMPLETE")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "main_fix_working": main_fix_passed,
            "results": self.test_results
        }

async def test_backend_health():
    """Quick health check of the backend"""
    print("🏥 BACKEND HEALTH CHECK")
    print("=" * 30)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    print("✅ Backend is responding")
                    return True
                else:
                    print(f"❌ Backend health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Backend health check failed: {str(e)}")
        return False

async def main():
    """Main test execution"""
    print("🚀 BOARD GAME SCORE TRACKER - NEW PLAYER VISIBILITY FIX TESTING")
    print("=" * 80)
    
    # Health check first
    if not await test_backend_health():
        print("❌ Backend is not responding. Please check if the service is running.")
        sys.exit(1)
    
    # Run the main test
    tester = NewPlayerVisibilityTest()
    results = await tester.run_all_tests()
    
    print(f"\n🏁 FINAL RESULT:")
    if results["main_fix_working"] and results["failed"] == 0:
        print("🎉 ALL TESTS PASSED! The new player visibility fix is working correctly.")
        sys.exit(0)
    elif results["main_fix_working"]:
        print(f"✅ MAIN FIX IS WORKING! ({results['failed']} minor issues found)")
        sys.exit(0)
    else:
        print(f"⚠️  MAIN FIX NEEDS ATTENTION. {results['failed']} tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())