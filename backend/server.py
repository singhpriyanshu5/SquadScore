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
@api_router.get("/groups/{group_id}/leaderboard/players", response_model=List[LeaderboardEntry])
async def get_player_leaderboard(
    group_id: str,
    game_name: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None
):
    """Get player leaderboard for a group with optional filters"""
    if game_name or year or month:
        # Get filtered game sessions first
        session_filter = {"group_id": group_id}
        if game_name:
            session_filter["game_name"] = {"$regex": game_name, "$options": "i"}
        if year or month:
            date_filter = {}
            if year:
                if month:
                    # Specific month and year
                    from datetime import datetime
                    start_date = datetime(year, month, 1)
                    if month == 12:
                        end_date = datetime(year + 1, 1, 1)
                    else:
                        end_date = datetime(year, month + 1, 1)
                    date_filter = {"$gte": start_date, "$lt": end_date}
                else:
                    # Entire year
                    from datetime import datetime
                    start_date = datetime(year, 1, 1)
                    end_date = datetime(year + 1, 1, 1)
                    date_filter = {"$gte": start_date, "$lt": end_date}
            session_filter["game_date"] = date_filter

        # Get sessions matching filters
        sessions = await db.game_sessions.find(session_filter).to_list(1000)
        
        # Calculate filtered scores
        player_stats = {}
        for session in sessions:
            # Process individual player scores
            for player_score in session.get("player_scores", []):
                player_id = player_score["player_id"]
                if player_id not in player_stats:
                    player_stats[player_id] = {
                        "name": player_score["player_name"],
                        "total_score": 0,
                        "games_played": 0
                    }
                player_stats[player_id]["total_score"] += player_score["score"]
                player_stats[player_id]["games_played"] += 1
            
            # Process team scores (distributed to players)
            for team_score in session.get("team_scores", []):
                if team_score.get("player_ids"):
                    score_per_player = team_score["score"] // len(team_score["player_ids"])
                    for player_id in team_score["player_ids"]:
                        if player_id not in player_stats:
                            # Get player name
                            player = await db.players.find_one({"id": player_id})
                            player_name = player["player_name"] if player else "Unknown"
                            player_stats[player_id] = {
                                "name": player_name,
                                "total_score": 0,
                                "games_played": 0
                            }
                        player_stats[player_id]["total_score"] += score_per_player
                        player_stats[player_id]["games_played"] += 1
        
        # Convert to leaderboard format
        leaderboard = []
        for player_id, stats in player_stats.items():
            avg_score = stats["total_score"] / stats["games_played"] if stats["games_played"] > 0 else 0
            leaderboard.append(LeaderboardEntry(
                id=player_id,
                name=stats["name"],
                total_score=stats["total_score"],
                games_played=stats["games_played"],
                average_score=round(avg_score, 2)
            ))
        
        # Sort by total score
        leaderboard.sort(key=lambda x: x.total_score, reverse=True)
        return leaderboard
    
    else:
        # Original unfiltered logic
        players = await db.players.find({"group_id": group_id}).sort("total_score", -1).to_list(1000)
        
        leaderboard = []
        for player in players:
            avg_score = player["total_score"] / player["games_played"] if player["games_played"] > 0 else 0
            leaderboard.append(LeaderboardEntry(
                id=player["id"],
                name=player["player_name"],
                total_score=player["total_score"],
                games_played=player["games_played"],
                average_score=round(avg_score, 2)
            ))
        
        return leaderboard

@api_router.get("/groups/{group_id}/leaderboard/teams", response_model=List[LeaderboardEntry])
async def get_team_leaderboard(group_id: str):
    """Get team leaderboard for a group"""
    teams = await db.teams.find({"group_id": group_id}).sort("total_score", -1).to_list(1000)
    
    leaderboard = []
    for team in teams:
        avg_score = team["total_score"] / team["games_played"] if team["games_played"] > 0 else 0
        leaderboard.append(LeaderboardEntry(
            id=team["id"],
            name=team["team_name"],
            total_score=team["total_score"],
            games_played=team["games_played"],
            average_score=round(avg_score, 2)
        ))
    
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
