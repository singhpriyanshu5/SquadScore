# SquadScore 🎲

**Track game scores with your squad**

SquadScore is a mobile-first board game score tracking application that helps groups of friends easily record, manage, and analyze their board game sessions. Built with fair scoring algorithms and intuitive design, it's the perfect companion for your game nights.

![SquadScore Demo](https://via.placeholder.com/600x300/007AFF/FFFFFF?text=SquadScore+Demo)

## ✨ Features

### 🎯 Core Functionality
- **Group Management**: Create or join groups with unique codes
- **Player Management**: Add players with custom emojis and track their progress
- **Team Support**: Create teams and automatically distribute scores to players
- **Game Recording**: Log individual and team-based game sessions
- **Smart Leaderboards**: Fair ranking system with normalized scoring across different games

### 📊 Advanced Analytics
- **Normalized Scoring**: Prevents high-scoring games from dominating leaderboards
- **Filtering**: View leaderboards by specific games, dates, or months  
- **Game History**: Complete record of all played sessions with delete functionality
- **Statistics Dashboard**: Group insights including top players and most played games

### 🔄 Data Management
- **Export/Import**: Backup and restore group data via CSV files
- **Cross-Platform**: Works seamlessly on iOS, Android, and web
- **Real-time Updates**: Automatic data refresh across all screens

### 🎨 User Experience
- **Mobile-First Design**: Optimized for touch interaction and thumb navigation
- **Intuitive Navigation**: Tab-based architecture with gesture support
- **Swipe Actions**: Quick access to edit/delete functions
- **Pull-to-Refresh**: Easy data updates with familiar mobile patterns

## 🚀 Tech Stack

### Frontend
- **[Expo](https://expo.dev/)** - React Native framework for cross-platform development
- **[React Native](https://reactnative.dev/)** - Mobile app framework
- **[TypeScript](https://www.typescriptlang.org/)** - Type-safe JavaScript
- **[Expo Router](https://docs.expo.dev/router/introduction/)** - File-based navigation system

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[MongoDB](https://www.mongodb.com/)** - NoSQL database for flexible data storage
- **[Pydantic](https://pydantic.dev/)** - Data validation and serialization

### Development
- **[ESLint](https://eslint.org/)** - JavaScript/TypeScript linting
- **[Ruff](https://github.com/astral-sh/ruff)** - Python linting and formatting

## 📱 Installation

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.8+
- MongoDB (local or cloud instance)
- Expo CLI: `npm install -g @expo/cli`

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/squadscore.git
   cd squadscore
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Create .env file
   echo "MONGO_URL=mongodb://localhost:27017/squadscore" > .env
   
   # Start the server
   uvicorn server:app --reload --host 0.0.0.0 --port 8001
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   yarn install
   
   # Create .env file
   echo "EXPO_PUBLIC_BACKEND_URL=http://localhost:8001" > .env
   
   # Start the development server
   expo start
   ```

4. **Open the app**
   - Scan the QR code with Expo Go app (iOS/Android)
   - Press 'w' to open in web browser
   - Press 'i' for iOS simulator
   - Press 'a' for Android emulator

## 🎮 Usage Guide

### Getting Started
1. **Create a Group**: Tap "Create New Group" and enter a group name
2. **Invite Friends**: Share your unique group code with other players
3. **Add Players**: Add players with names and fun emojis
4. **Record Games**: Start logging your board game sessions

### Recording Scores
- **Individual Games**: Enter scores for each player directly
- **Team Games**: Create teams and scores are automatically distributed
- **Game Selection**: Choose from previous games or add new ones

### Viewing Results
- **Leaderboards**: See fair rankings with normalized scoring
- **Game History**: Browse all recorded sessions with filtering options
- **Statistics**: Check group insights and top performers

### Data Management
- **Export**: Download your group's complete history as CSV
- **Import**: Restore data from previously exported files
- **Edit**: Modify group names, player details, or remove unwanted sessions

## 📚 API Documentation

### Base URL
```
http://localhost:8001/api
```

### Key Endpoints

#### Groups
- `POST /groups` - Create a new group
- `GET /groups/{group_id}` - Get group details
- `PUT /groups/{group_id}/name` - Update group name
- `GET /groups/{group_id}/stats` - Get group statistics

#### Players
- `GET /groups/{group_id}/players-normalized` - Get players with normalized scores
- `POST /players` - Add a new player
- `PUT /players/{player_id}` - Update player details
- `DELETE /players/{player_id}` - Remove a player

#### Game Sessions
- `POST /game-sessions` - Record a new game session
- `GET /groups/{group_id}/game-sessions` - Get game history
- `DELETE /game-sessions/{session_id}` - Delete a game session

#### Leaderboards
- `GET /groups/{group_id}/leaderboard/players` - Player rankings
- `GET /groups/{group_id}/leaderboard/teams` - Team rankings

#### Data Export/Import
- `GET /groups/{group_id}/download-csv` - Export group data
- `POST /groups/{group_id}/import-csv` - Import group data

For complete API documentation, visit `http://localhost:8001/docs` when running the backend.

## 🔧 Development

### Project Structure
```
squadscore/
├── frontend/                 # Expo React Native app
│   ├── app/                 # File-based routing screens
│   │   ├── index.tsx        # Home screen
│   │   └── group/           # Group-related screens
│   ├── assets/              # Static assets
│   └── package.json         # Frontend dependencies
│
├── backend/                 # FastAPI server
│   ├── server.py           # Main application file
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables
│
└── README.md              # This file
```

### Environment Variables

#### Frontend (.env)
```env
EXPO_PUBLIC_BACKEND_URL=http://localhost:8001
```

#### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017/squadscore
```

### Running Tests
```bash
# Backend linting
ruff check backend/

# Frontend linting
cd frontend && yarn lint
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit with clear messages: `git commit -m 'Add amazing feature'`
5. Push to your branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Contribution Guidelines
- Follow the existing code style and conventions
- Add tests for new features
- Update documentation as needed
- Ensure mobile-first design principles
- Test on multiple platforms (iOS, Android, Web)

## 🐛 Known Issues

- iOS file sharing requires iOS 13+
- Large group exports (1000+ games) may take several seconds
- Offline functionality not yet implemented

## 🔮 Roadmap

- [ ] Offline mode with sync capabilities
- [ ] Advanced statistics and charts
- [ ] Game suggestions based on group preferences
- [ ] Social features and group messaging
- [ ] Tournament bracket management
- [ ] Custom scoring rules per game
- [ ] Photo attachments for game sessions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ for the board gaming community
- Icons by [Ionicons](https://ionic.io/ionicons)
- Inspired by countless game nights with friends

## 📞 Support

- 🐛 **Bug Reports**: [Create an issue](https://github.com/yourusername/squadscore/issues)
- 💡 **Feature Requests**: [Start a discussion](https://github.com/yourusername/squadscore/discussions)
- 📧 **Contact**: [your.email@example.com](mailto:your.email@example.com)

---

**Made with 🎲 by the SquadScore team**

*Keep score, build memories!*
=======

#  SquadScore

**Track your game night glory with friends.**

SquadScore is a simple, fun, and mobile-friendly app that helps you and your friends keep track of scores from your board game nights. No more scribbled notes or lost scorecards - everything lives in one shared place.

---

## ✨ What you can do with SquadScore

* **Create a Group**
  Start a private group for your game night crew and invite your friends to join.

* **Add Players & Teams**
  Keep track of everyone playing. For team games, add team names and link players to them.

* **Log Games & Scores**
  Enter the game name, date, and scores after each session.

  * If it’s a **team game**, you only need to enter one team score — SquadScore will automatically distribute points to all team members.

* **View Leaderboards**
  See who’s topping the charts in your group with an always-up-to-date leaderboard.

* **Get Insights**
  Discover fun stats like:

  * Top-scoring players
  * Most-played games
  * Win streaks and bragging rights

---

## 🎯 Why SquadScore?

* **Quick & simple:** Designed to make score entry super easy, even in the middle of a game night.
* **Shared experience:** Everyone in the group sees the same data, no need to message results around.
* **Game night history:** Look back at past sessions and relive your best wins.

---

## 🕹️ Perfect for…

Catan, Ticket to Ride, Azul, Monopoly, Poker night, trivia battles — or any game where you keep score.

---

## 🚀 Getting Started

1. Create or join a group.
2. Add your players (or teams).
3. Start logging game sessions and watch the leaderboard update instantly.


---
