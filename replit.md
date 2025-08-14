# Overview

This is a multiplayer online car logo guessing game built with Flask and vanilla JavaScript. Teams compete in real-time to identify car brands from their logos during timed rounds. The system supports multiple teams playing simultaneously from different locations, with features for team registration, live scoring, round management, and admin controls.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The client-side is built with vanilla JavaScript, HTML, and Bootstrap for responsive design. The architecture uses a polling-based approach for real-time updates, with separate JavaScript classes for team (`TeamDashboard`) and admin (`AdminDashboard`) interfaces. The frontend communicates with the backend through RESTful API calls and updates the UI every 2 seconds to maintain real-time game state synchronization.

## Backend Architecture
The backend uses Flask as the web framework with a modular design pattern. Core components include:
- **Flask Application (`app.py`)**: Main application entry point with route definitions and request handling
- **Game Manager (`game_manager.py`)**: Encapsulates game logic including round management, timer tracking, and logo selection
- **Models (`models.py`)**: SQLAlchemy ORM models for data persistence
- **Templates**: Jinja2 templates for server-side rendering of HTML pages

The architecture follows RESTful principles with clear separation between game logic, data models, and web presentation layers.

## Data Storage
Uses SQLite as the primary database with SQLAlchemy ORM for data modeling. The database schema includes:
- **Teams**: Store team information, member lists (as JSON), and scores
- **Logos**: Car logo images, correct answers, and alternative acceptable answers
- **Games**: Track game sessions, current rounds, and timing information
- **Guesses**: Log all team guesses for auditing and scoring

The system initializes with sample logo data from a JSON file and supports dynamic logo management through the admin interface.

## Game Logic Design
Implements a question-based round system where:
- Each round contains exactly 10 questions
- Each question displays a randomly selected logo for exactly 30 seconds
- Questions automatically advance after 30 seconds
- After 10 questions, the round completes and waits for admin to send "NEXT ROUND"
- Total rounds = total available logos ÷ 10 (rounded up)
- Teams can submit case-insensitive guesses with support for alternative correct answers
- Scoring is tracked in real-time with immediate feedback
- Logo selection prevents repeats within the same game session
- Automatic question progression with admin-controlled round advancement

## Security and Configuration
Basic security measures include:
- Environment-based configuration for secrets and database URLs
- CORS enabled for cross-origin requests
- Proxy fix middleware for proper request handling
- Input validation and error handling throughout the application

# External Dependencies

## Core Web Framework
- **Flask**: Primary web framework for handling HTTP requests and routing
- **Flask-CORS**: Enables cross-origin resource sharing for API endpoints
- **Flask-SQLAlchemy**: ORM integration for database operations

## Database Technology
- **SQLite**: Embedded database for data persistence (configurable via DATABASE_URL environment variable)
- **SQLAlchemy**: Database toolkit and ORM for Python

## Frontend Libraries
- **Bootstrap**: CSS framework for responsive design and UI components
- **Font Awesome**: Icon library for enhanced visual elements

## External Logo Resources
The application references car logo images hosted on external services (logos-world.net) for the sample data. The system is designed to work with any publicly accessible image URLs.

## Development and Deployment
- **Werkzeug**: WSGI utilities including ProxyFix middleware for deployment
- Environment variable support for configuration management
- JSON-based sample data loading for initial setup