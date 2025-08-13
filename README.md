# Car Logo Guessing Game

A multiplayer online car logo guessing game built with Flask and vanilla JavaScript. Teams compete to identify car brands from their logos in timed rounds.

## Features

### Game Mechanics
- **Multiplayer Support**: Multiple teams can play simultaneously from different locations
- **Timed Rounds**: Each round lasts 30 seconds with real-time countdown
- **Real-time Scoring**: Live leaderboard updates during gameplay
- **Case-insensitive Guessing**: Accepts variations of correct answers
- **Alternative Answers**: Support for multiple correct answers per logo

### Team Features
- **Team Registration**: Teams register with team name and member list
- **Live Dashboard**: Real-time game status and score updates
- **Guess Submission**: Simple form-based guess submission
- **Visual Feedback**: Immediate feedback on guess correctness

### Admin Features
- **Game Control**: Start games, advance rounds, end games
- **Logo Management**: Add, view, and delete car logos
- **Live Monitoring**: Real-time view of all teams and scores
- **Alternative Answers**: Manage multiple correct answers per logo

### Technical Features
- **SQLite Database**: Persistent storage for teams, games, and logos
- **RESTful API**: Clean API endpoints for all game operations
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Polling-based updates every 2 seconds
- **Error Handling**: Comprehensive error handling and validation

## Installation and Setup

### Prerequisites
- Python 3.7+
- Flask
- Flask-CORS
- Flask-SQLAlchemy

### Quick Start

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install flask flask-cors flask-sqlalchemy
   ```

3. **Set environment variables** (optional):
   ```bash
   export SESSION_SECRET="your-secret-key-here"
   export DATABASE_URL="sqlite:///game.db"
   