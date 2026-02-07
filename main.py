"""Main game entry point with scene management."""
import pygame
from core.scene import SceneManager
from scenes import MainMenuScene, WorldScene, CampScene
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS


class Game:
    """Main game class managing the game loop and scenes."""
    
    def __init__(self):
        pygame.init()
        
        # Display setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Die Insel - Pygame")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Scene manager
        self.scene_manager = SceneManager()
        self._register_scenes()
        
        # Start at main menu
        self.scene_manager.change_scene('menu', self)
    
    def _register_scenes(self):
        """Register all game scenes."""
        self.scene_manager.register_scene('menu', MainMenuScene)
        self.scene_manager.register_scene('world', WorldScene)
        self.scene_manager.register_scene('camp', CampScene)
    
    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000  # Delta time in seconds
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene_manager.handle_event(event)
            
            # Update
            self.scene_manager.update(dt)
            
            # Draw
            self.scene_manager.draw(self.screen)
            pygame.display.flip()
        
        pygame.quit()


def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
