"""Collectible items and objects."""
import pygame
import os
from core.animation import AnimatedSprite
from config.settings import MUSHROOM_SPRITE_CONFIG, SPRITES_DIR


class Mushroom(AnimatedSprite):
    """Collectible mushroom that can be harvested."""
    
    def __init__(self, x: float, y: float):
        super().__init__(x, y, MUSHROOM_SPRITE_CONFIG)
        
        self.collected = False
        self.collection_timer = 0.0
        self.collection_delay = 1.5  # Time before actually collecting
        self.chunks_value = 3  # How many shroom_chunks this gives
        
        # Interaction
        self.interaction_radius = 19
        self.requires_attack = True  # Must attack to harvest
        
        # Play idle animation
        self.play('idle')
    
    def try_harvest(self, attack_hitbox: pygame.Rect | None) -> bool:
        """Try to harvest the mushroom. Returns True if harvest started."""
        if self.collected:
            return False
        
        if attack_hitbox is None:
            return False
        
        # Check if attack hitbox overlaps mushroom
        mushroom_rect = pygame.Rect(
            self.pos.x - self.interaction_radius,
            self.pos.y - self.interaction_radius,
            self.interaction_radius * 2,
            self.interaction_radius * 2
        )
        
        if attack_hitbox.colliderect(mushroom_rect):
            self._start_harvest()
            return True
        
        return False
    
    def _start_harvest(self):
        """Start the harvest animation."""
        self.collected = True
        self.collection_timer = self.collection_delay
        self.play('harvest', reset=True)
        if 'harvest' in self.animations:
            self.animations['harvest'].loop = False
    
    def update(self, dt: float) -> int:
        """Update mushroom. Returns chunks collected (0 if not done)."""
        chunks = 0
        
        if self.collected:
            self.collection_timer -= dt
            if self.collection_timer <= 0 and self.is_animation_finished():
                chunks = self.chunks_value
        
        super().update(dt)
        return chunks
    
    def is_fully_collected(self) -> bool:
        """Check if mushroom should be removed."""
        return self.collected and self.collection_timer <= 0 and self.is_animation_finished()


class Campfire:
    """Campfire save point object."""
    
    def __init__(self, x: float, y: float):
        self.pos = pygame.Vector2(x, y)
        self.interaction_radius = 40
        
        # Load sprite
        campfire_path = os.path.join(SPRITES_DIR, 'objects', 'campfire.png')
        try:
            sheet = pygame.image.load(campfire_path).convert_alpha()
            self.frames = []
            for i in range(4):
                frame = pygame.Surface((32, 32), pygame.SRCALPHA)
                frame.blit(sheet, (0, 0), (i * 32, 0, 32, 32))
                self.frames.append(frame)
        except pygame.error:
            # Fallback
            self.frames = [pygame.Surface((32, 32), pygame.SRCALPHA)]
            pygame.draw.circle(self.frames[0], (255, 100, 0), (16, 16), 12)
        
        self.current_frame = 0
        self.animation_timer = 0.0
        self.animation_fps = 5
    
    def update(self, dt: float):
        """Update campfire animation."""
        self.animation_timer += dt
        if self.animation_timer >= 1.0 / self.animation_fps:
            self.animation_timer = 0.0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
    
    def is_player_nearby(self, player_pos: pygame.Vector2) -> bool:
        """Check if player is close enough to interact."""
        return self.pos.distance_to(player_pos) <= self.interaction_radius
    
    def draw(self, screen: pygame.Surface):
        """Draw campfire and glow effect."""
        # Draw glow
        glow_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (255, 150, 50, 30), (50, 50), 50)
        screen.blit(glow_surface, (self.pos.x - 50, self.pos.y - 50))
        
        # Draw campfire sprite
        frame = self.frames[self.current_frame]
        rect = frame.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(frame, rect)
