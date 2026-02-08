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
    DIR_DOWN = 'down'
    DIR_UP = 'up'
    DIR_LEFT = 'left'
    DIR_RIGHT = 'right'
    
    # States
    STATE_IDLE = 'idle'
    STATE_WALKING = 'walking'
    STATE_CASTING = 'casting'
    STATE_BLOCKING = 'blocking'
    STATE_DEAD = 'dead'
    
    def __init__(self, x: float, y: float):
        super().__init__(x, y, PLAYER_SPRITE_CONFIG)
        
        # Movement
        self.speed = PLAYER_SPEED
        self.velocity = pygame.Vector2(0, 0)
        self.direction = self.DIR_DOWN  # Current facing direction
        
        # State
        self.state = self.STATE_IDLE
        self._alive = True
        
        # Spell casting
        self.spell_cooldown = 0.0
        self.spell_cooldown_duration = SPELL_COOLDOWN
        self.current_spell_index = 0
        
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
        
        # Casting animation timer
        self.cast_anim_timer = 0.0
        self.cast_anim_duration = 0.4  # seconds to show cast animation
        
        # Blocking
        self.is_blocking = False  # True while block animation is playing
        self.block_cooldown = 0.0
        self.block_cooldown_duration = 0.5  # seconds before can block again
        
        # Play initial animation
        self.play('idle_down')
    
    def handle_input(self, keys):
        """Process keyboard input for movement."""
        if self.state == self.STATE_DEAD:
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
        """Handle spell casting input. Returns a spell if cast."""
        # Spacebar is now used for blocking, not casting
        return None
    
    def handle_block_input(self, key) -> bool:
        """Handle block input. Returns True if block started."""
        return False
    
    def start_block(self) -> bool:
        """Start the blocking animation. Returns True if block started."""
        self.state = self.STATE_BLOCKING
        self.is_blocking = True
        self.velocity = pygame.Vector2(0, 0)
        self.play('block', reset=True)
        return True
    
    def cast_spell(self) -> SpellProjectile:
        """Cast the current spell and return the projectile."""
        # Get current spell type and cycle to next
        spell_type = SPELL_TYPES[self.current_spell_index]
        self.current_spell_index = (self.current_spell_index + 1) % len(SPELL_TYPES)
        
        # Calculate spell direction based on player facing
        direction = self._get_spell_direction()
        
        # Create spell projectile at player position (slightly offset in direction)
        # Adjust Y offset for left/right animations where wand is held lower
        offset = 20
        spawn_x = self.pos.x + direction.x * offset
        spawn_y = self.pos.y + direction.y * offset
        
        # Add vertical offset for horizontal casting (wand is held lower in side animations)
        if self.direction in (self.DIR_LEFT, self.DIR_RIGHT):
            spawn_y += 20  # Move spell down to match wand position
        if self.direction in (self.DIR_UP, self.DIR_DOWN):
            spawn_x += 10  # Move spell slightly to the right for better alignment
            if self.direction == self.DIR_DOWN:
                spawn_y += 50  # Move spell down for downward casting
        
        spell = SpellProjectile(spawn_x, spawn_y, spell_type, direction)
        
        # Set cooldown and play cast animation
        self.spell_cooldown = self.spell_cooldown_duration
        self.state = self.STATE_CASTING
        self.cast_anim_timer = self.cast_anim_duration
        self.play(f'cast_{self.direction}', reset=True)
        
        return spell
    
    def _get_spell_direction(self) -> pygame.Vector2:
        """Get the direction vector for spell casting based on facing."""
        if self.direction == self.DIR_DOWN:
            return pygame.Vector2(0, 1)
        elif self.direction == self.DIR_UP:
            return pygame.Vector2(0, -1)
        elif self.direction == self.DIR_RIGHT:
            return pygame.Vector2(1, 0)
        else:  # LEFT
            return pygame.Vector2(-1, 0)
    
    def play_cast_toward(self, target_pos: pygame.Vector2):
        """Trigger the casting animation facing toward a target position."""
        # Determine direction to target
        diff = target_pos - self.pos
        if abs(diff.x) > abs(diff.y):
            if diff.x > 0:
                self.direction = self.DIR_RIGHT
                self.facing_right = True
            else:
                self.direction = self.DIR_LEFT
                self.facing_right = False
        else:
            if diff.y > 0:
                self.direction = self.DIR_DOWN
            else:
                self.direction = self.DIR_UP
        
        # Set casting state and animation
        self.state = self.STATE_CASTING
        self.cast_anim_timer = self.cast_anim_duration
        self.play(f'cast_{self.direction}', reset=True)
    
    def update(self, dt: float):
        """Update player state, movement, and animation."""
        # Update spell cooldown
        if self.spell_cooldown > 0:
            self.spell_cooldown -= dt
        
        # Update block cooldown
        if self.block_cooldown > 0:
            self.block_cooldown -= dt
        
        # Update cast animation timer
        if self.cast_anim_timer > 0:
            self.cast_anim_timer -= dt
            if self.cast_anim_timer <= 0:
                self.state = self.STATE_IDLE
        
        # Check if block animation finished
        if self.state == self.STATE_BLOCKING:
            if self.is_animation_finished():
                self.is_blocking = False
                self.state = self.STATE_IDLE
                self.block_cooldown = self.block_cooldown_duration
        
        # Update movement if not dead, casting, or blocking
        if self.state not in (self.STATE_DEAD, self.STATE_CASTING, self.STATE_BLOCKING):
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
            if self.input_vector.x > 0:
                self.direction = self.DIR_RIGHT
                self.facing_right = True
            else:
                self.direction = self.DIR_LEFT
                self.facing_right = False
        elif self.input_vector.y > 0:
            # Moving down
            self.direction = self.DIR_DOWN
        elif self.input_vector.y < 0:
            # Moving up
            self.direction = self.DIR_UP
    
    def _update_animation(self):
        """Update current animation based on state and direction."""
        if self.state == self.STATE_DEAD:
            self.play('death')
            return
        
        if self.state == self.STATE_BLOCKING:
            # Block animation is already playing, don't override it
            return
        
        if self.state == self.STATE_CASTING:
            anim_name = f'cast_{self.direction}'
        elif self.state == self.STATE_WALKING:
            anim_name = f'walk_{self.direction}'
        else:
            # Idle: use first frame of walk animation for current direction
            anim_name = f'walk_{self.direction}'
            # Reset to first frame so we show a static idle pose
            if self.current_animation_name != anim_name:
                self.play(anim_name, reset=True)
                # Freeze on first frame
                if anim_name in self.animations:
                    self.animations[anim_name].current_frame = 0
                    self.animations[anim_name].elapsed_time = 0.0
            else:
                # Already on the right walk anim, just freeze on frame 0
                if anim_name in self.animations:
                    self.animations[anim_name].current_frame = 0
                    self.animations[anim_name].elapsed_time = 0.0
            return
        
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
        self.spell_cooldown = 0.0
        self.play('idle_down', reset=True)
    
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
