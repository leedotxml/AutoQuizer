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
                
                # Update used logos
                used_logo_ids.append(selected_logo.id)
                game.used_logo_ids = json.dumps(used_logo_ids)
                
                return selected_logo
            
        except Exception as e:
            print(f"Error starting question: {e}")
            return None
    
    def advance_question(self, game, logos):
        """Advance to next question or complete game"""
        try:
            if game.current_question < game.questions_per_round:
                # Move to next question in same round
                game.current_question += 1
                return self.start_question(game, logos)
            else:
                # All questions complete - end the game
                game.status = 'finished'
                game.current_logo_id = None
                return None
        except Exception as e:
            print(f"Error advancing question: {e}")
            return None
