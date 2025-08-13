#!/usr/bin/env python3
"""
Car Logo Guessing Game - Python Setup Script
Alternative to install.sh for Python-based installation
"""

import os
import sys
import subprocess
import json
import sqlite3
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=False)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python 3.7+ required. Found Python {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_packages():
    """Install required Python packages"""
    packages = [
        "flask>=2.3.0",
        "flask-cors>=4.0.0", 
        "flask-sqlalchemy>=3.0.0",
        "gunicorn>=21.0.0"
    ]
    
    for package in packages:
        if not run_command(f"pip install {package}", f"Installing {package.split('>=')[0]}"):
            return False
    return True

def setup_database():
    """Initialize the database with sample data"""
    print("🗄️ Setting up database...")
    
    # Sample logos data
    sample_logos = [
        {
            "name": "Toyota Logo",
            "image_url": "https://logos-world.net/wp-content/uploads/2020/04/Toyota-Logo.png",
            "correct_answer": "Toyota",
            "alternative_answers": ["Toyota Motor", "Toyota Motors"]
        },
        {
            "name": "BMW Logo",
            "image_url": "https://logos-world.net/wp-content/uploads/2020/04/BMW-Logo.png",
            "correct_answer": "BMW",
            "alternative_answers": ["Bayerische Motoren Werke", "BMW Group"]
        },
        {
            "name": "Mercedes-Benz Logo",
            "image_url": "https://logos-world.net/wp-content/uploads/2020/04/Mercedes-Benz-Logo.png",
            "correct_answer": "Mercedes-Benz",
            "alternative_answers": ["Mercedes", "Benz", "Mercedes Benz"]
        },
        {
            "name": "Audi Logo",
            "image_url": "https://logos-world.net/wp-content/uploads/2020/04/Audi-Logo.png",
            "correct_answer": "Audi",
            "alternative_answers": ["Audi AG"]
        },
        {
            "name": "Volkswagen Logo",
            "image_url": "https://logos-world.net/wp-content/uploads/2020/04/Volkswagen-Logo.png",
            "correct_answer": "Volkswagen",
            "alternative_answers": ["VW", "Volkswagen Group"]
        },
        {
            "name": "Ford Logo",
            "image_url": "https://logos-world.net/wp-content/uploads/2020/04/Ford-Logo.png",
            "correct_answer": "Ford",
            "alternative_answers": ["Ford Motor Company", "Ford Motors"]
        },
        {
            "name": "Honda Logo",
            "image_url": "https://logos-world.net/wp-content/uploads/2020/04/Honda-Logo.png",
            "correct_answer": "Honda",
            "alternative_answers": ["Honda Motor", "Honda Motors"]
        },
        {
            "name": "Nissan Logo",
            "image_url": "https://logos-world.net/wp-content/uploads/2020/04/Nissan-Logo.png",
            "correct_answer": "Nissan",
            "alternative_answers": ["Nissan Motor", "Nissan Motors"]
        },
        {
            "name": "Chevrolet Logo",
            "image_url": "https://logos-world.net/wp-content/uploads/2020/04/Chevrolet-Logo.png",
            "correct_answer": "Chevrolet",
            "alternative_answers": ["Chevy", "Chevrolet Motor"]
        },
        {
            "name": "Hyundai Logo",
            "image_url": "https://logos-world.net/wp-content/uploads/2020/04/Hyundai-Logo.png",
            "correct_answer": "Hyundai",
            "alternative_answers": ["Hyundai Motor", "Hyundai Motors"]
        }
    ]
    
    # Create data directory
    Path("data").mkdir(exist_ok=True)
    
    # Save sample logos
    with open("data/sample_logos.json", "w") as f:
        json.dump(sample_logos, f, indent=2)
    
    print("✅ Database setup completed")
    return True

def create_start_scripts():
    """Create startup scripts for different platforms"""
    
    # Create start script for Unix/Linux/macOS
    start_sh_content = '''#!/bin/bash

# Car Logo Guessing Game - Start Script

echo "🚗 Starting Car Logo Guessing Game..."

# Set environment variables
export SESSION_SECRET="car-logo-game-secret-$(date +%s)"
export DATABASE_URL="sqlite:///game.db"

# Start the server
echo "🌐 Server starting at http://localhost:5000"
echo "📊 Admin dashboard: http://localhost:5000/admin"
echo "🛑 Press Ctrl+C to stop the server"
echo

python3 main.py
'''

    # Create start script for Windows
    start_bat_content = '''@echo off
echo 🚗 Starting Car Logo Guessing Game...

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
'''
    
    # Write start scripts
    with open("start_game.sh", "w") as f:
        f.write(start_sh_content)
    
    with open("start_game.bat", "w") as f:
        f.write(start_bat_content)
    
    # Make shell script executable
    try:
        os.chmod("start_game.sh", 0o755)
    except:
        pass  # Windows doesn't support chmod
    
    print("✅ Start scripts created")
    return True

def main():
    """Main installation function"""
    print("🚗 Car Logo Guessing Game - Python Setup")
    print("=========================================")
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install required packages
    if not install_packages():
        print("❌ Failed to install packages")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("❌ Failed to setup database")
        sys.exit(1)
    
    # Create start scripts
    if not create_start_scripts():
        print("❌ Failed to create start scripts")
        sys.exit(1)
    
    print()
    print("🎉 Installation completed successfully!")
    print()
    print("📋 Next Steps:")
    print("===============")
    print("1. To start the game server:")
    print("   • On Linux/macOS: ./start_game.sh")
    print("   • On Windows: start_game.bat")
    print("   • Or directly: python3 main.py")
    print()
    print("2. Open your web browser and go to:")
    print("   • Game homepage: http://localhost:5000")
    print("   • Admin dashboard: http://localhost:5000/admin")
    print()
    print("3. Game Features:")
    print("   • Register teams from the homepage")
    print("   • Use admin dashboard to start games")
    print("   • Each round lasts 30 seconds")
    print("   • Teams compete to guess car logos")
    print()
    print("Happy gaming! 🏁")

if __name__ == "__main__":
    main()