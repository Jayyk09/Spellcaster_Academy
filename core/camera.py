"""Camera class for viewport management and smooth following."""
import pygame
from typing import Tuple, Optional


class Camera:
    """
    Manages the viewport into the game world.
    
    Features:
    - Follows a target (usually the player) with configurable drag margins
    - Limits camera to world boundaries
    - Provides world-to-screen coordinate conversion
    
    Mirrors the Godot Camera2D node with drag margins and limits.
    """
    
    def __init__(self, viewport_width: int, viewport_height: int,
                 world_width: int, world_height: int):
        """
        Initialize the camera.
        
        Args:
            viewport_width: Width of the visible area (screen width)
            viewport_height: Height of the visible area (screen height)
            world_width: Total world width in pixels
            world_height: Total world height in pixels
        """
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.world_width = world_width
        self.world_height = world_height
        
        # Camera position (top-left corner of viewport in world coordinates)
        self.x = 0.0
        self.y = 0.0
        
        # Drag margins (0.0-0.5, fraction of viewport where target can move freely)
        # 0.15 = 15% margin on each side, matching die-insel tutorial
        self.drag_margin = 0.15
        
        # Smoothing factor (0 = instant, 1 = no movement)
        # Not using smoothing for now to match die-insel behavior
        self.smoothing = 0.0
        
        # Target to follow
        self._target_pos: Optional[pygame.Vector2] = None
    
    @property
    def rect(self) -> pygame.Rect:
        """Get the camera's viewport as a rectangle in world coordinates."""
        return pygame.Rect(int(self.x), int(self.y), 
                          self.viewport_width, self.viewport_height)
    
    @property
    def center(self) -> Tuple[float, float]:
        """Get the center of the viewport in world coordinates."""
        return (self.x + self.viewport_width / 2, 
                self.y + self.viewport_height / 2)
    
    def set_target(self, pos: pygame.Vector2):
        """Set the position to follow."""
        self._target_pos = pos
    
    def update(self, dt: float = 0.0):
        """
        Update camera position to follow target.
        
        Uses drag margins so the camera only moves when the target
        approaches the edge of the "safe zone".
        
        Args:
            dt: Delta time (unused for now, for future smoothing)
        """
        if self._target_pos is None:
            return
        
        target_x = self._target_pos.x
        target_y = self._target_pos.y
        
        # Calculate the drag margin bounds in screen space
        margin_x = self.viewport_width * self.drag_margin
        margin_y = self.viewport_height * self.drag_margin
        
        # The "safe zone" where target can move without camera following
        safe_left = self.x + margin_x
        safe_right = self.x + self.viewport_width - margin_x
        safe_top = self.y + margin_y
        safe_bottom = self.y + self.viewport_height - margin_y
        
        # Move camera if target is outside the safe zone
        if target_x < safe_left:
            self.x = target_x - margin_x
        elif target_x > safe_right:
            self.x = target_x - (self.viewport_width - margin_x)
        
        if target_y < safe_top:
            self.y = target_y - margin_y
        elif target_y > safe_bottom:
            self.y = target_y - (self.viewport_height - margin_y)
        
        # Clamp camera to world bounds
        self._clamp_to_bounds()
    
    def _clamp_to_bounds(self):
        """Ensure camera stays within world boundaries."""
        # Left/Top bounds
        self.x = max(0, self.x)
        self.y = max(0, self.y)
        
        # Right/Bottom bounds
        max_x = max(0, self.world_width - self.viewport_width)
        max_y = max(0, self.world_height - self.viewport_height)
        self.x = min(max_x, self.x)
        self.y = min(max_y, self.y)
    
    def center_on(self, x: float, y: float):
        """
        Center the camera on a world position.
        
        Args:
            x: World x coordinate to center on
            y: World y coordinate to center on
        """
        self.x = x - self.viewport_width / 2
        self.y = y - self.viewport_height / 2
        self._clamp_to_bounds()
    
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """
        Convert world coordinates to screen coordinates.
        
        Args:
            world_x: X position in world space
            world_y: Y position in world space
            
        Returns:
            (screen_x, screen_y) tuple
        """
        screen_x = int(world_x - self.x)
        screen_y = int(world_y - self.y)
        return (screen_x, screen_y)
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """
        Convert screen coordinates to world coordinates.
        
        Args:
            screen_x: X position on screen
            screen_y: Y position on screen
            
        Returns:
            (world_x, world_y) tuple
        """
        world_x = screen_x + self.x
        world_y = screen_y + self.y
        return (world_x, world_y)
    
    def apply_to_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """
        Apply camera offset to a rectangle.
        
        Args:
            rect: Rectangle in world coordinates
            
        Returns:
            Rectangle in screen coordinates
        """
        return pygame.Rect(
            rect.x - int(self.x),
            rect.y - int(self.y),
            rect.width,
            rect.height
        )
    
    def apply_to_surface(self, surface: pygame.Surface, 
                         dest_surface: pygame.Surface,
                         world_pos: Tuple[int, int] = (0, 0)):
        """
        Blit a surface to the destination with camera offset applied.
        
        Args:
            surface: Source surface to blit
            dest_surface: Destination surface (usually the screen)
            world_pos: Position of source surface in world coordinates
        """
        screen_x, screen_y = self.world_to_screen(world_pos[0], world_pos[1])
        dest_surface.blit(surface, (screen_x, screen_y))
    
    def is_visible(self, rect: pygame.Rect) -> bool:
        """
        Check if a world rectangle is visible in the viewport.
        
        Args:
            rect: Rectangle in world coordinates
            
        Returns:
            True if any part of the rect is visible
        """
        return self.rect.colliderect(rect)
