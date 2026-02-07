"""Player entity with movement, animations, and spell casting."""
import pygame
from core.animation import AnimatedSprite
from config.settings import (
    PLAYER_SPRITE_CONFIG, PLAYER_SPEED, PLAYER_MAX_HEALTH,
    PLAYER_HEALTH_REGEN, PLAYER_REGEN_INTERVAL,
    SPELL_TYPES, SPELL_COOLDOWN
)
from entities.spell import SpellProjectile


class Player(AnimatedSprite):
    """Player character with 8-directional movement and spell casting."""
    
    # Direction constants
    DIR_FRONT = 'front'
    DIR_BACK = 'back'
    DIR_SIDE = 'side'
    
    # States
    STATE_IDLE = 'idle'
    STATE_WALKING = 'walking'
    STATE_CASTING = 'casting'
    STATE_DEAD = 'dead'
    
    def __init__(self, x: float, y: float):
        super().__init__(x, y, PLAYER_SPRITE_CONFIG)
        
        # Movement
        self.speed = PLAYER_SPEED
        self.velocity = pygame.Vector2(0, 0)
        self.direction = self.DIR_FRONT  # Current facing direction
        
        # State
        self.state = self.STATE_IDLE
        self._alive = True
        
        # Spell casting
        self.spell_cooldown = 0.0
        self.spell_cooldown_duration = SPELL_COOLDOWN
        self.current_spell_index = 0
        self.is_casting = False
        self.cast_timer = 0.0
        self.cast_duration = 0.3  # Brief casting animation
        
        # Health
        self.max_health = PLAYER_MAX_HEALTH
        self.health = PLAYER_MAX_HEALTH
        
        # Health regeneration
        self.regen_timer = 0.0
        self.regen_interval = PLAYER_REGEN_INTERVAL
        self.regen_amount = PLAYER_HEALTH_REGEN
        
        # Collision box (smaller than sprite for better feel)
        self.collision_radius = 7
        
        # Input tracking
        self.input_vector = pygame.Vector2(0, 0)
        
        # Play initial animation
        self.play('idle_front')
    
    def handle_input(self, keys):
        """Process keyboard input for movement."""
        if self.state == self.STATE_DEAD or self.state == self.STATE_CASTING:
            self.input_vector = pygame.Vector2(0, 0)
            return
        
        # Reset input
        self.input_vector = pygame.Vector2(0, 0)
        
        # WASD or Arrow keys
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.input_vector.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.input_vector.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.input_vector.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.input_vector.y += 1
        
        # Normalize diagonal movement
        if self.input_vector.length() > 0:
            self.input_vector = self.input_vector.normalize()
    
    def handle_spell_input(self, key) -> SpellProjectile | None:
        """Handle spell casting input (spacebar). Returns a spell if cast."""
        if key == pygame.K_SPACE and self.state != self.STATE_DEAD:
            if not self.is_casting and self.spell_cooldown <= 0:
                return self.cast_spell()
        return None
    
    def cast_spell(self) -> SpellProjectile:
        """Cast the current spell and return the projectile."""
        self.is_casting = True
        self.cast_timer = self.cast_duration
        self.state = self.STATE_CASTING
        
        # Get current spell type and cycle to next
        spell_type = SPELL_TYPES[self.current_spell_index]
        self.current_spell_index = (self.current_spell_index + 1) % len(SPELL_TYPES)
        
        # Calculate spell direction based on player facing
        direction = self._get_spell_direction()
        
        # Create spell projectile at player position (slightly offset in direction)
        offset = 20
        spawn_x = self.pos.x + direction.x * offset
        spawn_y = self.pos.y + direction.y * offset
        
        spell = SpellProjectile(spawn_x, spawn_y, spell_type, direction)
        
        # Play casting animation (use attack animation)
        anim_name = f'attack_{self.direction}'
        self.play(anim_name, reset=True)
        if anim_name in self.animations:
            self.animations[anim_name].loop = False
        
        return spell
    
    def _get_spell_direction(self) -> pygame.Vector2:
        """Get the direction vector for spell casting based on facing."""
        if self.direction == self.DIR_FRONT:
            return pygame.Vector2(0, 1)  # Down
        elif self.direction == self.DIR_BACK:
            return pygame.Vector2(0, -1)  # Up
        else:  # Side
            if self.facing_right:
                return pygame.Vector2(1, 0)  # Right
            else:
                return pygame.Vector2(-1, 0)  # Left
    
    def update(self, dt: float):
        """Update player state, movement, and animation."""
        # Update spell cooldown
        if self.spell_cooldown > 0:
            self.spell_cooldown -= dt
        
        # Handle casting state
        if self.is_casting:
            self.cast_timer -= dt
            if self.cast_timer <= 0:
                self.is_casting = False
                self.spell_cooldown = self.spell_cooldown_duration
                self.state = self.STATE_IDLE
        
        # Update movement if not casting or dead
        if self.state not in (self.STATE_CASTING, self.STATE_DEAD):
            self._update_movement(dt)
        
        # Update health regeneration
        if self._alive and self.health < self.max_health:
            self.regen_timer += dt
            if self.regen_timer >= self.regen_interval:
                self.regen_timer = 0.0
                self.health = min(self.max_health, self.health + self.regen_amount)
        
        # Update animation
        self._update_animation()
        
        # Call parent update for animation frame advancement
        super().update(dt)
    
    def _update_movement(self, dt: float):
        """Update player position based on input."""
        if self.input_vector.length() > 0:
            # Update velocity
            self.velocity = self.input_vector * self.speed
            
            # Update position
            self.pos += self.velocity * dt
            
            # Update direction based on movement
            self._update_direction()
            
            self.state = self.STATE_WALKING
        else:
            self.velocity = pygame.Vector2(0, 0)
            self.state = self.STATE_IDLE
    
    def _update_direction(self):
        """Update facing direction based on velocity."""
        if abs(self.input_vector.x) > abs(self.input_vector.y):
            # Moving more horizontally
            self.direction = self.DIR_SIDE
            self.facing_right = self.input_vector.x > 0
        elif self.input_vector.y > 0:
            # Moving down
            self.direction = self.DIR_FRONT
        elif self.input_vector.y < 0:
            # Moving up
            self.direction = self.DIR_BACK
    
    def _update_animation(self):
        """Update current animation based on state and direction."""
        if self.state == self.STATE_DEAD:
            self.play('death')
            return
        
        if self.state == self.STATE_CASTING:
            # Casting animation is already set in cast_spell
            return
        
        if self.state == self.STATE_WALKING:
            anim_name = f'walk_{self.direction}'
        else:
            anim_name = f'idle_{self.direction}'
        
        self.play(anim_name)
    
    def take_damage(self, amount: int):
        """Take damage and check for death."""
        if not self._alive:
            return
        
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.die()
    
    @property
    def is_alive(self) -> bool:
        """Check if player is alive."""
        return self._alive
    
    def die(self):
        """Handle player death."""
        self._alive = False
        self.state = self.STATE_DEAD
        self.play('death', reset=True)
        if 'death' in self.animations:
            self.animations['death'].loop = False
    
    def respawn(self, x: float, y: float):
        """Respawn player at position."""
        self.pos = pygame.Vector2(x, y)
        self.health = self.max_health
        self._alive = True
        self.state = self.STATE_IDLE
        self.is_casting = False
        self.cast_timer = 0.0
        self.spell_cooldown = 0.0
        self.play('idle_front', reset=True)
    
    def get_collision_rect(self) -> pygame.Rect:
        """Get collision rectangle for physics."""
        return pygame.Rect(
            self.pos.x - self.collision_radius,
            self.pos.y - self.collision_radius,
            self.collision_radius * 2,
            self.collision_radius * 2
        )
    
    def get_current_spell_name(self) -> str:
        """Get the name of the next spell that will be cast."""
        return SPELL_TYPES[self.current_spell_index]
