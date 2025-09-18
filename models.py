from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Team(db.Model):
    """Team model for storing team information"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    members = db.Column(db.Text, nullable=False)  # JSON string of member names
    score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Team {self.name}>'

class Logo(db.Model):
    """Logo model for storing car logos and answers"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)
    alternative_answers = db.Column(db.Text)  # JSON string of alternative answers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Logo {self.name}>'

class Game(db.Model):
    """Game model for tracking game sessions"""
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default='waiting')  # waiting, active, finished, round_complete
    current_round = db.Column(db.Integer, default=1)
    total_rounds = db.Column(db.Integer, default=1)
    current_question = db.Column(db.Integer, default=1)  # Question number within current round (1-10)
    questions_per_round = db.Column(db.Integer, default=10)
    current_logo_id = db.Column(db.Integer, db.ForeignKey('logo.id'))
    round_start_time = db.Column(db.DateTime)
    used_logo_ids = db.Column(db.Text)  # JSON string of used logo IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Game {self.id} - {self.status}>'

class GameTeam(db.Model):
    """GameTeam model for tracking which teams are participating in each game"""
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate entries
    __table_args__ = (db.UniqueConstraint('game_id', 'team_id', name='_game_team_uc'),)
    
    def __repr__(self):
        return f'<GameTeam game:{self.game_id} team:{self.team_id}>'

class Guess(db.Model):
    """Guess model for storing team guesses"""
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    logo_id = db.Column(db.Integer, db.ForeignKey('logo.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    guess_text = db.Column(db.String(100), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Legacy field for backward compatibility - will be removed after migration
    guess = db.Column(db.String(100), nullable=True)
    
    # Unique constraint to prevent duplicate guesses per team/question
    __table_args__ = (db.UniqueConstraint('team_id', 'game_id', 'round_number', 'logo_id', name='_team_game_round_logo_uc'),)
    
    def __repr__(self):
        return f'<Guess {self.guess_text} - {self.is_correct}>'
