"""Main game entry point with scene management."""
import pygame
from core.scene import SceneManager
from scenes import MainMenuScene, WorldScene
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    CAMERA_ENABLED, CAMERA_HOLD_TIME, CAMERA_CONFIDENCE, CAMERA_SHOW_PREVIEW
)


class Game:
    """Main game class managing the game loop and scenes."""
    
    def __init__(self):
        pygame.init()
        
        # Display setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Die Insel - Pygame")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Shared camera input (persists across scenes)
        self.camera_input = None
        self._camera_initialized = False
        
        # Scene manager
        self.scene_manager = SceneManager()
        self._register_scenes()
        
        # Start at main menu
        self.scene_manager.change_scene('menu', self)
    
    def get_camera_input(self):
        """Get or initialize the shared camera input."""
        if not CAMERA_ENABLED:
            return None
        
        if not self._camera_initialized:
            self._camera_initialized = True
            try:
                from vision.camera_input import CameraInput
                self.camera_input = CameraInput(
                    hold_time=CAMERA_HOLD_TIME,
                    confidence_threshold=CAMERA_CONFIDENCE,
                    show_preview=CAMERA_SHOW_PREVIEW
                )
                self.camera_input.start()
            except Exception as e:
                print(f"Camera input not available: {e}")
                self.camera_input = None
        
        return self.camera_input
    
    def _register_scenes(self):
        """Register all game scenes."""
        self.scene_manager.register_scene('menu', MainMenuScene)
        self.scene_manager.register_scene('world', WorldScene)
    
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
        
        # Cleanup camera on exit
        if self.camera_input is not None:
            self.camera_input.stop()
        
        pygame.quit()


def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
