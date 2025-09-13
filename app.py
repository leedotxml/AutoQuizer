import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, Team, Logo, Game, Guess
from game_manager import GameManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS for all routes
CORS(app)

# Configure database - temporarily use SQLite to avoid endpoint issues
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///game.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Initialize game manager
game_manager = GameManager()

# Create tables and load sample data
with app.app_context():
    db.create_all()
    
    # Handle database schema migration for new game features
    try:
        # Check if we need to add new columns
        from sqlalchemy import text
        result = db.session.execute(text("PRAGMA table_info(game)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'current_question' not in columns:
            # Add new columns for question tracking
            db.session.execute(text("ALTER TABLE game ADD COLUMN current_question INTEGER DEFAULT 1"))
            db.session.execute(text("ALTER TABLE game ADD COLUMN questions_per_round INTEGER DEFAULT 10"))
            db.session.execute(text("ALTER TABLE game ADD COLUMN used_logo_ids TEXT"))
            db.session.commit()
            logging.info("Database schema updated with new game features")
    except Exception as e:
        logging.warning(f"Schema migration skipped: {e}")
    
    # Load sample logos if none exist
    try:
        logo_count = Logo.query.count()
        if logo_count == 0:
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
                    logging.info(f"Loaded {len(sample_logos)} sample logos")
            except FileNotFoundError:
                logging.warning("Sample logos file not found, starting with empty logo database")
    except Exception as e:
        logging.warning(f"Could not check logo count: {e}")
        db.session.rollback()

@app.route('/')
def index():
    """Landing page with team registration"""
    return render_template('index.html')

@app.route('/team/<team_name>')
def team_dashboard(team_name):
    """Team dashboard for playing the game"""
    team = Team.query.filter_by(name=team_name).first()
    if not team:
        flash('Team not found. Please register first.', 'error')
        return redirect(url_for('index'))
    return render_template('team.html', team=team)

@app.route('/admin')
def admin():
    """Admin login page"""
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Protected admin dashboard"""
    return render_template('admin.html')

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin login with password"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        # Simple password check (you can change this)
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            return jsonify({'success': True, 'redirect_url': '/admin/dashboard'})
        else:
            return jsonify({'error': 'Invalid password'}), 401
            
    except Exception as e:
        logging.error(f"Admin login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# API Endpoints

@app.route('/api/register_team', methods=['POST'])
def register_team():
    """Register a new team"""
    try:
        data = request.get_json()
        team_name = data.get('team_name', '').strip()
        members = data.get('members', [])
        
        if not team_name:
            return jsonify({'error': 'Team name is required'}), 400
        
        if not members or len(members) == 0:
            return jsonify({'error': 'At least one team member is required'}), 400
        
        # Check if team already exists
        existing_team = Team.query.filter_by(name=team_name).first()
        if existing_team:
            return jsonify({'error': 'Team name already exists'}), 400
        
        # Create new team
        team = Team(
            name=team_name,
            members=json.dumps(members),
            score=0
        )
        db.session.add(team)
        db.session.commit()
        
        logging.info(f"Team '{team_name}' registered with {len(members)} members")
        return jsonify({
            'success': True,
            'team_id': team.id,
            'team_name': team.name,
            'redirect_url': url_for('team_dashboard', team_name=team.name)
        })
        
    except Exception as e:
        logging.error(f"Error registering team: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/submit_guess', methods=['POST'])
def submit_guess():
    """Submit a guess for the current round"""
    try:
        data = request.get_json()
        team_name = data.get('team_name')
        guess = data.get('guess', '').strip().lower()
        
        if not team_name or not guess:
            return jsonify({'error': 'Team name and guess are required'}), 400
        
        team = Team.query.filter_by(name=team_name).first()
        if not team:
            return jsonify({'error': 'Team not found'}), 404
        
        game = Game.query.filter_by(status='active').first()
        if not game:
            return jsonify({'error': 'No active game'}), 400
        
        # Simple approach: Allow one guess per question per team per game
        # Check based on current logo ID to track questions
        logo_id_str = str(game.current_logo_id) 
        existing_guess = Guess.query.filter(
            Guess.team_id == team.id,
            Guess.game_id == game.id,
            Guess.round_number == game.current_round,
            Guess.guess.like(f'%{logo_id_str}%')
        ).first()
        
        if existing_guess:
            return jsonify({'error': 'Team has already submitted a guess for this question'}), 400
        
        # Get current logo
        logo = Logo.query.get(game.current_logo_id)
        if not logo:
            return jsonify({'error': 'No logo found for current round'}), 400
        
        # Check if guess is correct
        correct_answers = [logo.correct_answer.lower()]
        if logo.alternative_answers:
            try:
                alternative_answers = json.loads(logo.alternative_answers)
                correct_answers.extend([ans.lower() for ans in alternative_answers])
            except:
                pass
        
        is_correct = guess in correct_answers
        
        # Save guess with logo ID to track questions properly
        guess_with_id = f"{guess}_{game.current_logo_id}"
        guess_obj = Guess(
            team_id=team.id,
            game_id=game.id,
            round_number=game.current_round,
            guess=guess_with_id,
            is_correct=is_correct,
            timestamp=datetime.utcnow()
        )
        db.session.add(guess_obj)
        
        # Update team score if correct
        if is_correct:
            team.score += 1
        
        db.session.commit()
        
        logging.info(f"Team '{team_name}' guessed '{guess}' - {'Correct' if is_correct else 'Incorrect'}")
        return jsonify({
            'success': True,
            'is_correct': is_correct,
            'correct_answer': logo.correct_answer if is_correct else None
        })
        
    except Exception as e:
        logging.error(f"Error submitting guess: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/status/<team_name>')
def get_team_status(team_name):
    """Get current game status for a team"""
    try:
        team = Team.query.filter_by(name=team_name).first()
        if not team:
            return jsonify({'error': 'Team not found'}), 404
        
        game = Game.query.filter_by(status='active').first()
        
        if not game:
            return jsonify({
                'game_status': 'waiting',
                'team_score': team.score,
                'message': 'Waiting for game to start...'
            })
        
        # Get current logo
        logo = None
        if game.current_logo_id:
            logo = Logo.query.get(game.current_logo_id)
        
        # Check if team has guessed for this specific logo 
        has_guessed = False
        if game and logo:
            logo_id_str = str(game.current_logo_id)
            existing_guess = Guess.query.filter(
                Guess.team_id == team.id,
                Guess.game_id == game.id,
                Guess.round_number == game.current_round,
                Guess.guess.like(f'%{logo_id_str}%')
            ).first()
            has_guessed = existing_guess is not None
        
        return jsonify({
            'game_status': game.status,
            'current_round': game.current_round,
            'total_rounds': game.total_rounds,
            'current_question': getattr(game, 'current_question', 1),
            'questions_per_round': getattr(game, 'questions_per_round', 10),
            'team_score': team.score,
            'logo_url': logo.image_url if logo else None,
            'has_guessed': has_guessed,
            'round_active': game.status == 'active'
        })
        
    except Exception as e:
        logging.error(f"Error getting team status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/status')
def get_admin_status():
    """Get current game status for admin"""
    try:
        game = Game.query.filter_by(status='active').first()
        teams = Team.query.order_by(Team.score.desc()).all()
        logos = Logo.query.all()
        
        team_data = []
        for team in teams:
            members = []
            try:
                members = json.loads(team.members)
            except:
                pass
            
            team_data.append({
                'id': team.id,
                'name': team.name,
                'members': members,
                'score': team.score
            })
        
        logo_data = []
        for logo in logos:
            alternatives = []
            try:
                alternatives = json.loads(logo.alternative_answers or '[]')
            except:
                pass
            
            logo_data.append({
                'id': logo.id,
                'name': logo.name,
                'image_url': logo.image_url,
                'correct_answer': logo.correct_answer,
                'alternative_answers': alternatives
            })
        
        game_data = None
        if game:
            current_logo = None
            if game.current_logo_id:
                logo = Logo.query.get(game.current_logo_id)
                if logo:
                    current_logo = {
                        'id': logo.id,
                        'name': logo.name,
                        'image_url': logo.image_url,
                        'correct_answer': logo.correct_answer
                    }
            
            game_data = {
                'id': game.id,
                'status': game.status,
                'current_round': game.current_round,
                'total_rounds': game.total_rounds,
                'current_question': getattr(game, 'current_question', 1),
                'questions_per_round': getattr(game, 'questions_per_round', 10),
                'current_logo': current_logo,
                'round_active': game.status == 'active'
            }
        
        return jsonify({
            'game': game_data,
            'teams': team_data,
            'logos': logo_data
        })
        
    except Exception as e:
        logging.error(f"Error getting admin status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/start_game', methods=['POST'])
def start_game():
    """Start a new game"""
    try:
        # End any existing active games
        active_games = Game.query.filter_by(status='active').all()
        for game in active_games:
            game.status = 'finished'
        
        # Reset all team scores
        teams = Team.query.all()
        for team in teams:
            team.score = 0
        
        # Get available logos
        logos = Logo.query.all()
        if not logos:
            return jsonify({'error': 'No logos available. Please add logos first.'}), 400
        
        # Create new game - single round with all questions
        questions_per_round = len(logos)  # All questions in one round
        total_rounds = 1  # Only one round
        game = Game(
            status='active',
            current_round=1,
            total_rounds=total_rounds,
            current_question=1,
            questions_per_round=questions_per_round,
            used_logo_ids='[]',
            created_at=datetime.utcnow()
        )
        db.session.add(game)
        db.session.flush()  # Get the game ID
        
        # Start first round
        game_manager.start_round(game, logos)
        
        db.session.commit()
        
        logging.info(f"New game started with {total_rounds} rounds")
        return jsonify({'success': True, 'game_id': game.id})
        
    except Exception as e:
        logging.error(f"Error starting game: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/next_round', methods=['POST'])
def next_round():
    """Advance to the next round (admin sends 'NEXT ROUND')"""
    try:
        game = Game.query.filter_by(status='round_complete').first()
        if not game:
            return jsonify({'error': 'No round waiting to advance'}), 400
        
        if game.current_round >= game.total_rounds:
            # End the game
            game.status = 'finished'
            db.session.commit()
            return jsonify({'success': True, 'game_finished': True})
        
        # Advance to next round
        game.current_round += 1
        logos = Logo.query.all()
        game_manager.start_round(game, logos)
        
        db.session.commit()
        
        logging.info(f"Advanced to round {game.current_round}")
        return jsonify({'success': True, 'current_round': game.current_round})
        
    except Exception as e:
        logging.error(f"Error advancing round: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/next_question', methods=['POST'])
def next_question():
    """Manually advance to the next question"""
    try:
        game = Game.query.filter_by(status='active').first()
        if not game:
            return jsonify({'error': 'No active game'}), 400
        
        logos = Logo.query.all()
        result = game_manager.advance_question(game, logos)
        
        db.session.commit()
        
        if game.status == 'finished':
            logging.info(f"Game completed with all questions answered")
            return jsonify({'success': True, 'game_finished': True})
        else:
            logging.info(f"Advanced to question {game.current_question} in round {game.current_round}")
            return jsonify({'success': True, 'current_question': game.current_question})
        
    except Exception as e:
        logging.error(f"Error advancing question: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/logos', methods=['GET'])
def get_logos():
    """Get all logos"""
    try:
        logos = Logo.query.all()
        logo_data = []
        
        for logo in logos:
            alternatives = []
            try:
                alternatives = json.loads(logo.alternative_answers or '[]')
            except:
                pass
            
            logo_data.append({
                'id': logo.id,
                'name': logo.name,
                'image_url': logo.image_url,
                'correct_answer': logo.correct_answer,
                'alternative_answers': alternatives
            })
        
        return jsonify({'logos': logo_data})
        
    except Exception as e:
        logging.error(f"Error getting logos: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/logos', methods=['POST'])
def add_logo():
    """Add a new logo"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        image_url = data.get('image_url', '').strip()
        correct_answer = data.get('correct_answer', '').strip()
        alternative_answers = data.get('alternative_answers', [])
        
        if not all([name, image_url, correct_answer]):
            return jsonify({'error': 'Name, image URL, and correct answer are required'}), 400
        
        logo = Logo(
            name=name,
            image_url=image_url,
            correct_answer=correct_answer,
            alternative_answers=json.dumps(alternative_answers)
        )
        db.session.add(logo)
        db.session.commit()
        
        logging.info(f"Added new logo: {name}")
        return jsonify({'success': True, 'logo_id': logo.id})
        
    except Exception as e:
        logging.error(f"Error adding logo: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/logos/<int:logo_id>', methods=['DELETE'])
def delete_logo(logo_id):
    """Delete a logo"""
    try:
        logo = Logo.query.get(logo_id)
        if not logo:
            return jsonify({'error': 'Logo not found'}), 404
        
        db.session.delete(logo)
        db.session.commit()
        
        logging.info(f"Deleted logo: {logo.name}")
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Error deleting logo: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/stop_game', methods=['POST'])
def stop_game():
    """Stop the current game immediately"""
    try:
        game = Game.query.filter_by(status='active').first()
        if not game:
            return jsonify({'error': 'No active game to stop'}), 400
        
        # Stop the game immediately
        game.status = 'finished'
        game.current_logo_id = None
        game.round_start_time = None
        
        db.session.commit()
        
        logging.info("Game stopped by admin")
        return jsonify({'success': True, 'message': 'Game stopped successfully'})
        
    except Exception as e:
        logging.error(f"Error stopping game: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/restart_game', methods=['POST'])
def restart_game():
    """Restart the game - reset everything and start fresh"""
    try:
        # End any existing games
        active_games = Game.query.all()
        for game in active_games:
            game.status = 'finished'
        
        # Reset all team scores
        teams = Team.query.all()
        for team in teams:
            team.score = 0
        
        # Clear all guesses
        guesses = Guess.query.all()
        for guess in guesses:
            db.session.delete(guess)
        
        # Get available logos
        logos = Logo.query.all()
        if not logos:
            return jsonify({'error': 'No logos available. Please add logos first.'}), 400
        
        # Create new game - single round with all questions
        questions_per_round = len(logos)  # All questions in one round
        total_rounds = 1  # Only one round
        game = Game(
            status='active',
            current_round=1,
            total_rounds=total_rounds,
            current_question=1,
            questions_per_round=questions_per_round,
            used_logo_ids='[]',
            created_at=datetime.utcnow()
        )
        db.session.add(game)
        db.session.flush()  # Get the game ID
        
        # Start first round
        game_manager.start_round(game, logos)
        
        db.session.commit()
        
        logging.info("Game restarted by admin")
        return jsonify({'success': True, 'game_id': game.id, 'message': 'Game restarted successfully'})
        
    except Exception as e:
        logging.error(f"Error restarting game: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
