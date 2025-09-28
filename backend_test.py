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
                "group_name": "Player Test Group"
            }
            
            async with self.session.post(f"{API_BASE}/groups", json=group_data) as response:
                if response.status == 200:
                    group = await response.json()
                    self.test_group_id = group["id"]
                    self.log_result("Create Test Group", True, f"Created group with ID: {self.test_group_id}")
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("Create Test Group", False, f"Failed to create group: {response.status}", {"error": error_text})
                    return False
                    
        except Exception as e:
            self.log_result("Create Test Group", False, f"Exception creating group: {str(e)}")
            return False
            
    async def test_player_creation_api(self):
        """Test POST /api/players endpoint with realistic data"""
        test_players = [
            {"player_name": "Emma Rodriguez", "emoji": "🎯", "group_id": self.test_group_id},
            {"player_name": "Marcus Chen", "emoji": "🎲", "group_id": self.test_group_id},
            {"player_name": "Sofia Patel", "emoji": "🏆", "group_id": self.test_group_id}
        ]
        
        for i, player_data in enumerate(test_players):
            try:
                async with self.session.post(f"{API_BASE}/players", json=player_data) as response:
                    if response.status == 200:
                        created_player = await response.json()
                        self.created_players.append(created_player)
                        self.log_result(
                            f"Create Player {i+1}", 
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
                            f"Create Player {i+1}", 
                            False, 
                            f"Failed to create player {player_data['player_name']}: {response.status}",
                            {"error": error_text}
                        )
                        
            except Exception as e:
                self.log_result(f"Create Player {i+1}", False, f"Exception creating player: {str(e)}")
                
    async def test_player_retrieval_standard(self):
        """Test GET /api/groups/{group_id}/players endpoint"""
        try:
            async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/players") as response:
                if response.status == 200:
                    players = await response.json()
                    self.log_result(
                        "Retrieve Players (Standard)", 
                        True, 
                        f"Retrieved {len(players)} players",
                        {
                            "player_count": len(players),
                            "players": [{"name": p["player_name"], "id": p["id"]} for p in players]
                        }
                    )
                    
                    # Check if all created players are present
                    created_ids = {p["id"] for p in self.created_players}
                    retrieved_ids = {p["id"] for p in players}
                    missing_ids = created_ids - retrieved_ids
                    
                    if missing_ids:
                        self.log_result(
                            "Player Consistency Check (Standard)", 
                            False, 
                            f"Missing {len(missing_ids)} created players",
                            {"missing_player_ids": list(missing_ids)}
                        )
                    else:
                        self.log_result(
                            "Player Consistency Check (Standard)", 
                            True, 
                            "All created players found in retrieval"
                        )
                        
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Retrieve Players (Standard)", 
                        False, 
                        f"Failed to retrieve players: {response.status}",
                        {"error": error_text}
                    )
                    
        except Exception as e:
            self.log_result("Retrieve Players (Standard)", False, f"Exception retrieving players: {str(e)}")
            
    async def test_player_retrieval_normalized(self):
        """Test GET /api/groups/{group_id}/players-normalized endpoint"""
        try:
            async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/players-normalized") as response:
                if response.status == 200:
                    players = await response.json()
                    self.log_result(
                        "Retrieve Players (Normalized)", 
                        True, 
                        f"Retrieved {len(players)} normalized players",
                        {
                            "player_count": len(players),
                            "players": [{"name": p["player_name"], "id": p["id"], "total_score": p.get("total_score", 0)} for p in players]
                        }
                    )
                    
                    # Check if all created players are present
                    created_ids = {p["id"] for p in self.created_players}
                    retrieved_ids = {p["id"] for p in players}
                    missing_ids = created_ids - retrieved_ids
                    
                    if missing_ids:
                        self.log_result(
                            "Player Consistency Check (Normalized)", 
                            False, 
                            f"Missing {len(missing_ids)} created players",
                            {"missing_player_ids": list(missing_ids)}
                        )
                    else:
                        self.log_result(
                            "Player Consistency Check (Normalized)", 
                            True, 
                            "All created players found in normalized retrieval"
                        )
                        
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Retrieve Players (Normalized)", 
                        False, 
                        f"Failed to retrieve normalized players: {response.status}",
                        {"error": error_text}
                    )
                    
        except Exception as e:
            self.log_result("Retrieve Players (Normalized)", False, f"Exception retrieving normalized players: {str(e)}")
            
    async def test_group_isolation(self):
        """Test that players are properly isolated by group"""
        try:
            # Create a second test group
            group_data = {"group_name": "Isolation Test Group"}
            async with self.session.post(f"{API_BASE}/groups", json=group_data) as response:
                if response.status != 200:
                    self.log_result("Group Isolation Test", False, "Failed to create second group")
                    return
                    
                second_group = await response.json()
                second_group_id = second_group["id"]
                
            # Add a player to the second group
            player_data = {
                "player_name": "Isolation Test Player",
                "emoji": "🔒",
                "group_id": second_group_id
            }
            
            async with self.session.post(f"{API_BASE}/players", json=player_data) as response:
                if response.status != 200:
                    self.log_result("Group Isolation Test", False, "Failed to create player in second group")
                    return
                    
            # Check that first group still has only its players
            async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/players-normalized") as response:
                if response.status == 200:
                    first_group_players = await response.json()
                    expected_count = len(self.created_players)
                    actual_count = len(first_group_players)
                    
                    if actual_count == expected_count:
                        self.log_result(
                            "Group Isolation Test", 
                            True, 
                            f"Group isolation working - first group has {actual_count} players as expected"
                        )
                    else:
                        self.log_result(
                            "Group Isolation Test", 
                            False, 
                            f"Group isolation failed - expected {expected_count}, got {actual_count} players",
                            {"expected": expected_count, "actual": actual_count}
                        )
                else:
                    self.log_result("Group Isolation Test", False, "Failed to retrieve first group players for isolation test")
                    
        except Exception as e:
            self.log_result("Group Isolation Test", False, f"Exception in group isolation test: {str(e)}")
            
    async def test_database_state_verification(self):
        """Verify that players are actually stored in the database with correct structure"""
        try:
            # Test by retrieving a specific player and checking its structure
            if not self.created_players:
                self.log_result("Database State Verification", False, "No created players to verify")
                return
                
            first_player = self.created_players[0]
            
            # Get all players and find our test player
            async with self.session.get(f"{API_BASE}/groups/{self.test_group_id}/players") as response:
                if response.status == 200:
                    all_players = await response.json()
                    test_player = next((p for p in all_players if p["id"] == first_player["id"]), None)
                    
                    if test_player:
                        # Check required fields
                        required_fields = ["id", "player_name", "group_id", "emoji", "total_score", "games_played", "created_date"]
                        missing_fields = [field for field in required_fields if field not in test_player]
                        
                        if not missing_fields:
                            # Check data types and values
                            checks = []
                            checks.append(("ID matches", test_player["id"] == first_player["id"]))
                            checks.append(("Name matches", test_player["player_name"] == first_player["player_name"]))
                            checks.append(("Group ID matches", test_player["group_id"] == self.test_group_id))
                            checks.append(("Emoji matches", test_player["emoji"] == first_player["emoji"]))
                            checks.append(("Total score is integer", isinstance(test_player["total_score"], int)))
                            checks.append(("Games played is integer", isinstance(test_player["games_played"], int)))
                            checks.append(("Created date exists", test_player["created_date"] is not None))
                            
                            failed_checks = [check[0] for check in checks if not check[1]]
                            
                            if not failed_checks:
                                self.log_result(
                                    "Database State Verification", 
                                    True, 
                                    "Player data structure and values are correct",
                                    {"verified_player": test_player["player_name"], "all_checks_passed": True}
                                )
                            else:
                                self.log_result(
                                    "Database State Verification", 
                                    False, 
                                    f"Data validation failed: {', '.join(failed_checks)}",
                                    {"failed_checks": failed_checks, "player_data": test_player}
                                )
                        else:
                            self.log_result(
                                "Database State Verification", 
                                False, 
                                f"Missing required fields: {', '.join(missing_fields)}",
                                {"missing_fields": missing_fields, "player_data": test_player}
                            )
                    else:
                        self.log_result(
                            "Database State Verification", 
                            False, 
                            "Created player not found in database retrieval"
                        )
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Database State Verification", 
                        False, 
                        f"Failed to retrieve players for verification: {response.status}",
                        {"error": error_text}
                    )
                    
        except Exception as e:
            self.log_result("Database State Verification", False, f"Exception in database verification: {str(e)}")
            
    async def test_immediate_consistency(self):
        """Test immediate consistency - create player and immediately retrieve"""
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
        """Run all player creation and retrieval tests"""
        print("🔍 STARTING PLAYER CREATION AND RETRIEVAL INVESTIGATION")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Setup
            if not await self.create_test_group():
                print("❌ Cannot proceed without test group")
                return
                
            # Core tests as requested
            await self.test_player_creation_api()
            await self.test_player_retrieval_standard()
            await self.test_player_retrieval_normalized()
            await self.test_database_state_verification()
            await self.test_immediate_consistency()
            await self.test_group_isolation()
            
        finally:
            await self.cleanup_session()
            
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅ PASS" in r["status"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"  - {result['test']}: {result['message']}")
                    
        print("\n🔍 INVESTIGATION COMPLETE")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": self.test_results
        }

async def main():
    """Main test execution"""
    tester = PlayerCreationRetrievalTest()
    results = await tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())