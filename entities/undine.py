import pygame
import os
import math
import random
import string
from config.settings import FONTS_DIR, ENEMY_LETTER_OFFSET_Y, ENEMY_LETTER_BACKDROP_PATH, SPELL_SPEED, SPELL_DAMAGE
from entities.spell import SpellProjectile
from core.sound_manager import sound_manager


class Undine:
    # Class-level font for letter rendering (loaded once)
    _letter_font = None
    _letter_backdrop = None
    
    @classmethod
    def _get_letter_font(cls):
        """Get or initialize the letter font (lazy loading)."""
        if cls._letter_font is None:
            font_path = os.path.join(FONTS_DIR, 'Alkhemikal.ttf')
            try:
                cls._letter_font = pygame.font.Font(font_path, 24)  # Larger font for undine
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
    
    def __init__(self, x, y, screen_width, screen_height, letter: str | None = None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.speed = 70
        
        # Assign letter (use provided letter or random A-E as fallback)
        if letter is not None:
            self.letter = letter.upper()
        else:
            self.letter = random.choice(['A', 'B', 'C', 'D', 'E'])
        self._letter_surface = None  # Pre-rendered letter surface
        self._render_letter_surface()
        
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
        
        # Distance keeping behavior
        self.ideal_distance = 150  # Keep this distance from player
        self.distance_tolerance = 25  # Tolerance for distance keeping
        
        # Spell casting
        self.cast_cooldown = 0.0
        self.cast_interval = 3.0  # Cast every 3 seconds
        self.initial_attack_delay = 3.0  # Wait 3 seconds before first attack
        self.spell_damage = int(SPELL_DAMAGE / 3)  # 33% of player spell damage (50)
        self.spell_type = 'air'  # Use air spells
        self.spells_cast = []  # List of spells cast by this undine
        
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
        Keeps distance from player and casts spells.
        Note: Collision detection is handled by the world scene.
        
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
        
        # Update spell cooldown and initial attack delay
        if self.cast_cooldown > 0:
            self.cast_cooldown -= dt
        if self.initial_attack_delay > 0:
            self.initial_attack_delay -= dt
        
        # AI behavior: keep distance and cast spells
        if player is not None:
            player_pos = pygame.Vector2(player.rect.center)
            distance_to_player = self.pos.distance_to(player_pos)
            
            if distance_to_player <= self.detection_range:
                self.is_chasing = True
                
                # Distance keeping behavior
                if distance_to_player < self.ideal_distance - self.distance_tolerance:
                    # Too close - move away from player
                    direction_away = self.pos - player_pos
                    if direction_away.length() > 0:
                        self.direction = direction_away.normalize()
                elif distance_to_player > self.ideal_distance + self.distance_tolerance:
                    # Too far - move toward player
                    self._move_toward_target(player_pos)
                else:
                    # At ideal distance - stop moving
                    self.direction = pygame.Vector2(0, 0)
                    
                # Try to cast spell at player (only after initial delay)
                if self.cast_cooldown <= 0 and self.initial_attack_delay <= 0:
                    self._cast_spell_at_player(player_pos)
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
        
        # Calculate movement
        if self.direction.length() > 0:
            # Move faster when chasing
            current_speed = self.speed * 1.5 if self.is_chasing else self.speed
            movement = self.direction * current_speed * dt
            
            self.pos.x += movement.x
            self.pos.y += movement.y
        
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
    
    def _cast_spell_at_player(self, player_pos: pygame.Vector2):
        """Cast a spell at the player."""
        # Calculate direction from undine to player
        direction = player_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = pygame.Vector2(1, 0)  # Default to right if same position
        
        # Create spell projectile at undine's position
        spell = SpellProjectile(
            self.pos.x, self.pos.y,
            self.spell_type,
            direction,
            None  # No letter restriction - can hit player
        )
        # Override damage for undine spells (50% of player spell damage)
        spell.damage = self.spell_damage
        
        self.spells_cast.append(spell)
        self.cast_cooldown = self.cast_interval
        sound_manager.play_undine_spell()
    
    def take_damage(self, amount):
        """Apply damage to the undine."""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False
    
    def check_collision_with_player(self, player):
        """Check if undine is colliding with the player."""
        return self.rect.colliderect(player.rect)
    
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
        Draw the assigned letter above the undine.
        
        Args:
            screen: The surface to draw on
            screen_x: Undine center x position in screen coordinates
            screen_y: Undine center y position in screen coordinates
        """
        if self._letter_surface is None:
            return
        
        # Position letter above undine (above health bar area)
        letter_x = screen_x - self._letter_surface.get_width() // 2
        letter_y = screen_y - ENEMY_LETTER_OFFSET_Y - 15  # Extra offset for undine (they float higher)
        
        screen.blit(self._letter_surface, (letter_x, letter_y))
    
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
        self.spells = []  # Spells cast by all undines
    
    def spawn_undine(self, x, y, letter: str | None = None):
        """Spawn a new undine at the specified position."""
        undine = Undine(x, y, self.screen_width, self.screen_height, letter=letter)
        self.undines.append(undine)
        return undine
    
    def spawn_random(self, count=1, margin=50, letters: list[str] | None = None):
        """
        Spawn undines at random positions, avoiding screen edges.
        
        Args:
            count: Number of undines to spawn
            margin: Minimum distance from screen edges
            letters: Optional list of letters to assign (randomly picked from pool)
        """
        for _ in range(count):
            x = random.randint(margin, self.screen_width - margin)
            y = random.randint(margin, self.screen_height - margin)
            letter = random.choice(letters) if letters else None
            self.spawn_undine(x, y, letter=letter)
    
    def spawn_near(self, count=1, center_x=0, center_y=0, radius=200, letters: list[str] | None = None, region_bounds: dict | None = None):
        """
        Spawn undines near a specific position within optional region bounds.

        Args:
            count: Number of undines to spawn
            center_x: Center x position
            center_y: Center y position
            radius: Maximum distance from center
            letters: Optional list of letters to assign (randomly picked from pool)
            region_bounds: Optional dict with 'min_x', 'max_x', 'min_y', 'max_y' to constrain spawn
        """
        spawned = []
        for _ in range(count):
            # Random position within radius of center
            angle = random.uniform(0, 2 * 3.14159)
            dist = random.uniform(50, radius)
            x = center_x + math.cos(angle) * dist
            y = center_y + math.sin(angle) * dist

            # Clamp to region bounds if provided
            if region_bounds:
                margin = 50
                x = max(region_bounds['min_x'] + margin, min(region_bounds['max_x'] - margin, x))
                y = max(region_bounds['min_y'] + margin, min(region_bounds['max_y'] - margin, y))
            else:
                # Clamp to screen bounds
                x = max(50, min(self.screen_width - 50, x))
                y = max(50, min(self.screen_height - 50, y))

            letter = random.choice(letters) if letters else None
            undine = self.spawn_undine(x, y, letter=letter)
            if undine:
                spawned.append(undine)

        return spawned
    
    def update(self, dt, player=None):
        """Update all undines and their spells. They collide with each other but fly through obstacles."""
        # Update undines
        for undine in self.undines:
            undine.update(dt, player, self.undines)
            
            # Collect any new spells cast by undines
            if undine.alive and undine.spells_cast:
                for spell in undine.spells_cast:
                    self.spells.append(spell)
                undine.spells_cast.clear()
        
        # Update undine spells
        for spell in list(self.spells):
            spell.update(dt)
            if not spell.is_alive:
                self.spells.remove(spell)
        
        # Remove dead undines
        self.undines = [u for u in self.undines if u.alive]
    
    def draw(self, surface):
        """Draw all undines and their spells."""
        # Draw spells first (so they appear behind undines)
        for spell in self.spells:
            if spell.is_alive:
                surface.blit(spell.image, spell.rect)
        
        # Draw undines
        for undine in self.undines:
            undine.draw(surface)
    
    def check_player_collision(self, player):
        """Check if any undine is colliding with the player. Returns list of colliding undines."""
        return [u for u in self.undines if u.alive and u.check_collision_with_player(player)]
    
    def get_alive_count(self):
        """Return number of living undines."""
        return len([u for u in self.undines if u.alive])
