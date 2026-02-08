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
        
        # Velocity-based offset - show more in direction of movement
        # Offset as fraction of viewport (0.3 = player is at 30% from edge when moving)
        self.velocity_offset = 0.3
        self._target_velocity: Optional[pygame.Vector2] = None
    
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
    
    def set_target(self, pos: pygame.Vector2, velocity: Optional[pygame.Vector2] = None):
        """Set the position and velocity to follow."""
        self._target_pos = pos
        self._target_velocity = velocity
    
    def update(self, dt: float = 0.0):
        """
        Update camera position to follow target.
        
        Uses velocity-based offset to show more of the map in the
        direction the target is moving (player at bottom when going up,
        at top when going down, etc.).
        
        Args:
            dt: Delta time (unused for now, for future smoothing)
        """
        if self._target_pos is None:
            return
        
        target_x = self._target_pos.x
        target_y = self._target_pos.y
        
        # Calculate velocity-based offset
        # Show more in the direction we're moving
        offset_x = 0.0
        offset_y = 0.0
        if self._target_velocity is not None:
            # Normalize velocity to get direction
            vel_x = self._target_velocity.x
            vel_y = self._target_velocity.y
            
            # Calculate offset - camera shifts to show more in movement direction
            # Moving up (negative Y velocity) -> camera shifts up -> player at bottom
            # Moving right (positive X velocity) -> camera shifts right -> player at left
            offset_x = vel_x * self.velocity_offset if abs(vel_x) > 0.1 else 0
            offset_y = vel_y * self.velocity_offset if abs(vel_y) > 0.1 else 0
            
            # Clamp offset to reasonable range
            max_offset_x = self.viewport_width * 0.25
            max_offset_y = self.viewport_height * 0.25
            offset_x = max(-max_offset_x, min(max_offset_x, offset_x))
            offset_y = max(-max_offset_y, min(max_offset_y, offset_y))
        
        # Calculate desired camera position (centered on target + offset)
        desired_x = target_x - self.viewport_width / 2 + offset_x
        desired_y = target_y - self.viewport_height / 2 + offset_y
        
        # Apply smoothing if enabled
        if self.smoothing > 0 and dt > 0:
            self.x += (desired_x - self.x) * (1 - self.smoothing) * dt * 60
            self.y += (desired_y - self.y) * (1 - self.smoothing) * dt * 60
        else:
            self.x = desired_x
            self.y = desired_y
        
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
