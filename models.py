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
    status = db.Column(db.String(20), default='waiting')  # waiting, active, finished
    current_round = db.Column(db.Integer, default=1)
    total_rounds = db.Column(db.Integer, default=3)
    current_logo_id = db.Column(db.Integer, db.ForeignKey('logo.id'))
    round_start_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Game {self.id} - {self.status}>'

class Guess(db.Model):
    """Guess model for storing team guesses"""
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    guess = db.Column(db.String(100), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Guess {self.guess} - {self.is_correct}>'
