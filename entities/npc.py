"""NPC entity - Mage Guardian that shows sign reference when player is nearby."""
import pygame
from core.animation import AnimatedSprite
from config.settings import NPC_SPRITE_CONFIG, NPC_INTERACTION_RADIUS


class MageGuardian(AnimatedSprite):
    """Mage Guardian NPC that displays ASL sign reference when the player is near."""

    def __init__(self, x: float, y: float):
        super().__init__(x, y, NPC_SPRITE_CONFIG)
        self.interaction_radius = NPC_INTERACTION_RADIUS
        self.player_nearby = False
        self.play('idle')

    def update(self, dt: float, player=None):
        """Update animation and check proximity to player."""
        # Check if player is within interaction radius
        if player and player.is_alive:
            distance = self.pos.distance_to(player.pos)
            self.player_nearby = distance <= self.interaction_radius
        else:
            self.player_nearby = False

        # Update animation
        super().update(dt)

    def is_player_nearby(self) -> bool:
        """Return whether the player is close enough to interact."""
        return self.player_nearby
