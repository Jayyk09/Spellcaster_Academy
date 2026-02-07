import pygame
import os
import math
import random


class Undine:
    def __init__(self, x, y, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.speed = 70
        
        # Animation settings
        self.frame_count = 6
        self.frame_width = 32
        self.frame_height = 32
        self.scale_size = 64  # Scale up from 32x32 to 64x64
        self.frames = []
        self.current_frame = 0
        self.animation_counter = 0
        self.animation_speed = 5  # Change frame every 5 game frames
        
        # Load undine sprite sheet and extract frames
        image_path = os.path.join('assets', 'sprites', 'monsters', 'undine.png')
        try:
            sprite_sheet = pygame.image.load(image_path).convert_alpha()
            # Extract 6 frames from the sprite sheet (32x32 each, side by side)
            for i in range(self.frame_count):
                frame_rect = pygame.Rect(i * self.frame_width, 0, self.frame_width, self.frame_height)
                frame = sprite_sheet.subsurface(frame_rect).copy()
                # Scale up the frame
                frame = pygame.transform.scale(frame, (self.scale_size, self.scale_size))
                self.frames.append(frame)
        except pygame.error as e:
            print(f"Error loading undine image: {e}")
            # Fallback: create 6 blue water spirit frames
            for i in range(self.frame_count):
                fallback = pygame.Surface((self.scale_size, self.scale_size), pygame.SRCALPHA)
                # Slight variation per frame for animation effect
                offset = i * 2
                pygame.draw.ellipse(fallback, (50, 100, 200), (8, 4 + offset % 4, 32, 40))
                pygame.draw.ellipse(fallback, (100, 180, 255), (14, 10 + offset % 4, 20, 28))
                self.frames.append(fallback)
        
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.pos = pygame.Vector2(x, y)
        
        # Movement state
        self.direction = pygame.Vector2(0, 0)
        self.wander_timer = 0
        self.wander_interval = 1.5  # Change direction more frequently (floaty movement)
        
        # Detection range for chasing player
        self.detection_range = 250  # Larger detection range since it flies
        self.is_chasing = False
        
        # Health
        self.max_health = 30  # Less health than slime
        self.health = self.max_health
        self.alive = True
    
    def _choose_random_direction(self):
        """Pick a random direction to wander."""
        angle = random.uniform(0, 2 * math.pi)
        self.direction = pygame.Vector2(math.cos(angle), math.sin(angle))
    
    def _move_toward_target(self, target_pos):
        """Calculate direction toward a target position."""
        diff = target_pos - self.pos
        distance = diff.length()
        if distance > 0:
            self.direction = diff.normalize()
        return distance
    
    def update(self, dt, player=None, other_undines=None):
        """
        Update undine position and behavior.
        Flies through obstacles but cannot overlap with other undines.
        
        Args:
            dt: Delta time in seconds
            player: Player object to chase (optional)
            other_undines: List of other Undine objects to avoid colliding with (optional)
        """
        if not self.alive:
            return
        
        # Update animation
        self.animation_counter += 1
        if self.animation_counter >= self.animation_speed:
            self.animation_counter = 0
            self.current_frame = (self.current_frame + 1) % self.frame_count
            self.image = self.frames[self.current_frame]
        
        # AI behavior: chase player if in range, otherwise wander
        if player is not None:
            player_pos = pygame.Vector2(player.rect.center)
            distance_to_player = self._move_toward_target(player_pos)
            
            if distance_to_player <= self.detection_range:
                self.is_chasing = True
            else:
                self.is_chasing = False
                # Wander behavior
                self.wander_timer += dt
                if self.wander_timer >= self.wander_interval:
                    self._choose_random_direction()
                    self.wander_timer = 0
        else:
            # No player reference, just wander
            self.is_chasing = False
            self.wander_timer += dt
            if self.wander_timer >= self.wander_interval:
                self._choose_random_direction()
                self.wander_timer = 0
        
        # Calculate movement - no collision detection, flies through everything
        if self.direction.length() > 0:
            # Move faster when chasing
            current_speed = self.speed * 1.5 if self.is_chasing else self.speed
            movement = self.direction * current_speed * dt
            
            self.pos.x += movement.x
            self.pos.y += movement.y
        
        # Keep undine on screen (screen boundaries act as walls)
        self.pos.x = max(self.rect.width / 2, min(self.screen_width - self.rect.width / 2, self.pos.x))
        self.pos.y = max(self.rect.height / 2, min(self.screen_height - self.rect.height / 2, self.pos.y))
        
        self.rect.center = self.pos
        
        # Collision with other undines - push apart if overlapping
        if other_undines:
            for other in other_undines:
                if other is self or not other.alive:
                    continue
                if self.rect.colliderect(other.rect):
                    # Calculate push direction
                    diff = self.pos - other.pos
                    if diff.length() > 0:
                        push_dir = diff.normalize()
                    else:
                        # If exactly overlapping, push in random direction
                        angle = random.uniform(0, 2 * math.pi)
                        push_dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                    
                    # Push this undine away from the other
                    push_strength = 2.0
                    self.pos += push_dir * push_strength
                    self.rect.center = self.pos
    
    def take_damage(self, amount):
        """Apply damage to the undine."""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False
    
    def check_collision_with_player(self, player):
        """Check if undine is colliding with the player."""
        return self.rect.colliderect(player.rect)
    
    def draw(self, surface):
        """Draw the undine to the screen."""
        if self.alive:
            surface.blit(self.image, self.rect)
            
            # Optional: Draw health bar above undine
            if self.health < self.max_health:
                bar_width = 40
                bar_height = 4
                bar_x = self.rect.centerx - bar_width // 2
                bar_y = self.rect.top - 8
                
                # Background (red)
                pygame.draw.rect(surface, (200, 50, 50), (bar_x, bar_y, bar_width, bar_height))
                # Health (blue for undine)
                health_width = int(bar_width * (self.health / self.max_health))
                pygame.draw.rect(surface, (50, 150, 255), (bar_x, bar_y, health_width, bar_height))


class UndineManager:
    """Manages multiple undines for spawning and group updates."""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.undines = []
    
    def spawn_undine(self, x, y):
        """Spawn a new undine at the specified position."""
        undine = Undine(x, y, self.screen_width, self.screen_height)
        self.undines.append(undine)
        return undine
    
    def spawn_random(self, count=1, margin=50):
        """Spawn undines at random positions, avoiding screen edges."""
        for _ in range(count):
            x = random.randint(margin, self.screen_width - margin)
            y = random.randint(margin, self.screen_height - margin)
            self.spawn_undine(x, y)
    
    def update(self, dt, player=None):
        """Update all undines. They collide with each other but fly through obstacles."""
        for undine in self.undines:
            undine.update(dt, player, self.undines)
        
        # Remove dead undines
        self.undines = [u for u in self.undines if u.alive]
    
    def draw(self, surface):
        """Draw all undines."""
        for undine in self.undines:
            undine.draw(surface)
    
    def check_player_collision(self, player):
        """Check if any undine is colliding with the player. Returns list of colliding undines."""
        return [u for u in self.undines if u.alive and u.check_collision_with_player(player)]
    
    def get_alive_count(self):
        """Return number of living undines."""
        return len([u for u in self.undines if u.alive])
