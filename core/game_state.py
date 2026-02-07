"""Global game state that persists across scenes."""
import json
import os


class GameState:
    """Global game state singleton."""
    
    def __init__(self):
        # Player stats
        self.player_exp = 0
        self.player_level = 1
        self.shroom_chunks = 0
        
        # Game flags
        self.game_has_savegame = False
        self.current_scene = "world"
        
        # Player position (for scene transitions)
        self.player_start_pos: tuple[float, float] = (400, 250)
        self.player_exit_pos: tuple[float, float] = (230, 215)
        self.player_load_pos: tuple[float, float] = (355, 160)
        
        # Save file path
        self.save_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'savegame.json'
        )
    
    def save_game(self):
        """Save game state to file."""
        data = {
            'player_exp': self.player_exp,
            'player_level': self.player_level,
            'shroom_chunks': self.shroom_chunks,
            'game_has_savegame': True,
        }
        
        try:
            with open(self.save_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.game_has_savegame = True
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    def load_game(self):
        """Load game state from file."""
        if not os.path.exists(self.save_file):
            return False
        
        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)
            
            self.player_exp = data.get('player_exp', 0)
            self.player_level = data.get('player_level', 1)
            self.shroom_chunks = data.get('shroom_chunks', 0)
            self.game_has_savegame = data.get('game_has_savegame', False)
            return True
        except Exception as e:
            print(f"Error loading game: {e}")
            return False
    
    def check_savegame_exists(self):
        """Check if a save file exists."""
        self.game_has_savegame = os.path.exists(self.save_file)
        return self.game_has_savegame
    
    def reset(self):
        """Reset to default state."""
        self.player_exp = 0
        self.player_level = 1
        self.shroom_chunks = 0


# Global instance
game_state = GameState()
