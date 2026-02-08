"""Lich boss enemy entity with AI behavior."""
import pygame
import random
import math
import os
from core.animation import AnimatedSprite
from entities.spell import SpellProjectile
from entities.enemy import Skeleton
from config.settings import (
    LICH_SPRITE_CONFIG, LICH_LIGHTNING_CONFIG,
    LICH_MAX_HEALTH, LICH_X_OFFSET, LICH_SPEED_FACTOR,
    LICH_ATTACK_COOLDOWN_MIN, LICH_ATTACK_COOLDOWN_MAX,
    LICH_LIGHTNING_DAMAGE,
    PLAYER_SPEED,
    ENEMY_LETTER_OFFSET_Y, ENEMY_LETTER_BACKDROP_PATH,
    FONTS_DIR,
    SKELETON_SPRITE_CONFIG, ENEMY_MAX_HEALTH, ENEMY_ATTACK_DAMAGE,
    ENEMY_CHASE_SPEED,
    WORLD_WIDTH, WORLD_HEIGHT,
)


class LichLightning(AnimatedSprite):
    """Lightning bolt projectile fired by the Lich."""

    def __init__(self, x: float, y: float, direction: pygame.Vector2):
        super().__init__(x, y, LICH_LIGHTNING_CONFIG)
        self.speed = 150  # pixels per second
        self.damage = LICH_LIGHTNING_DAMAGE
        self.alive = True
        self.lifetime = 3.0
        self.direction = direction
        self.velocity = direction * self.speed
        self.collision_radius = 16

        # Calculate rotation angle so sprite faces direction of travel
        self.rotation_angle = -math.degrees(math.atan2(direction.y, direction.x))

        # Play the lightning animation
        if 'lightning' in self.animations:
            self.play('lightning')

    def update(self, dt: float):
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
            frame = anim.get_current_frame()
            # Rotate the frame to face direction of travel
            if self.rotation_angle != 0:
                frame = pygame.transform.rotate(frame, self.rotation_angle)
            self.image = frame

        # Update rect position
        if self.rect is not None:
            self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def get_hitbox(self) -> pygame.Rect:
        """Get axis-aligned bounding box (for broad phase collision)."""
        # Return AABB that contains the rotated hitbox
        corners = self.get_hitbox_corners()
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def get_hitbox_corners(self) -> list[tuple[float, float]]:
        """Get the 4 corners of the rotated hitbox (64x10)."""
        # Hitbox dimensions: 64 long x 10 tall
        half_length = 32
        half_height = 5
        
        # Rotation angle in radians (same as sprite rotation)
        angle_rad = math.radians(-self.rotation_angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # Local corners (unrotated, centered at origin)
        local_corners = [
            (-half_length, -half_height),
            (half_length, -half_height),
            (half_length, half_height),
            (-half_length, half_height),
        ]
        
        # Rotate and translate to world position
        world_corners = []
        for lx, ly in local_corners:
            wx = self.pos.x + lx * cos_a - ly * sin_a
            wy = self.pos.y + lx * sin_a + ly * cos_a
            world_corners.append((wx, wy))
        
        return world_corners

    def destroy(self):
        self.alive = False

    @property
    def is_alive(self) -> bool:
        return self.alive


class Lich(AnimatedSprite):
    """Lich boss enemy - stays to the left of the player, casts lightning and summons skeletons."""

    # States
    STATE_IDLE = 'idle'
    STATE_CASTING = 'casting'
    STATE_ATTACKING = 'attacking'  # third_attack (lightning)
    STATE_BLOCKING = 'blocking'    # long_spin_attack variants
    STATE_HURT = 'hurt'
    STATE_DEAD = 'dead'

    # Class-level font for letter rendering (shared with Enemy)
    _letter_font = None
    _letter_backdrop = None

    @classmethod
    def _get_letter_font(cls):
        if cls._letter_font is None:
            font_path = os.path.join(FONTS_DIR, 'Alkhemikal.ttf')
            try:
                cls._letter_font = pygame.font.Font(font_path, 24)
            except Exception:
                cls._letter_font = pygame.font.Font(None, 24)
        return cls._letter_font

    @classmethod
    def _get_letter_backdrop(cls):
        if cls._letter_backdrop is None:
            try:
                original = pygame.image.load(ENEMY_LETTER_BACKDROP_PATH).convert_alpha()
                cls._letter_backdrop = pygame.transform.scale(original, (36, 28))
            except Exception:
                cls._letter_backdrop = pygame.Surface((36, 28), pygame.SRCALPHA)
                cls._letter_backdrop.fill((20, 40, 50, 200))
        return cls._letter_backdrop

    def __init__(self, x: float, y: float, letter: str | None = None,
                 wave_letters: list[str] | None = None):
        super().__init__(x, y, LICH_SPRITE_CONFIG)

        # Available letters for this wave (used to rotate letter on hit & for summoned skeletons)
        self.wave_letters = wave_letters if wave_letters else ['A', 'B', 'C', 'D', 'E']

        # Letter assignment
        if letter is not None:
            self.letter = letter.upper()
        else:
            self.letter = random.choice(self.wave_letters)
        self._letter_surface = None
        self._render_letter_surface()

        # Health - takes 5 hits to kill
        self.max_health = LICH_MAX_HEALTH
        self.health = LICH_MAX_HEALTH

        # Movement
        self.speed = PLAYER_SPEED * LICH_SPEED_FACTOR  # 60% of player speed
        self.velocity = pygame.Vector2(0, 0)
        self.x_offset = LICH_X_OFFSET  # Stay 250px to the left of player

        # State
        self.state = self.STATE_IDLE
        self._alive = True

        # Attack cooldown
        self.attack_cooldown = random.uniform(LICH_ATTACK_COOLDOWN_MIN, LICH_ATTACK_COOLDOWN_MAX)
        self.attack_timer = self.attack_cooldown  # Start with a full cooldown

        # Hurt animation timer
        self._hurt_timer = 0.0
        self._hurt_duration = 0.4  # seconds

        # Current attack animation tracking
        self._attack_anim_playing = False

        # Target (player)
        self.target = None

        # Projectiles and summoned skeletons
        self.lightning_bolts: list[LichLightning] = []
        self.summoned_skeletons: list[Skeleton] = []

        # Whether lightning has been fired during current attack animation
        self._lightning_fired = False

        # Blocking state
        self.is_blocking = False

        # Pending skeletons to be added to the world this frame
        self.pending_skeletons: list[Skeleton] = []

        # Collision
        self.collision_radius = 20
        self.hitbox_radius = 40

        # Play initial animation
        self.play('idle')

    @property
    def is_alive(self) -> bool:
        return self._alive

    def set_target(self, target):
        self.target = target

    # ── Update ──────────────────────────────────────────────────────────

    def update(self, dt: float):
        if self.state == self.STATE_DEAD:
            super().update(dt)
            return

        # Update attack cooldown
        if self.attack_timer > 0:
            self.attack_timer -= dt

        # State machine
        if self.state == self.STATE_HURT:
            self._update_hurt(dt)
        elif self.state in (self.STATE_CASTING, self.STATE_ATTACKING, self.STATE_BLOCKING):
            self._update_attack_animation(dt)
        else:
            # Idle state — move and decide on attacks
            self._update_movement(dt)
            self._try_choose_attack()

        # Update lightning bolts
        for bolt in list(self.lightning_bolts):
            bolt.update(dt)
            if not bolt.is_alive:
                self.lightning_bolts.remove(bolt)

        # Call parent update (animation frame advance + rect sync)
        super().update(dt)

    # ── Movement ────────────────────────────────────────────────────────

    def _update_movement(self, dt: float):
        """Stay 250 px to the left of the player and mirror the player's Y position."""
        if not self.target:
            return

        target_x = self.target.pos.x - self.x_offset
        target_y = self.target.pos.y

        # Horizontal: move faster (3x) to guarantee the lich stays left of the player
        dx = target_x - self.pos.x
        horizontal_speed = self.speed * 3.0
        move_x = min(abs(dx), horizontal_speed * dt) * (1 if dx > 0 else -1)
        self.pos.x += move_x

        # Hard clamp: never go to the right of the player
        if self.pos.x > self.target.pos.x - 60:
            self.pos.x = self.target.pos.x - 60

        # Mirror the player's Y position (move toward same row)
        dy = target_y - self.pos.y
        move_y = min(abs(dy), self.speed * dt) * (1 if dy > 0 else -1)
        self.pos.y += move_y

        # Clamp to world bounds
        margin = 32
        self.pos.x = max(margin, min(WORLD_WIDTH - margin, self.pos.x))
        self.pos.y = max(margin, min(WORLD_HEIGHT - margin, self.pos.y))

    # ── Attack selection ────────────────────────────────────────────────

    def _try_choose_attack(self):
        """Choose an attack if cooldown has elapsed."""
        if self.attack_timer > 0 or not self.target:
            return

        # Pick a random attack: lightning (50%) or casting/summon (50%)
        roll = random.random()
        if roll < 0.5:
            self._start_lightning_attack()
        else:
            self._start_casting_attack()

    def _start_lightning_attack(self):
        """Begin the third_attack animation and fire lightning at midpoint."""
        self.state = self.STATE_ATTACKING
        self._attack_anim_playing = True
        self._lightning_fired = False
        self.play('third_attack', reset=True)
        if 'third_attack' in self.animations:
            self.animations['third_attack'].loop = False

    def _start_casting_attack(self):
        """Begin the casting animation to summon skeletons."""
        self.state = self.STATE_CASTING
        self._attack_anim_playing = True
        self.play('casting', reset=True)
        if 'casting' in self.animations:
            self.animations['casting'].loop = False

    def start_block(self):
        """Begin a random long_spin_attack variant as a block."""
        variant = random.choice(['long_spin_attack', 'long_spin_ghosts', 'long_spin_symbols'])
        self.state = self.STATE_BLOCKING
        self.is_blocking = True
        self._attack_anim_playing = True
        self.play(variant, reset=True)
        if variant in self.animations:
            self.animations[variant].loop = False

    # ── Attack animation updates ────────────────────────────────────────

    def _update_attack_animation(self, dt: float):
        """Tick attack/casting/blocking animations and fire effects at the right time."""
        anim = self.get_current_animation()
        if anim is None:
            self._finish_attack()
            return

        # Lightning attack: fire bolt at the end of the animation (full startup warning)
        if self.state == self.STATE_ATTACKING and not self._lightning_fired:
            total_frames = len(anim.frames)
            if anim.current_frame >= total_frames - 1:
                self._fire_lightning()
                self._lightning_fired = True

        # When the animation finishes
        if anim.finished:
            if self.state == self.STATE_CASTING:
                self._summon_skeletons()
            self._finish_attack()

    def _finish_attack(self):
        """Return to idle after an attack finishes."""
        self.state = self.STATE_IDLE
        self.is_blocking = False
        self._attack_anim_playing = False
        self.attack_timer = random.uniform(LICH_ATTACK_COOLDOWN_MIN, LICH_ATTACK_COOLDOWN_MAX)
        self.play('idle')

    # ── Effects ─────────────────────────────────────────────────────────

    def _fire_lightning(self):
        """Spawn a lightning bolt that fires toward the player's current position."""
        if not self.target:
            return
        
        # Calculate direction toward player
        direction = pygame.Vector2(
            self.target.pos.x - self.pos.x,
            self.target.pos.y - self.pos.y
        )
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            # Fallback to rightward if somehow at same position
            direction = pygame.Vector2(1, 0)
        
        bolt = LichLightning(self.pos.x + 60, self.pos.y, direction)
        self.lightning_bolts.append(bolt)

    def _summon_skeletons(self):
        """Summon 1-3 skeletons near the lich and queue them for world pickup."""
        count = random.randint(1, 3)
        for _ in range(count):
            offset_x = random.uniform(-100, 100)
            offset_y = random.uniform(-100, 100)
            sx = self.pos.x + offset_x
            sy = self.pos.y + offset_y
            # Clamp to world bounds
            sx = max(32, min(WORLD_WIDTH - 32, sx))
            sy = max(32, min(WORLD_HEIGHT - 32, sy))
            skeleton = Skeleton(sx, sy, letter=random.choice(self.wave_letters))
            skeleton.set_target(self.target)
            self.summoned_skeletons.append(skeleton)
            self.pending_skeletons.append(skeleton)

    # ── Damage / Death ──────────────────────────────────────────────────

    def take_damage(self, amount: int = 1):
        """Take one hit (lich counts hits, not damage amount). Triggers hurt anim."""
        if not self._alive or self.state == self.STATE_DEAD:
            return
        if self.is_blocking:
            return  # Blocked!

        self.health -= 1
        if self.health <= 0:
            self.health = 0
            self.die()
        else:
            # Change to a different letter on each hit
            other_letters = [l for l in self.wave_letters if l != self.letter]
            if other_letters:
                self.letter = random.choice(other_letters)
            else:
                self.letter = random.choice(self.wave_letters)
            self._render_letter_surface()

            self.state = self.STATE_HURT
            self._hurt_timer = self._hurt_duration
            self.play('hurt', reset=True)
            if 'hurt' in self.animations:
                self.animations['hurt'].loop = False

    def _update_hurt(self, dt: float):
        """Return to idle when hurt animation ends."""
        self._hurt_timer -= dt
        if self._hurt_timer <= 0 or self.is_animation_finished():
            self.state = self.STATE_IDLE
            self.play('idle')

    def die(self):
        self._alive = False
        self.state = self.STATE_DEAD
        self.velocity = pygame.Vector2(0, 0)
        self.is_blocking = False
        self.play('death', reset=True)
        if 'death' in self.animations:
            self.animations['death'].loop = False

    # ── Collision helpers ───────────────────────────────────────────────

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(
            self.pos.x - self.hitbox_radius,
            self.pos.y - self.hitbox_radius,
            self.hitbox_radius * 2,
            self.hitbox_radius * 2,
        )

    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.pos.x - self.collision_radius,
            self.pos.y - self.collision_radius,
            self.collision_radius * 2,
            self.collision_radius * 2,
        )

    # ── Letter rendering (same pattern as Enemy) ────────────────────────

    def _render_letter_surface(self):
        font = self._get_letter_font()
        backdrop = self._get_letter_backdrop()
        letter_surf = font.render(self.letter, True, (255, 255, 255))
        self._letter_surface = backdrop.copy()
        letter_x = (backdrop.get_width() - letter_surf.get_width()) // 2
        letter_y = (backdrop.get_height() - letter_surf.get_height()) // 2
        self._letter_surface.blit(letter_surf, (letter_x, letter_y))

    def draw_letter(self, screen: pygame.Surface, screen_x: float, screen_y: float):
        if self._letter_surface is None:
            return
        letter_x = screen_x - self._letter_surface.get_width() // 2
        letter_y = screen_y - ENEMY_LETTER_OFFSET_Y - 60  # Extra offset for large boss sprite
        screen.blit(self._letter_surface, (letter_x, letter_y))
