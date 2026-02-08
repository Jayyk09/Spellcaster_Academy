"""Global game state that persists across scenes."""
import json
import os


class GameState:
    """Global game state singleton."""
    
    def __init__(self):
        # Player stats
        self.shroom_chunks = 0
        
        # Game flags
        self.current_scene = "world"
        
        # Player position (for scene transitions)
        self.player_start_pos: tuple[float, float] = (400, 250)
        self.player_exit_pos: tuple[float, float] = (230, 215)
        self.player_load_pos: tuple[float, float] = (355, 160)
    
    def reset(self):
        """Reset to default state."""
        self.shroom_chunks = 0


# Global instance
game_state = GameState()
