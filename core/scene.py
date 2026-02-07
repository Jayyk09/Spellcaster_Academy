"""Scene management and game state system."""
import pygame
from abc import ABC, abstractmethod


class Scene(ABC):
    """Base class for game scenes."""
    
    def __init__(self, game):
        self.game = game
        self.next_scene = None
    
    @abstractmethod
    def handle_event(self, event):
        """Handle pygame events."""
        pass
    
    @abstractmethod
    def update(self, dt: float):
        """Update scene logic."""
        pass
    
    @abstractmethod
    def draw(self, screen: pygame.Surface):
        """Draw scene to screen."""
        pass
    
    def on_enter(self):
        """Called when scene becomes active."""
        pass
    
    def on_exit(self):
        """Called when scene is about to be replaced."""
        pass


class SceneManager:
    """Manages scene transitions and the current scene."""
    
    def __init__(self):
        self.current_scene: Scene | None = None
        self.scenes: dict[str, type] = {}
    
    def register_scene(self, name: str, scene_class: type):
        """Register a scene class with a name."""
        self.scenes[name] = scene_class
    
    def change_scene(self, name: str, game, **kwargs):
        """Change to a different scene."""
        if name not in self.scenes:
            print(f"Warning: Scene '{name}' not registered")
            return
        
        # Exit current scene
        if self.current_scene:
            self.current_scene.on_exit()
        
        # Create and enter new scene
        self.current_scene = self.scenes[name](game, **kwargs)
        self.current_scene.on_enter()
    
    def handle_event(self, event):
        """Pass event to current scene."""
        if self.current_scene:
            self.current_scene.handle_event(event)
    
    def update(self, dt: float):
        """Update current scene."""
        if self.current_scene:
            self.current_scene.update(dt)
            
            # Check for scene transition
            if self.current_scene.next_scene:
                next_scene_name = self.current_scene.next_scene
                self.current_scene.next_scene = None
                self.change_scene(next_scene_name, self.current_scene.game)
    
    def draw(self, screen: pygame.Surface):
        """Draw current scene."""
        if self.current_scene:
            self.current_scene.draw(screen)
