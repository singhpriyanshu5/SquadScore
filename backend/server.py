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
    total_score: int = 0
    games_played: int = 0
    created_date: datetime = Field(default_factory=datetime.utcnow)

class PlayerCreate(BaseModel):
    player_name: str
    group_id: str

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
