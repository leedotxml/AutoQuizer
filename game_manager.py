import random
from datetime import datetime
from models import db

class GameManager:
    """Manages game logic and flow"""
    
    def start_round(self, game, logos):
        """Start a new round with a random logo"""
        try:
            # Get a random logo that hasn't been used in this game yet
            used_logo_ids = []
            if hasattr(game, '_used_logos'):
                used_logo_ids = game._used_logos
            else:
                game._used_logos = []
            
            available_logos = [logo for logo in logos if logo.id not in used_logo_ids]
            
            if not available_logos:
                # If all logos have been used, reset and use all logos again
                available_logos = logos
                game._used_logos = []
            
            if available_logos:
                selected_logo = random.choice(available_logos)
                game.current_logo_id = selected_logo.id
                game.round_start_time = datetime.utcnow()
                game._used_logos.append(selected_logo.id)
                
                return selected_logo
            
        except Exception as e:
            print(f"Error starting round: {e}")
            return None
    
    def is_round_expired(self, game):
        """Check if the current round has expired (30 seconds)"""
        if not game.round_start_time:
            return False
        
        elapsed = (datetime.utcnow() - game.round_start_time).total_seconds()
        return elapsed >= 30
    
    def get_time_remaining(self, game):
        """Get remaining time for current round"""
        if not game.round_start_time:
            return 0
        
        elapsed = (datetime.utcnow() - game.round_start_time).total_seconds()
        return max(0, 30 - elapsed)
