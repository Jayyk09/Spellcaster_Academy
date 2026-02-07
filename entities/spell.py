"""Spell projectile entity for ranged combat."""
import pygame
import math
from core.animation import AnimatedSprite
from config.settings import (
    SPELL_PROJECTILE_CONFIG, SPELL_SPEED, SPELL_DAMAGE, SPELL_LIFETIME, SCALE
)


class SpellProjectile(AnimatedSprite):
    """A spell projectile that travels in a direction and damages enemies on hit."""
    
    def __init__(self, x: float, y: float, spell_type: str, direction: pygame.Vector2,
                 target_letter: str | None = None):
        """
        Create a spell projectile.
        
        Args:
            x: Starting x position
            y: Starting y position
            spell_type: Type of spell (fireball, ice, etc.) - determines animation
            direction: Normalized direction vector for movement
            target_letter: If set, this spell can only hit enemies with this letter
        """
        super().__init__(x, y, SPELL_PROJECTILE_CONFIG)
        
        self.spell_type = spell_type
        self.damage = SPELL_DAMAGE
        self.speed = SPELL_SPEED
        self.lifetime = SPELL_LIFETIME
        self.alive = True
        self.direction = direction
        
        # Letter targeting - if set, can only hit enemies with this letter
        self.target_letter = target_letter.upper() if target_letter else None
        
        # Set velocity based on direction
        self.velocity = direction * self.speed
        
        # Collision radius for hit detection
        self.collision_radius = 10
        
        # Calculate rotation angle from direction vector
        # Sprites face right (1, 0) by default, so we calculate angle from that
        # atan2 gives angle in radians, convert to degrees
        # Pygame rotates counter-clockwise, so we negate
        self.rotation_angle = -math.degrees(math.atan2(direction.y, direction.x))
        
        # Play the appropriate spell animation
        if spell_type in self.animations:
            self.play(spell_type)
        else:
            self.play('fireball')  # Fallback
    
    @classmethod
    def create_targeted(cls, source_pos: pygame.Vector2, target_pos: pygame.Vector2,
                        spell_type: str, target_letter: str) -> 'SpellProjectile':
        """
        Create a spell that travels toward a target position.
        
        Args:
            source_pos: Starting position (usually player position)
            target_pos: Target position (usually enemy position)
            spell_type: Type of spell for animation
            target_letter: Letter of the target enemy (spell can only hit this letter)
        
        Returns:
            A new SpellProjectile aimed at the target
        """
        # Calculate direction from source to target
        direction = target_pos - source_pos
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = pygame.Vector2(1, 0)  # Default to right if same position
        
        return cls(source_pos.x, source_pos.y, spell_type, direction, target_letter)
    
    def can_hit_target(self, target_letter: str) -> bool:
        """
        Check if this spell can hit a target with the given letter.
        
        Args:
            target_letter: The letter of the potential target
        
        Returns:
            True if this spell can hit the target, False otherwise
        """
        if self.target_letter is None:
            # No letter restriction, can hit anyone
            return True
        return self.target_letter == target_letter.upper()
    
    def update(self, dt: float):
        """Update spell position and check lifetime."""
        if not self.alive:
            return
        
        # Move projectile
        self.pos += self.velocity * dt
        
        # Update lifetime
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
        
        # Update animation frame
        if self.current_animation_name in self.animations:
            anim = self.animations[self.current_animation_name]
            anim.update(dt)
            
            # Get frame and rotate based on direction
            frame = anim.get_current_frame()
            
            # Rotate the frame
            if self.rotation_angle != 0:
                frame = pygame.transform.rotate(frame, self.rotation_angle)
            
            self.image = frame
        
        # Update rect position
        if self.rect is not None:
            self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
    
    def get_hitbox(self) -> pygame.Rect:
        """Get collision rectangle for hit detection."""
        # Scale the hitbox appropriately
        size = self.collision_radius * 2
        return pygame.Rect(
            self.pos.x - self.collision_radius,
            self.pos.y - self.collision_radius,
            size, size
        )
    
    def destroy(self):
        """Mark spell for removal (called when it hits something)."""
        self.alive = False
    
    @property
    def is_alive(self) -> bool:
        """Check if spell is still active."""
        return self.alive
