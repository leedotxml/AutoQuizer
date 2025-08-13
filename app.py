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

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///game.db")
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
                logging.info(f"Loaded {len(sample_logos)} sample logos")
        except FileNotFoundError:
            logging.warning("Sample logos file not found, starting with empty logo database")

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
def admin_dashboard():
    """Admin dashboard for game management"""
    return render_template('admin.html')

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
        
        # Check if team already guessed for this round
        existing_guess = Guess.query.filter_by(
            team_id=team.id,
            game_id=game.id,
            round_number=game.current_round
        ).first()
        
        if existing_guess:
            return jsonify({'error': 'Team has already submitted a guess for this round'}), 400
        
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
        
        # Save guess
        guess_obj = Guess(
            team_id=team.id,
            game_id=game.id,
            round_number=game.current_round,
            guess=guess,
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
        
        # Check if team has guessed this round
        has_guessed = False
        if game and logo:
            existing_guess = Guess.query.filter_by(
                team_id=team.id,
                game_id=game.id,
                round_number=game.current_round
            ).first()
            has_guessed = existing_guess is not None
        
        # Calculate time remaining
        time_remaining = 0
        if game.round_start_time:
            elapsed = (datetime.utcnow() - game.round_start_time).total_seconds()
            time_remaining = max(0, 30 - elapsed)
        
        return jsonify({
            'game_status': game.status,
            'current_round': game.current_round,
            'total_rounds': game.total_rounds,
            'team_score': team.score,
            'logo_url': logo.image_url if logo else None,
            'has_guessed': has_guessed,
            'time_remaining': int(time_remaining),
            'round_active': time_remaining > 0
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
            # Calculate time remaining
            time_remaining = 0
            if game.round_start_time:
                elapsed = (datetime.utcnow() - game.round_start_time).total_seconds()
                time_remaining = max(0, 30 - elapsed)
            
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
                'current_logo': current_logo,
                'time_remaining': int(time_remaining),
                'round_active': time_remaining > 0
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
        
        # Create new game
        total_rounds = min(len(logos), 3)  # Max 3 rounds or number of logos
        game = Game(
            status='active',
            current_round=1,
            total_rounds=total_rounds,
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
    """Advance to the next round"""
    try:
        game = Game.query.filter_by(status='active').first()
        if not game:
            return jsonify({'error': 'No active game'}), 400
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
