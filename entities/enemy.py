"""Enemy entities with AI behavior."""
import pygame
import random
import math
import string
import os
from core.animation import AnimatedSprite
from config.settings import (
    SLIME_SPRITE_CONFIG, SKELETON_SPRITE_CONFIG,
    ENEMY_CHASE_SPEED, ENEMY_IDLE_SPEED,
    ENEMY_MAX_HEALTH, ENEMY_ATTACK_DAMAGE, ENEMY_DETECTION_RADIUS,
    ENEMY_ATTACK_RANGE, ENEMY_DAMAGE_COOLDOWN, ENEMY_XP_VALUE,
    ENEMY_LETTER_OFFSET_Y, FONTS_DIR,
    ENEMY_LETTER_BACKDROP_PATH
)


class Enemy(AnimatedSprite):
    """Base enemy class with common behavior."""
    
    # Direction constants
    DIR_FRONT = 'front'
    DIR_BACK = 'back'
    DIR_SIDE = 'side'
    
    # States
    STATE_IDLE = 'idle'
    STATE_WALKING = 'walking'
    STATE_CHASING = 'chasing'
    STATE_DEAD = 'dead'
    
    # Class-level font for letter rendering (loaded once)
    _letter_font = None
    _letter_backdrop = None
    
    @classmethod
    def _get_letter_font(cls):
        """Get or initialize the letter font (lazy loading)."""
        if cls._letter_font is None:
            font_path = os.path.join(FONTS_DIR, 'Alkhemikal.ttf')
            try:
                cls._letter_font = pygame.font.Font(font_path, 24)  # Larger font size
            except:
                cls._letter_font = pygame.font.Font(None, 24)
        return cls._letter_font
    
    @classmethod
    def _get_letter_backdrop(cls):
        """Get or initialize the letter backdrop image (lazy loading)."""
        if cls._letter_backdrop is None:
            try:
                original = pygame.image.load(ENEMY_LETTER_BACKDROP_PATH).convert_alpha()
                # Scale to larger size for better visibility
                cls._letter_backdrop = pygame.transform.scale(original, (36, 28))
            except:
                # Fallback: create a simple dark rectangle
                cls._letter_backdrop = pygame.Surface((36, 28), pygame.SRCALPHA)
                cls._letter_backdrop.fill((20, 40, 50, 200))
        return cls._letter_backdrop
    
    def __init__(self, x: float, y: float, sprite_config: dict):
        super().__init__(x, y, sprite_config)
        
        # Assign random letter (A-E for testing)
        self.letter = random.choice(['A', 'B', 'C', 'D', 'E'])
        self._letter_surface = None  # Pre-rendered letter surface
        self._render_letter_surface()
        
        # Movement
        self.idle_speed = ENEMY_IDLE_SPEED
        self.chase_speed = ENEMY_CHASE_SPEED
        self.velocity = pygame.Vector2(0, 0)
        self.direction = self.DIR_FRONT
        
        # State
        self.state = self.STATE_IDLE
        self._alive = True
        
        # Combat
        self.max_health = ENEMY_MAX_HEALTH
        self.health = ENEMY_MAX_HEALTH
        self.attack_damage = ENEMY_ATTACK_DAMAGE
        self.detection_radius = ENEMY_DETECTION_RADIUS
        self.attack_range = ENEMY_ATTACK_RANGE
        self.damage_cooldown = 0.0
        self.damage_cooldown_duration = ENEMY_DAMAGE_COOLDOWN
        self.xp_value = ENEMY_XP_VALUE
        
        # AI behavior timers
        self.wander_timer = 0.0
        self.wander_interval = random.uniform(2.0, 4.0)
        self.wander_direction = pygame.Vector2(0, 0)
        
        # Collision
        self.collision_radius = 8
        self.hitbox_radius = 13
        
        # Target (player)
        self.target = None
        
        # Play initial animation
        self.play('idle_front')
    
    @property
    def is_alive(self) -> bool:
        """Check if enemy is alive."""
        return self._alive
    
    def set_target(self, target):
        """Set the target to chase (usually the player)."""
        self.target = target
    
    def update(self, dt: float):
        """Update enemy state and behavior."""
        if self.state == self.STATE_DEAD:
            super().update(dt)
            return
        
        # Update damage cooldown
        if self.damage_cooldown > 0:
            self.damage_cooldown -= dt
        
        # Check for target and update state
        if self.target and self.target.is_alive:
            distance = self._get_distance_to_target()
            
            if distance <= self.attack_range:
                # In attack range - stop and deal damage
                self.state = self.STATE_CHASING
                self.velocity = pygame.Vector2(0, 0)
                self._try_attack_target()
            elif distance <= self.detection_radius:
                # Chase target
                self.state = self.STATE_CHASING
                self._chase_target(dt)
            else:
                # Wander
                self.state = self.STATE_IDLE
                self._wander(dt)
        else:
            # No target - wander
            self.state = self.STATE_IDLE
            self._wander(dt)
        
        # Update animation
        self._update_animation()
        
        # Call parent update
        super().update(dt)
    
    def _get_distance_to_target(self) -> float:
        """Get distance to current target."""
        if not self.target:
            return float('inf')
        return self.pos.distance_to(self.target.pos)
    
    def _chase_target(self, dt: float):
        """Chase the target."""
        if not self.target:
            return
        
        # Direction to target
        direction = self.target.pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        
        # Update velocity
        self.velocity = direction * self.chase_speed
        
        # Move
        self.pos += self.velocity * dt
        
        # Update facing direction
        self._update_direction(direction)
    
    def _wander(self, dt: float):
        """Random wandering behavior."""
        self.wander_timer -= dt
        
        if self.wander_timer <= 0:
            # Pick new random direction or stop
            self.wander_timer = random.uniform(2.0, 4.0)
            
            if random.random() < 0.5:
                # Stop
                self.wander_direction = pygame.Vector2(0, 0)
            else:
                # Random direction
                angle = random.uniform(0, 2 * math.pi)
                self.wander_direction = pygame.Vector2(math.cos(angle), math.sin(angle))
        
        # Apply wander movement
        if self.wander_direction.length() > 0:
            self.velocity = self.wander_direction * self.idle_speed
            self.pos += self.velocity * dt
            self._update_direction(self.wander_direction)
            self.state = self.STATE_WALKING
        else:
            self.velocity = pygame.Vector2(0, 0)
            self.state = self.STATE_IDLE
    
    def _update_direction(self, move_dir: pygame.Vector2):
        """Update facing direction based on movement."""
        if move_dir.length() == 0:
            return
        
        if abs(move_dir.x) > abs(move_dir.y):
            self.direction = self.DIR_SIDE
            self.facing_right = move_dir.x > 0
        elif move_dir.y > 0:
            self.direction = self.DIR_FRONT
        else:
            self.direction = self.DIR_BACK
    
    def _update_animation(self):
        """Update animation based on state."""
        if self.state == self.STATE_DEAD:
            self.play('death')
            return
        
        if self.state == self.STATE_CHASING:
            if self.velocity.length() > 0:
                anim_name = f'walk_{self.direction}'
            else:
                anim_name = f'idle_{self.direction}'
        elif self.state == self.STATE_WALKING:
            anim_name = f'walk_{self.direction}'
        else:
            anim_name = f'idle_{self.direction}'
        
        self.play(anim_name)
    
    def _try_attack_target(self):
        """Try to deal damage to target if cooldown allows."""
        if self.damage_cooldown <= 0 and self.target:
            self.target.take_damage(self.attack_damage)
            self.damage_cooldown = self.damage_cooldown_duration
    
    def take_damage(self, amount: int):
        """Take damage from attack."""
        if not self._alive:
            return
        
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.die()
    
    def die(self):
        """Handle enemy death."""
        self._alive = False
        self.state = self.STATE_DEAD
        self.velocity = pygame.Vector2(0, 0)
        self.play('death', reset=True)
        if 'death' in self.animations:
            self.animations['death'].loop = False
    
    def get_hitbox(self) -> pygame.Rect:
        """Get the hitbox for player attack detection."""
        return pygame.Rect(
            self.pos.x - self.hitbox_radius,
            self.pos.y - self.hitbox_radius,
            self.hitbox_radius * 2,
            self.hitbox_radius * 2
        )
    
    def get_collision_rect(self) -> pygame.Rect:
        """Get collision rectangle for physics."""
        return pygame.Rect(
            self.pos.x - self.collision_radius,
            self.pos.y - self.collision_radius,
            self.collision_radius * 2,
            self.collision_radius * 2
        )
    
    def _render_letter_surface(self):
        """Pre-render the letter with backdrop for efficient drawing."""
        font = self._get_letter_font()
        backdrop = self._get_letter_backdrop()
        
        # Render white letter
        letter_surf = font.render(self.letter, True, (255, 255, 255))
        
        # Create combined surface with backdrop and centered letter
        self._letter_surface = backdrop.copy()
        letter_x = (backdrop.get_width() - letter_surf.get_width()) // 2
        letter_y = (backdrop.get_height() - letter_surf.get_height()) // 2
        self._letter_surface.blit(letter_surf, (letter_x, letter_y))
    
    def draw_letter(self, screen: pygame.Surface, screen_x: float, screen_y: float):
        """
        Draw the assigned letter above the enemy.
        
        Args:
            screen: The surface to draw on
            screen_x: Enemy center x position in screen coordinates
            screen_y: Enemy center y position in screen coordinates
        """
        if self._letter_surface is None:
            return
        
        # Position letter above enemy (above health bar)
        letter_x = screen_x - self._letter_surface.get_width() // 2
        letter_y = screen_y - ENEMY_LETTER_OFFSET_Y
        
        screen.blit(self._letter_surface, (letter_x, letter_y))


class Slime(Enemy):
    """Slime enemy - basic melee enemy that chases player."""
    
    def __init__(self, x: float, y: float):
        super().__init__(x, y, SLIME_SPRITE_CONFIG)


class Skeleton(Enemy):
    """Skeleton enemy - stronger melee enemy with more health."""
    
    def __init__(self, x: float, y: float):
        super().__init__(x, y, SKELETON_SPRITE_CONFIG)
        
        # Skeleton is tougher than slime
        self.max_health = int(ENEMY_MAX_HEALTH * 1.5)  # 150 HP
        self.health = self.max_health
        self.attack_damage = int(ENEMY_ATTACK_DAMAGE * 1.2)  # 60 damage
        self.chase_speed = ENEMY_CHASE_SPEED * 1.1  # Slightly faster
        self.xp_value = ENEMY_XP_VALUE * 2  # 20 XP
        
        # Larger collision for skeleton
        self.collision_radius = 10
        self.hitbox_radius = 16


def find_enemies_by_letter(enemies, letter: str) -> list:
    """
    Find all alive enemies with the matching letter.
    
    Args:
        enemies: Iterable of Enemy objects (can be sprite group or list)
        letter: The letter to match (case-insensitive)
    
    Returns:
        List of Enemy objects with matching letter that are alive
    """
    letter = letter.upper()
    return [e for e in enemies if e.is_alive and e.letter == letter]


def find_closest_enemy_by_letter(enemies, letter: str, from_pos: pygame.Vector2) -> 'Enemy | None':
    """
    Find the closest alive enemy with the matching letter.
    
    Args:
        enemies: Iterable of Enemy objects
        letter: The letter to match (case-insensitive)
        from_pos: Position to measure distance from (usually player position)
    
    Returns:
        The closest Enemy with matching letter, or None if no match
    """
    matching = find_enemies_by_letter(enemies, letter)
    if not matching:
        return None
    
    # Find closest
    closest = None
    closest_dist = float('inf')
    
    for enemy in matching:
        dist = from_pos.distance_to(enemy.pos)
        if dist < closest_dist:
            closest_dist = dist
            closest = enemy
    
    return closest
