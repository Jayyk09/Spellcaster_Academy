"""Sprite animation system for loading and playing sprite sheet animations."""
import pygame
import os


class SpriteSheet:
    """Load and extract frames from a sprite sheet."""
    
    def __init__(self, path: str, frame_width: int, frame_height: int):
        self.path = path
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        try:
            self.sheet = pygame.image.load(path).convert_alpha()
        except pygame.error as e:
            print(f"Error loading sprite sheet {path}: {e}")
            # Create a fallback surface
            self.sheet = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            pygame.draw.rect(self.sheet, (255, 0, 255), (0, 0, frame_width, frame_height))
    
    def get_frame(self, col: int, row: int) -> pygame.Surface:
        """Extract a single frame from the sprite sheet."""
        x = col * self.frame_width
        y = row * self.frame_height
        
        frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
        frame.blit(self.sheet, (0, 0), (x, y, self.frame_width, self.frame_height))
        return frame
    
    def get_animation_frames(self, row: int, num_frames: int) -> list[pygame.Surface]:
        """Extract a row of frames for an animation."""
        return [self.get_frame(col, row) for col in range(num_frames)]


class Animation:
    """Manages a single animation sequence."""
    
    def __init__(self, frames: list[pygame.Surface], fps: float = 5.0, loop: bool = True):
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self.frame_duration = 1.0 / fps if fps > 0 else 1.0
        self.current_frame = 0
        self.elapsed_time = 0.0
        self.finished = False
    
    def reset(self):
        """Reset animation to the beginning."""
        self.current_frame = 0
        self.elapsed_time = 0.0
        self.finished = False
    
    def update(self, dt: float):
        """Update animation based on elapsed time."""
        if self.finished:
            return
        
        self.elapsed_time += dt
        
        while self.elapsed_time >= self.frame_duration:
            self.elapsed_time -= self.frame_duration
            self.current_frame += 1
            
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.finished = True
    
    def get_current_frame(self) -> pygame.Surface:
        """Get the current frame surface."""
        return self.frames[self.current_frame]


class AnimatedSprite(pygame.sprite.Sprite):
    """A sprite with multiple animations that can be switched between."""
    
    def __init__(self, x: float, y: float, sprite_config: dict):
        super().__init__()
        
        self.pos = pygame.Vector2(x, y)
        self.animations: dict[str, Animation] = {}
        self.current_animation_name = ""
        self.facing_right = True  # For horizontal flip
        
        # Load sprite sheet and animations from config
        self._load_from_config(sprite_config)
        
        # Set initial image and rect
        if self.animations:
            first_anim = list(self.animations.keys())[0]
            self.current_animation_name = first_anim
            self.image = self.animations[first_anim].get_current_frame()
        else:
            self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        
        self.rect = self.image.get_rect()
        self.rect.center = (int(x), int(y))
    
    def _load_from_config(self, config: dict):
        """Load animations from a sprite configuration dictionary."""
        sprite_sheet = SpriteSheet(
            config['path'],
            config['frame_width'],
            config['frame_height']
        )
        
        for anim_name, anim_data in config['animations'].items():
            frames = sprite_sheet.get_animation_frames(
                anim_data['row'],
                anim_data['frames']
            )
            loop = anim_data.get('loop', True)
            self.animations[anim_name] = Animation(frames, anim_data['fps'], loop)
    
    def add_animation(self, name: str, animation: Animation):
        """Add an animation to the sprite."""
        self.animations[name] = animation
    
    def play(self, animation_name: str, reset: bool = False):
        """Switch to a different animation."""
        if animation_name not in self.animations:
            print(f"Warning: Animation '{animation_name}' not found")
            return
        
        if animation_name != self.current_animation_name or reset:
            self.current_animation_name = animation_name
            if reset:
                self.animations[animation_name].reset()
    
    def update(self, dt: float):
        """Update the current animation."""
        if self.current_animation_name in self.animations:
            anim = self.animations[self.current_animation_name]
            anim.update(dt)
            
            # Get frame and flip if needed
            frame = anim.get_current_frame()
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            self.image = frame
        
        if self.rect is not None:
            self.rect.center = (int(self.pos.x), int(self.pos.y))
    
    def is_animation_finished(self) -> bool:
        """Check if the current animation has finished (for non-looping animations)."""
        if self.current_animation_name in self.animations:
            return self.animations[self.current_animation_name].finished
        return True
    
    def get_current_animation(self) -> Animation | None:
        """Get the current animation object."""
        return self.animations.get(self.current_animation_name)
