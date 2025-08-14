import random
import json
from datetime import datetime
from models import db

class GameManager:
    """Manages game logic and flow"""
    
    def start_round(self, game, logos):
        """Start a new round with first question"""
        try:
            game.current_question = 1
            game.status = 'active'
            return self.start_question(game, logos)
        except Exception as e:
            print(f"Error starting round: {e}")
            return None
    
    def start_question(self, game, logos):
        """Start a new question with a random logo"""
        try:
            # Get used logo IDs from database
            used_logo_ids = []
            if game.used_logo_ids:
                try:
                    used_logo_ids = json.loads(game.used_logo_ids)
                except:
                    used_logo_ids = []
            
            available_logos = [logo for logo in logos if logo.id not in used_logo_ids]
            
            if not available_logos:
                # If all logos have been used, reset and use all logos again
                available_logos = logos
                used_logo_ids = []
            
            if available_logos:
                selected_logo = random.choice(available_logos)
                game.current_logo_id = selected_logo.id
                game.round_start_time = datetime.utcnow()
                
                # Update used logos
                used_logo_ids.append(selected_logo.id)
                game.used_logo_ids = json.dumps(used_logo_ids)
                
                return selected_logo
            
        except Exception as e:
            print(f"Error starting question: {e}")
            return None
    
    def advance_question(self, game, logos):
        """Advance to next question or complete round"""
        try:
            if game.current_question < game.questions_per_round:
                # Move to next question in same round
                game.current_question += 1
                return self.start_question(game, logos)
            else:
                # Round complete - wait for admin
                game.status = 'round_complete'
                game.current_logo_id = None
                game.round_start_time = None
                return None
        except Exception as e:
            print(f"Error advancing question: {e}")
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
