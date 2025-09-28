from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import random
import string


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

def generate_group_code():
    """Generate a unique 6-character group code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Define Models

# Group Models
class Group(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_code: str
    group_name: str
    created_date: datetime = Field(default_factory=datetime.utcnow)

class GroupCreate(BaseModel):
    group_name: str

class GroupJoin(BaseModel):
    group_code: str

# Player Models
class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_name: str
    group_id: str
    emoji: str = "😀"  # Default emoji
    total_score: int = 0
    games_played: int = 0
    created_date: datetime = Field(default_factory=datetime.utcnow)

class PlayerCreate(BaseModel):
    player_name: str
    group_id: str
    emoji: str = "😀"  # Default emoji

# Team Models
class Team(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    team_name: str
    group_id: str
    player_ids: List[str] = []
    total_score: int = 0
    games_played: int = 0
    created_date: datetime = Field(default_factory=datetime.utcnow)

class TeamCreate(BaseModel):
    team_name: str
    group_id: str
    player_ids: List[str] = []

# Game Session Models
class PlayerScore(BaseModel):
    player_id: str
    player_name: str
    score: int

class TeamScore(BaseModel):
    team_id: str
    team_name: str
    score: int
    player_ids: List[str]

class GameSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str
    game_name: str
    game_date: datetime
    player_scores: List[PlayerScore] = []
    team_scores: List[TeamScore] = []
    created_date: datetime = Field(default_factory=datetime.utcnow)

class GameSessionCreate(BaseModel):
    group_id: str
    game_name: str
    game_date: datetime
    player_scores: List[PlayerScore] = []
    team_scores: List[TeamScore] = []

# Leaderboard Models
class LeaderboardEntry(BaseModel):
    id: str
    name: str
    total_score: int
    games_played: int
    average_score: float

class GroupStats(BaseModel):
    total_players: int
    total_teams: int
    total_games: int
    most_played_game: Optional[str]
    top_player: Optional[LeaderboardEntry]

# Routes

@api_router.get("/")
async def root():
    return {"message": "Board Game Score Tracker API"}

# Group Management Routes
@api_router.post("/groups", response_model=Group)
async def create_group(group_data: GroupCreate):
    """Create a new group with a unique code"""
    group_code = generate_group_code()
    
    # Ensure group code is unique
    while await db.groups.find_one({"group_code": group_code}):
        group_code = generate_group_code()
    
    group_dict = group_data.dict()
    group_obj = Group(group_code=group_code, **group_dict)
    
    result = await db.groups.insert_one(group_obj.dict())
    if result.inserted_id:
        return group_obj
    else:
        raise HTTPException(status_code=500, detail="Failed to create group")

@api_router.post("/groups/join", response_model=Group)
async def join_group(join_data: GroupJoin):
    """Join an existing group using group code"""
    group = await db.groups.find_one({"group_code": join_data.group_code})
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return Group(**group)

@api_router.get("/groups/{group_id}")
async def get_group(group_id: str):
    """Get group details by ID"""
    group = await db.groups.find_one({"id": group_id})
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return Group(**group)

# Player Management Routes
@api_router.post("/players", response_model=Player)
async def create_player(player_data: PlayerCreate):
    """Add a new player to a group"""
    # Verify group exists
    group = await db.groups.find_one({"id": player_data.group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if player name already exists in this group
    existing_player = await db.players.find_one({
        "player_name": player_data.player_name,
        "group_id": player_data.group_id
    })
    if existing_player:
        raise HTTPException(status_code=400, detail="Player name already exists in this group")
    
    player_dict = player_data.dict()
    player_obj = Player(**player_dict)
    
    result = await db.players.insert_one(player_obj.dict())
    if result.inserted_id:
        return player_obj
    else:
        raise HTTPException(status_code=500, detail="Failed to create player")

@api_router.get("/groups/{group_id}/players", response_model=List[Player])
async def get_group_players(group_id: str):
    """Get all players in a group"""
    players = await db.players.find({"group_id": group_id}).to_list(1000)
    return [Player(**player) for player in players]

class PlayerUpdate(BaseModel):
    player_name: str
    emoji: str

@api_router.put("/players/{player_id}", response_model=Player)
async def update_player(player_id: str, player_data: PlayerUpdate):
    """Update a player's name and emoji"""
    # Check if player exists
    existing_player = await db.players.find_one({"id": player_id})
    if not existing_player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Check if new name already exists in the same group (if name is changing)
    if player_data.player_name != existing_player["player_name"]:
        name_exists = await db.players.find_one({
            "player_name": player_data.player_name,
            "group_id": existing_player["group_id"],
            "id": {"$ne": player_id}
        })
        if name_exists:
            raise HTTPException(status_code=400, detail="Player name already exists in this group")
    
    # Update player
    update_result = await db.players.update_one(
        {"id": player_id},
        {"$set": {
            "player_name": player_data.player_name,
            "emoji": player_data.emoji
        }}
    )
    
    if update_result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update player")
    
    # Return updated player
    updated_player = await db.players.find_one({"id": player_id})
    return Player(**updated_player)

@api_router.delete("/players/{player_id}")
async def delete_player(player_id: str):
    """Delete a player and remove them from all teams and game sessions"""
    # Check if player exists
    player = await db.players.find_one({"id": player_id})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Remove player from all teams
    await db.teams.update_many(
        {"player_ids": player_id},
        {"$pull": {"player_ids": player_id}}
    )
    
    # Remove player scores from all game sessions
    await db.game_sessions.update_many(
        {"player_scores.player_id": player_id},
        {"$pull": {"player_scores": {"player_id": player_id}}}
    )
    
    # Delete the player
    delete_result = await db.players.delete_one({"id": player_id})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete player")
    
    return {"message": "Player deleted successfully"}

# Team Management Routes
@api_router.post("/teams", response_model=Team)
async def create_team(team_data: TeamCreate):
    """Create a new team in a group"""
    # Verify group exists
    group = await db.groups.find_one({"id": team_data.group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Verify all player IDs exist in the group
    if team_data.player_ids:
        for player_id in team_data.player_ids:
            player = await db.players.find_one({"id": player_id, "group_id": team_data.group_id})
            if not player:
                raise HTTPException(status_code=404, detail=f"Player {player_id} not found in group")
    
    # Check if team name already exists in this group
    existing_team = await db.teams.find_one({
        "team_name": team_data.team_name,
        "group_id": team_data.group_id
    })
    if existing_team:
        raise HTTPException(status_code=400, detail="Team name already exists in this group")
    
    team_dict = team_data.dict()
    team_obj = Team(**team_dict)
    
    result = await db.teams.insert_one(team_obj.dict())
    if result.inserted_id:
        return team_obj
    else:
        raise HTTPException(status_code=500, detail="Failed to create team")

@api_router.get("/groups/{group_id}/teams", response_model=List[Team])
async def get_group_teams(group_id: str):
    """Get all teams in a group"""
    teams = await db.teams.find({"group_id": group_id}).to_list(1000)
    return [Team(**team) for team in teams]

# Game Session Routes
@api_router.post("/game-sessions", response_model=GameSession)
async def create_game_session(session_data: GameSessionCreate):
    """Record a new game session with scores"""
    # Verify group exists
    group = await db.groups.find_one({"id": session_data.group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    session_dict = session_data.dict()
    session_obj = GameSession(**session_dict)
    
    # Insert game session
    result = await db.game_sessions.insert_one(session_obj.dict())
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to create game session")
    
    # Update player and team statistics
    await update_player_team_stats(session_obj)
    
    return session_obj

async def update_player_team_stats(session: GameSession):
    """Update player and team total scores and game counts"""
    
    # Update individual player scores
    for player_score in session.player_scores:
        await db.players.update_one(
            {"id": player_score.player_id},
            {
                "$inc": {
                    "total_score": player_score.score,
                    "games_played": 1
                }
            }
        )
    
    # Update team scores and distribute to team players
    for team_score in session.team_scores:
        # Update team stats
        await db.teams.update_one(
            {"id": team_score.team_id},
            {
                "$inc": {
                    "total_score": team_score.score,
                    "games_played": 1
                }
            }
        )
        
        # Distribute team score equally among team players
        if team_score.player_ids:
            score_per_player = team_score.score // len(team_score.player_ids)
            for player_id in team_score.player_ids:
                await db.players.update_one(
                    {"id": player_id},
                    {
                        "$inc": {
                            "total_score": score_per_player,
                            "games_played": 1
                        }
                    }
                )

@api_router.get("/groups/{group_id}/game-sessions", response_model=List[GameSession])
async def get_game_sessions(group_id: str):
    """Get all game sessions for a group"""
    sessions = await db.game_sessions.find({"group_id": group_id}).sort("game_date", -1).to_list(1000)
    return [GameSession(**session) for session in sessions]

@api_router.delete("/game-sessions/{session_id}")
async def delete_game_session(session_id: str):
    """Delete a game session and revert player/team scores"""
    # Get the game session first
    session = await db.game_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    # Revert player scores
    for player_score in session.get("player_scores", []):
        await db.players.update_one(
            {"id": player_score["player_id"]},
            {
                "$inc": {
                    "total_score": -player_score["score"],
                    "games_played": -1
                }
            }
        )
    
    # Revert team scores and distributed player scores
    for team_score in session.get("team_scores", []):
        # Revert team stats
        await db.teams.update_one(
            {"id": team_score["team_id"]},
            {
                "$inc": {
                    "total_score": -team_score["score"],
                    "games_played": -1
                }
            }
        )
        
        # Revert distributed player scores
        if team_score.get("player_ids"):
            score_per_player = team_score["score"] // len(team_score["player_ids"])
            for player_id in team_score["player_ids"]:
                await db.players.update_one(
                    {"id": player_id},
                    {
                        "$inc": {
                            "total_score": -score_per_player,
                            "games_played": -1
                        }
                    }
                )
    
    # Delete the game session
    delete_result = await db.game_sessions.delete_one({"id": session_id})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete game session")
    
    return {"message": "Game session deleted successfully"}

# Leaderboard and Dashboard Routes
async def calculate_normalized_scores(group_id: str, game_name: Optional[str] = None, year: Optional[int] = None, month: Optional[int] = None):
    """Calculate normalized scores (0-1) for each game to ensure fair leaderboard"""
    # Build session filter
    session_filter = {"group_id": group_id}
    if game_name:
        session_filter["game_name"] = {"$regex": game_name, "$options": "i"}
    if year or month:
        date_filter = {}
        if year:
            if month:
                from datetime import datetime
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1)
                else:
                    end_date = datetime(year, month + 1, 1)
                date_filter = {"$gte": start_date, "$lt": end_date}
            else:
                from datetime import datetime
                start_date = datetime(year, 1, 1)
                end_date = datetime(year + 1, 1, 1)
                date_filter = {"$gte": start_date, "$lt": end_date}
        session_filter["game_date"] = date_filter

    sessions = await db.game_sessions.find(session_filter).to_list(1000)
    
    # Group sessions by game name and collect all scores
    game_scores = {}
    player_stats = {}
    
    for session in sessions:
        game_name = session["game_name"]
        if game_name not in game_scores:
            game_scores[game_name] = []
        
        # Collect all scores for this game session
        session_scores = []
        
        # Individual player scores
        for player_score in session.get("player_scores", []):
            session_scores.append(player_score["score"])
            game_scores[game_name].append(player_score["score"])
        
        # Team scores (we'll use the team score for normalization)
        for team_score in session.get("team_scores", []):
            session_scores.append(team_score["score"])
            game_scores[game_name].append(team_score["score"])
    
    # Calculate min/max for each game for normalization
    game_normalization = {}
    for game_name, scores in game_scores.items():
        if len(scores) > 0:
            min_score = min(scores)
            max_score = max(scores)
            game_normalization[game_name] = {
                "min": min_score,
                "max": max_score,
                "range": max_score - min_score if max_score != min_score else 1
            }
    
    # Now calculate normalized scores for players
    for session in sessions:
        game_name = session["game_name"]
        normalization = game_normalization.get(game_name)
        
        if not normalization:
            continue
            
        # Process individual player scores
        for player_score in session.get("player_scores", []):
            player_id = player_score["player_id"]
            raw_score = player_score["score"]
            
            # Normalize score to 0-1 range
            normalized_score = (raw_score - normalization["min"]) / normalization["range"]
            
            if player_id not in player_stats:
                player_stats[player_id] = {
                    "name": player_score["player_name"],
                    "total_normalized_score": 0,
                    "total_raw_score": 0,
                    "games_played": 0
                }
            
            player_stats[player_id]["total_normalized_score"] += normalized_score
            player_stats[player_id]["total_raw_score"] += raw_score
            player_stats[player_id]["games_played"] += 1
        
        # Process team scores (distributed to players)
        for team_score in session.get("team_scores", []):
            if team_score.get("player_ids"):
                raw_score = team_score["score"]
                normalized_score = (raw_score - normalization["min"]) / normalization["range"]
                
                # Distribute normalized score equally among team members
                normalized_score_per_player = normalized_score / len(team_score["player_ids"])
                raw_score_per_player = raw_score // len(team_score["player_ids"])
                
                for player_id in team_score["player_ids"]:
                    if player_id not in player_stats:
                        player = await db.players.find_one({"id": player_id})
                        player_name = player["player_name"] if player else "Unknown"
                        player_stats[player_id] = {
                            "name": player_name,
                            "total_normalized_score": 0,
                            "total_raw_score": 0,
                            "games_played": 0
                        }
                    
                    player_stats[player_id]["total_normalized_score"] += normalized_score_per_player
                    player_stats[player_id]["total_raw_score"] += raw_score_per_player
                    player_stats[player_id]["games_played"] += 1
    
    return player_stats

@api_router.get("/groups/{group_id}/leaderboard/players", response_model=List[LeaderboardEntry])
async def get_player_leaderboard(
    group_id: str,
    game_name: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None
):
    """Get player leaderboard for a group with optional filters using normalized scores"""
    # Use normalized scoring for fair comparison across different games
    player_stats = await calculate_normalized_scores(group_id, game_name, year, month)
    
    # Convert to leaderboard format
    leaderboard = []
    for player_id, stats in player_stats.items():
        # Use normalized score for leaderboard ranking, but show raw scores for display
        avg_normalized_score = stats["total_normalized_score"] / stats["games_played"] if stats["games_played"] > 0 else 0
        avg_raw_score = stats["total_raw_score"] / stats["games_played"] if stats["games_played"] > 0 else 0
        
        leaderboard.append(LeaderboardEntry(
            id=player_id,
            name=stats["name"],
            total_score=round(stats["total_normalized_score"], 2),  # Use normalized score for ranking
            games_played=stats["games_played"],
            average_score=round(avg_normalized_score, 3)  # Show normalized average (3 decimals for precision)
        ))
    
    # Sort by normalized total score
    leaderboard.sort(key=lambda x: x.total_score, reverse=True)
    return leaderboard

@api_router.get("/groups/{group_id}/leaderboard/teams", response_model=List[LeaderboardEntry])
async def get_team_leaderboard(group_id: str):
    """Get team leaderboard for a group using normalized scores"""
    # Calculate normalized scores for teams
    sessions = await db.game_sessions.find({"group_id": group_id}).to_list(1000)
    
    # Group sessions by game name and collect all team scores
    game_scores = {}
    team_stats = {}
    
    for session in sessions:
        game_name = session["game_name"]
        if game_name not in game_scores:
            game_scores[game_name] = []
        
        # Collect all team scores for this game
        for team_score in session.get("team_scores", []):
            game_scores[game_name].append(team_score["score"])
    
    # Calculate min/max for each game for normalization
    game_normalization = {}
    for game_name, scores in game_scores.items():
        if len(scores) > 0:
            min_score = min(scores)
            max_score = max(scores)
            game_normalization[game_name] = {
                "min": min_score,
                "max": max_score,
                "range": max_score - min_score if max_score != min_score else 1
            }
    
    # Calculate normalized scores for teams
    for session in sessions:
        game_name = session["game_name"]
        normalization = game_normalization.get(game_name)
        
        if not normalization:
            continue
            
        for team_score in session.get("team_scores", []):
            team_id = team_score["team_id"]
            raw_score = team_score["score"]
            
            # Normalize score to 0-1 range
            normalized_score = (raw_score - normalization["min"]) / normalization["range"]
            
            if team_id not in team_stats:
                team_stats[team_id] = {
                    "name": team_score["team_name"],
                    "total_normalized_score": 0,
                    "total_raw_score": 0,
                    "games_played": 0
                }
            
            team_stats[team_id]["total_normalized_score"] += normalized_score
            team_stats[team_id]["total_raw_score"] += raw_score
            team_stats[team_id]["games_played"] += 1
    
    # Convert to leaderboard format
    leaderboard = []
    for team_id, stats in team_stats.items():
        avg_normalized_score = stats["total_normalized_score"] / stats["games_played"] if stats["games_played"] > 0 else 0
        
        leaderboard.append(LeaderboardEntry(
            id=team_id,
            name=stats["name"],
            total_score=round(stats["total_normalized_score"], 2),  # Use normalized score for ranking
            games_played=stats["games_played"],
            average_score=round(avg_normalized_score, 3)  # Show normalized average
        ))
    
    # Sort by normalized total score
    leaderboard.sort(key=lambda x: x.total_score, reverse=True)
    return leaderboard

@api_router.get("/groups/{group_id}/stats", response_model=GroupStats)
async def get_group_stats(group_id: str):
    """Get overall group statistics"""
    # Count players and teams
    player_count = await db.players.count_documents({"group_id": group_id})
    team_count = await db.teams.count_documents({"group_id": group_id})
    
    # Count total games
    session_count = await db.game_sessions.count_documents({"group_id": group_id})
    
    # Find most played game
    pipeline = [
        {"$match": {"group_id": group_id}},
        {"$group": {"_id": "$game_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    most_played_result = await db.game_sessions.aggregate(pipeline).to_list(1)
    most_played_game = most_played_result[0]["_id"] if most_played_result else None
    
    # Get top player
    top_player_doc = await db.players.find_one(
        {"group_id": group_id}, 
        sort=[("total_score", -1)]
    )
    
    top_player = None
    if top_player_doc:
        avg_score = top_player_doc["total_score"] / top_player_doc["games_played"] if top_player_doc["games_played"] > 0 else 0
        top_player = LeaderboardEntry(
            id=top_player_doc["id"],
            name=top_player_doc["player_name"],
            total_score=top_player_doc["total_score"],
            games_played=top_player_doc["games_played"],
            average_score=round(avg_score, 2)
        )
    
    return GroupStats(
        total_players=player_count,
        total_teams=team_count,
        total_games=session_count,
        most_played_game=most_played_game,
        top_player=top_player
    )

@api_router.get("/groups/{group_id}/games", response_model=List[str])
async def get_group_games(group_id: str):
    """Get list of unique game names played in a group"""
    pipeline = [
        {"$match": {"group_id": group_id}},
        {"$group": {"_id": "$game_name"}},
        {"$sort": {"_id": 1}}
    ]
    result = await db.game_sessions.aggregate(pipeline).to_list(1000)
    return [item["_id"] for item in result]

from fastapi.responses import Response

def convert_to_csv(data):
    """Convert export data to CSV format"""
    lines = []
    
    # Add group info header
    lines.append('GROUP INFORMATION')
    lines.append(f'Group Name,{data["group"]["group_name"]}')
    lines.append(f'Group Code,{data["group"]["group_code"]}')
    lines.append(f'Export Date,{data["group"]["export_date"].split("T")[0]}')
    lines.append('')
    
    # Add players section
    lines.append('PLAYERS')
    lines.append('Player Name,Emoji,Total Score,Games Played,Average Score,Joined Date')
    for player in data["players"]:
        avg_score = player["total_score"] / player["games_played"] if player["games_played"] > 0 else 0
        joined_date = player["created_date"].split("T")[0]
        lines.append(f'"{player["player_name"]}",{player["emoji"]},{player["total_score"]},{player["games_played"]},{avg_score:.2f},{joined_date}')
    lines.append('')
    
    # Add teams section
    if data["teams"]:
        lines.append('TEAMS')
        lines.append('Team Name,Players,Total Score,Games Played,Average Score,Created Date')
        for team in data["teams"]:
            player_names = []
            for player_id in team["player_ids"]:
                player = next((p for p in data["players"] if p["id"] == player_id), None)
                if player:
                    player_names.append(player["player_name"])
            players_str = "; ".join(player_names)
            avg_score = team["total_score"] / team["games_played"] if team["games_played"] > 0 else 0
            created_date = team["created_date"].split("T")[0]
            lines.append(f'"{team["team_name"]}","{players_str}",{team["total_score"]},{team["games_played"]},{avg_score:.2f},{created_date}')
        lines.append('')
    
    # Add game sessions section
    if data["game_sessions"]:
        lines.append('GAME SESSIONS')
        lines.append('Game Name,Date,Player/Team,Score,Type')
        for session in data["game_sessions"]:
            game_date = session["game_date"].split("T")[0]
            
            # Individual player scores
            for player_score in session.get("player_scores", []):
                lines.append(f'"{session["game_name"]}",{game_date},"{player_score["player_name"]}",{player_score["score"]},Individual')
            
            # Team scores
            for team_score in session.get("team_scores", []):
                lines.append(f'"{session["game_name"]}",{game_date},"{team_score["team_name"]}",{team_score["score"]},Team')
    
    return '\n'.join(lines)

@api_router.get("/groups/{group_id}/export")
async def export_group_data(group_id: str):
    """Export all group data as JSON"""
    # Verify group exists
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get all data
    players = await db.players.find({"group_id": group_id}).to_list(1000)
    teams = await db.teams.find({"group_id": group_id}).to_list(1000)
    sessions = await db.game_sessions.find({"group_id": group_id}).sort("game_date", 1).to_list(1000)
    
    # Format export data
    export_data = {
        "group": {
            "id": group["id"],
            "group_code": group["group_code"],
            "group_name": group["group_name"],
            "created_date": group["created_date"].isoformat() if isinstance(group["created_date"], datetime) else group["created_date"],
            "export_date": datetime.utcnow().isoformat()
        },
        "players": [
            {
                "id": player["id"],
                "player_name": player["player_name"],
                "emoji": player.get("emoji", "😀"),
                "total_score": player["total_score"],
                "games_played": player["games_played"],
                "created_date": player["created_date"].isoformat() if isinstance(player["created_date"], datetime) else player["created_date"]
            }
            for player in players
        ],
        "teams": [
            {
                "id": team["id"],
                "team_name": team["team_name"],
                "player_ids": team["player_ids"],
                "total_score": team["total_score"],
                "games_played": team["games_played"],
                "created_date": team["created_date"].isoformat() if isinstance(team["created_date"], datetime) else team["created_date"]
            }
            for team in teams
        ],
        "game_sessions": [
            {
                "id": session["id"],
                "game_name": session["game_name"],
                "game_date": session["game_date"].isoformat() if isinstance(session["game_date"], datetime) else session["game_date"],
                "player_scores": session.get("player_scores", []),
                "team_scores": session.get("team_scores", []),
                "created_date": session["created_date"].isoformat() if isinstance(session["created_date"], datetime) else session["created_date"]
            }
            for session in sessions
        ]
    }
    
    return export_data

@api_router.get("/groups/{group_id}/download-csv")
async def download_group_csv(group_id: str):
    """Download group data as CSV file"""
    # Verify group exists
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get all data
    players = await db.players.find({"group_id": group_id}).to_list(1000)
    teams = await db.teams.find({"group_id": group_id}).to_list(1000)
    sessions = await db.game_sessions.find({"group_id": group_id}).sort("game_date", 1).to_list(1000)
    
    # Format export data
    export_data = {
        "group": {
            "id": group["id"],
            "group_code": group["group_code"],
            "group_name": group["group_name"],
            "created_date": group["created_date"].isoformat() if isinstance(group["created_date"], datetime) else group["created_date"],
            "export_date": datetime.utcnow().isoformat()
        },
        "players": [
            {
                "id": player["id"],
                "player_name": player["player_name"],
                "emoji": player.get("emoji", "😀"),
                "total_score": player["total_score"],
                "games_played": player["games_played"],
                "created_date": player["created_date"].isoformat() if isinstance(player["created_date"], datetime) else player["created_date"]
            }
            for player in players
        ],
        "teams": [
            {
                "id": team["id"],
                "team_name": team["team_name"],
                "player_ids": team["player_ids"],
                "total_score": team["total_score"],
                "games_played": team["games_played"],
                "created_date": team["created_date"].isoformat() if isinstance(team["created_date"], datetime) else team["created_date"]
            }
            for team in teams
        ],
        "game_sessions": [
            {
                "id": session["id"],
                "game_name": session["game_name"],
                "game_date": session["game_date"].isoformat() if isinstance(session["game_date"], datetime) else session["game_date"],
                "player_scores": session.get("player_scores", []),
                "team_scores": session.get("team_scores", []),
                "created_date": session["created_date"].isoformat() if isinstance(session["created_date"], datetime) else session["created_date"]
            }
            for session in sessions
        ]
    }
    
    # Convert to CSV
    csv_content = convert_to_csv(export_data)
    
    # Create filename
    filename = f'{group["group_name"].replace(" ", "_")}_history_{datetime.utcnow().strftime("%Y-%m-%d")}.csv'
    
    # Return CSV file with download headers
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )

@api_router.get("/groups/{group_id}/download-json")
async def download_group_json(group_id: str):
    """Download group data as JSON file"""
    # Get the export data
    export_data = await export_group_data(group_id)
    
    # Get group name for filename
    group = await db.groups.find_one({"id": group_id})
    filename = f'{group["group_name"].replace(" ", "_")}_history_{datetime.utcnow().strftime("%Y-%m-%d")}.json'
    
    # Return JSON file with download headers
    import json
    json_content = json.dumps(export_data, indent=2)
    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/json; charset=utf-8"
        }
    )

from fastapi import UploadFile, File
import json

@api_router.post("/groups/{group_id}/import")
async def import_group_data(group_id: str, file: UploadFile = File(...)):
    """Import group data from uploaded JSON file to reset group"""
    # Verify group exists
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    try:
        # Read and parse uploaded file
        content = await file.read()
        import_data = json.loads(content.decode('utf-8'))
        
        # Validate import data structure
        required_keys = ["group", "players", "teams", "game_sessions"]
        if not all(key in import_data for key in required_keys):
            raise HTTPException(status_code=400, detail="Invalid import file format")
        
        # Clear existing data for this group
        await db.players.delete_many({"group_id": group_id})
        await db.teams.delete_many({"group_id": group_id})
        await db.game_sessions.delete_many({"group_id": group_id})
        
        # Import players
        if import_data["players"]:
            players_to_insert = []
            for player_data in import_data["players"]:
                player_doc = {
                    "id": player_data["id"],
                    "player_name": player_data["player_name"],
                    "group_id": group_id,
                    "emoji": player_data.get("emoji", "😀"),
                    "total_score": player_data["total_score"],
                    "games_played": player_data["games_played"],
                    "created_date": datetime.fromisoformat(player_data["created_date"].replace('Z', '+00:00'))
                }
                players_to_insert.append(player_doc)
            await db.players.insert_many(players_to_insert)
        
        # Import teams
        if import_data["teams"]:
            teams_to_insert = []
            for team_data in import_data["teams"]:
                team_doc = {
                    "id": team_data["id"],
                    "team_name": team_data["team_name"],
                    "group_id": group_id,
                    "player_ids": team_data["player_ids"],
                    "total_score": team_data["total_score"],
                    "games_played": team_data["games_played"],
                    "created_date": datetime.fromisoformat(team_data["created_date"].replace('Z', '+00:00'))
                }
                teams_to_insert.append(team_doc)
            await db.teams.insert_many(teams_to_insert)
        
        # Import game sessions
        if import_data["game_sessions"]:
            sessions_to_insert = []
            for session_data in import_data["game_sessions"]:
                session_doc = {
                    "id": session_data["id"],
                    "group_id": group_id,
                    "game_name": session_data["game_name"],
                    "game_date": datetime.fromisoformat(session_data["game_date"].replace('Z', '+00:00')),
                    "player_scores": session_data.get("player_scores", []),
                    "team_scores": session_data.get("team_scores", []),
                    "created_date": datetime.fromisoformat(session_data["created_date"].replace('Z', '+00:00'))
                }
                sessions_to_insert.append(session_doc)
            await db.game_sessions.insert_many(sessions_to_insert)
        
        return {
            "message": "Group data imported successfully",
            "imported": {
                "players": len(import_data["players"]),
                "teams": len(import_data["teams"]),
                "game_sessions": len(import_data["game_sessions"])
            }
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

def parse_csv(csv_content: str):
    """Parse CSV content back to structured data"""
    import csv
    from io import StringIO
    
    lines = csv_content.strip().split('\n')
    data = {
        "group": {},
        "players": [],
        "teams": [],
        "game_sessions": []
    }
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line == 'GROUP INFORMATION':
            i += 1
            # Parse group information
            while i < len(lines) and lines[i].strip() != '':
                if lines[i].startswith('Group Name,'):
                    data["group"]["group_name"] = lines[i].split(',', 1)[1].strip()
                elif lines[i].startswith('Group Code,'):
                    data["group"]["group_code"] = lines[i].split(',', 1)[1].strip()
                elif lines[i].startswith('Export Date,'):
                    data["group"]["export_date"] = lines[i].split(',', 1)[1].strip()
                i += 1
        
        elif line == 'PLAYERS':
            i += 2  # Skip header line
            # Parse players
            while i < len(lines) and lines[i].strip() != '':
                reader = csv.reader([lines[i]])
                row = next(reader)
                if len(row) >= 6:
                    player = {
                        "id": str(uuid.uuid4()),
                        "player_name": row[0],
                        "emoji": row[1],
                        "total_score": int(row[2]),
                        "games_played": int(row[3]),
                        "created_date": f"{row[5]}T00:00:00"
                    }
                    data["players"].append(player)
                i += 1
        
        elif line == 'TEAMS':
            i += 2  # Skip header line
            # Parse teams
            while i < len(lines) and lines[i].strip() != '':
                reader = csv.reader([lines[i]])
                row = next(reader)
                if len(row) >= 6:
                    # Find player IDs by names
                    player_names = row[1].split('; ')
                    player_ids = []
                    for name in player_names:
                        player = next((p for p in data["players"] if p["player_name"] == name.strip()), None)
                        if player:
                            player_ids.append(player["id"])
                    
                    team = {
                        "id": str(uuid.uuid4()),
                        "team_name": row[0],
                        "player_ids": player_ids,
                        "total_score": int(row[2]),
                        "games_played": int(row[3]),
                        "created_date": f"{row[5]}T00:00:00"
                    }
                    data["teams"].append(team)
                i += 1
        
        elif line == 'GAME SESSIONS':
            i += 2  # Skip header line
            # Parse game sessions
            sessions_dict = {}
            while i < len(lines) and lines[i].strip() != '':
                reader = csv.reader([lines[i]])
                row = next(reader)
                if len(row) >= 5:
                    game_name = row[0]
                    game_date = f"{row[1]}T00:00:00"
                    participant_name = row[2]
                    score = int(row[3])
                    score_type = row[4]
                    
                    # Create session key
                    session_key = f"{game_name}_{game_date}"
                    
                    if session_key not in sessions_dict:
                        sessions_dict[session_key] = {
                            "id": str(uuid.uuid4()),
                            "game_name": game_name,
                            "game_date": game_date,
                            "player_scores": [],
                            "team_scores": [],
                            "created_date": game_date
                        }
                    
                    if score_type == "Individual":
                        # Find player ID by name
                        player = next((p for p in data["players"] if p["player_name"] == participant_name), None)
                        if player:
                            sessions_dict[session_key]["player_scores"].append({
                                "player_id": player["id"],
                                "player_name": participant_name,
                                "score": score
                            })
                    elif score_type == "Team":
                        # Find team and its player IDs
                        team = next((t for t in data["teams"] if t["team_name"] == participant_name), None)
                        if team:
                            sessions_dict[session_key]["team_scores"].append({
                                "team_id": team["id"],
                                "team_name": participant_name,
                                "score": score,
                                "player_ids": team["player_ids"]
                            })
                i += 1
            
            data["game_sessions"] = list(sessions_dict.values())
        
        else:
            i += 1
    
    return data

@api_router.put("/groups/{group_id}/name")
async def update_group_name(group_id: str, request: dict):
    """Update group name"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    new_name = request.get("group_name", "").strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="Group name cannot be empty")
    
    if len(new_name) > 50:
        raise HTTPException(status_code=400, detail="Group name must be 50 characters or less")
    
    # Update the group name
    await db.groups.update_one(
        {"id": group_id},
        {"$set": {"group_name": new_name}}
    )
    
    return {
        "message": "Group name updated successfully",
        "group_name": new_name
    }

@api_router.post("/groups/{group_id}/import-csv")
async def import_group_csv(group_id: str, file: UploadFile = File(...)):
    """Import group data from uploaded CSV file to reset group"""
    # Verify group exists
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    try:
        # Read and parse uploaded CSV file
        content = await file.read()
        csv_content = content.decode('utf-8')
        import_data = parse_csv(csv_content)
        
        # Clear existing data for this group
        await db.players.delete_many({"group_id": group_id})
        await db.teams.delete_many({"group_id": group_id})
        await db.game_sessions.delete_many({"group_id": group_id})
        
        # Import players
        if import_data["players"]:
            players_to_insert = []
            for player_data in import_data["players"]:
                player_doc = {
                    "id": player_data["id"],
                    "player_name": player_data["player_name"],
                    "group_id": group_id,
                    "emoji": player_data.get("emoji", "😀"),
                    "total_score": player_data["total_score"],
                    "games_played": player_data["games_played"],
                    "created_date": datetime.fromisoformat(player_data["created_date"].replace('Z', '+00:00'))
                }
                players_to_insert.append(player_doc)
            await db.players.insert_many(players_to_insert)
        
        # Import teams
        if import_data["teams"]:
            teams_to_insert = []
            for team_data in import_data["teams"]:
                team_doc = {
                    "id": team_data["id"],
                    "team_name": team_data["team_name"],
                    "group_id": group_id,
                    "player_ids": team_data["player_ids"],
                    "total_score": team_data["total_score"],
                    "games_played": team_data["games_played"],
                    "created_date": datetime.fromisoformat(team_data["created_date"].replace('Z', '+00:00'))
                }
                teams_to_insert.append(team_doc)
            await db.teams.insert_many(teams_to_insert)
        
        # Import game sessions
        if import_data["game_sessions"]:
            sessions_to_insert = []
            for session_data in import_data["game_sessions"]:
                session_doc = {
                    "id": session_data["id"],
                    "group_id": group_id,
                    "game_name": session_data["game_name"],
                    "game_date": datetime.fromisoformat(session_data["game_date"].replace('Z', '+00:00')),
                    "player_scores": session_data.get("player_scores", []),
                    "team_scores": session_data.get("team_scores", []),
                    "created_date": datetime.fromisoformat(session_data["created_date"].replace('Z', '+00:00'))
                }
                sessions_to_insert.append(session_doc)
            await db.game_sessions.insert_many(sessions_to_insert)
        
        return {
            "message": "Group data imported successfully from CSV",
            "imported": {
                "players": len(import_data["players"]),
                "teams": len(import_data["teams"]),
                "game_sessions": len(import_data["game_sessions"])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV import failed: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
