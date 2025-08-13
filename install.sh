#!/bin/bash

# Car Logo Guessing Game - Installation Script
# This script will install and set up the game locally

set -e  # Exit on any error

echo "🚗 Car Logo Guessing Game - Installation Script"
echo "================================================"
echo

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.7 or higher and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    echo "Please install pip3 and try again."
    exit 1
fi

echo "✓ Found pip3"
echo

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix/Linux/macOS
    source venv/bin/activate
fi

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install required packages
echo "📥 Installing required packages..."
pip install flask flask-cors flask-sqlalchemy gunicorn

# Create directory structure if it doesn't exist
echo "📁 Setting up directory structure..."
mkdir -p data
mkdir -p static/css
mkdir -p static/js
mkdir -p templates

# Set environment variables
echo "🔧 Setting up environment variables..."
export SESSION_SECRET="car-logo-game-secret-$(date +%s)"
export DATABASE_URL="sqlite:///game.db"

# Initialize database and load sample data
echo "🗄️ Initializing database..."
python3 -c "
from app import app, db
import json
from models import Logo

with app.app_context():
    db.create_all()
    
    # Load sample logos if none exist
    if Logo.query.count() == 0:
        try:
            with open('data/sample_logos.json', 'r') as f:
                sample_logos = json.load(f)
                for logo_data in sample_logos:
                    logo = Logo(
                        name=logo_data['name'],
                        image_url=logo_data['image_url'],
                        correct_answer=logo_data['correct_answer'],
                        alternative_answers=json.dumps(logo_data.get('alternative_answers', []))
                    )
                    db.session.add(logo)
                db.session.commit()
                print(f'Loaded {len(sample_logos)} sample logos')
        except FileNotFoundError:
            print('Sample logos file not found, starting with empty logo database')
"

echo "✅ Database initialized successfully!"
echo

# Create startup script
echo "📝 Creating startup script..."
cat > start_game.sh << 'EOF'
#!/bin/bash

# Car Logo Guessing Game - Start Script

echo "🚗 Starting Car Logo Guessing Game..."

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Set environment variables
export SESSION_SECRET="car-logo-game-secret-$(date +%s)"
export DATABASE_URL="sqlite:///game.db"

# Start the server
echo "🌐 Server starting at http://localhost:5000"
echo "📊 Admin dashboard: http://localhost:5000/admin"
echo "🛑 Press Ctrl+C to stop the server"
echo

python3 main.py
EOF

# Create Windows startup script
cat > start_game.bat << 'EOF'
@echo off
echo 🚗 Starting Car Logo Guessing Game...

REM Activate virtual environment
call venv\Scripts\activate

REM Set environment variables
set SESSION_SECRET=car-logo-game-secret-%RANDOM%
set DATABASE_URL=sqlite:///game.db

REM Start the server
echo 🌐 Server starting at http://localhost:5000
echo 📊 Admin dashboard: http://localhost:5000/admin
echo 🛑 Press Ctrl+C to stop the server
echo.

python main.py
pause
EOF

# Make startup scripts executable
chmod +x start_game.sh

echo
echo "🎉 Installation completed successfully!"
echo
echo "📋 Next Steps:"
echo "==============="
echo "1. To start the game server:"
echo "   • On Linux/macOS: ./start_game.sh"
echo "   • On Windows: start_game.bat"
echo
echo "2. Open your web browser and go to:"
echo "   • Game homepage: http://localhost:5000"
echo "   • Admin dashboard: http://localhost:5000/admin"
echo
echo "3. Game Features:"
echo "   • Register teams from the homepage"
echo "   • Use admin dashboard to start games"
echo "   • Each round lasts 30 seconds"
echo "   • Teams compete to guess car logos"
echo
echo "4. Adding Custom Logos:"
echo "   • Use the admin dashboard to add new logos"
echo "   • Or edit data/sample_logos.json manually"
echo
echo "🔧 Troubleshooting:"
echo "==================="
echo "• If port 5000 is busy, the game will try other ports"
echo "• Database file (game.db) stores all game data"
echo "• Sample logos are loaded automatically on first run"
echo "• Check console output for any error messages"
echo
echo "📁 Project Structure:"
echo "====================="
echo "• app.py - Main Flask application"
echo "• models.py - Database models"
echo "• game_manager.py - Game logic"
echo "• templates/ - HTML templates"
echo "• static/ - CSS, JavaScript, images"
echo "• data/ - Sample logos and game data"
echo
echo "Happy gaming! 🏁"