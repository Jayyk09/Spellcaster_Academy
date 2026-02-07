"""Enemy entities with AI behavior."""
import pygame
import random
import math
from core.animation import AnimatedSprite
from config.settings import (
    SLIME_SPRITE_CONFIG, SKELETON_SPRITE_CONFIG,
    ENEMY_CHASE_SPEED, ENEMY_IDLE_SPEED,
    ENEMY_MAX_HEALTH, ENEMY_ATTACK_DAMAGE, ENEMY_DETECTION_RADIUS,
    ENEMY_ATTACK_RANGE, ENEMY_DAMAGE_COOLDOWN, ENEMY_XP_VALUE
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
    
    def __init__(self, x: float, y: float, sprite_config: dict):
        super().__init__(x, y, sprite_config)
        
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
