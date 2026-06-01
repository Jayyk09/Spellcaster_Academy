"""Survival scene - endless waves in a colosseum arena."""

import pygame
import random
import string

from core.scene import Scene
from core.game_state import game_state
from core.ui import HUD, DeathPanel, CameraLetterDisplay, WaveDisplay, SignReferencePanel
from core.camera import Camera
from core.map_loader import load_map_data, create_tilemap_from_data, get_spawn_points
from entities.player import Player
from entities.enemy import Slime, Skeleton, find_closest_enemy_by_letter
from entities.undine import UndineManager
from entities.spell import SpellProjectile
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TILE_SIZE, SCALE, CAMERA_DRAG_MARGIN,
    CAMERA_ENABLED, SPELL_TYPES, DEBUG_SHOW_HITBOXES,
    CAMERA_SHOW_PREVIEW, CAMERA_PREVIEW_CORNER,
    CAMERA_PREVIEW_WIDTH, CAMERA_PREVIEW_HEIGHT,
    CAMERA_PREVIEW_MARGIN_X, CAMERA_PREVIEW_MARGIN_Y,
)
from core.sound_manager import sound_manager


class SurvivalScene(Scene):
    """Endless Survival mode: fight randomized waves with intermission previews."""

    def __init__(self, game, **kwargs):
        super().__init__(game)

        # Load map data
        self.map_data = load_map_data('survival_arena')
        if self.map_data is None:
            raise RuntimeError("Failed to load survival arena map data")

        # Create tilemap
        self.tilemap = create_tilemap_from_data(self.map_data)

        # Calculate world dimensions in pixels (at scale)
        tile_size = self.map_data.get('tile_size', TILE_SIZE)
        width_tiles = self.map_data.get('width', 33)
        height_tiles = self.map_data.get('height', 33)
        self.world_pixel_width = width_tiles * tile_size * SCALE
        self.world_pixel_height = height_tiles * tile_size * SCALE

        # Create camera
        self.camera = Camera(
            SCREEN_WIDTH, SCREEN_HEIGHT,
            self.world_pixel_width, self.world_pixel_height
        )
        self.camera.drag_margin = CAMERA_DRAG_MARGIN

        # Pre-render and scale the base tilemap layers
        self._render_scaled_background()

        # Pre-render and scale ysort decoration objects
        self._prepare_decorations()

        # Spawn points
        spawn_points = get_spawn_points(self.map_data)

        # Create player at spawn point
        player_spawn = spawn_points.get('player_start', {'x': 16, 'y': 16})
        start_x = player_spawn['x'] * tile_size * SCALE + (tile_size * SCALE // 2)
        start_y = player_spawn['y'] * tile_size * SCALE + (tile_size * SCALE // 2)
        self.player = Player(start_x, start_y)

        # Set camera to follow player
        self.camera.set_target(self.player.pos, self.player.velocity)
        self.camera.center_on(self.player.pos.x, self.player.pos.y)

        # Enemy groups
        self.enemies = pygame.sprite.Group()

        # Undines
        self.undine_manager = UndineManager(self.world_pixel_width, self.world_pixel_height)

        # All sprites for rendering
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)

        # Spell projectiles
        self.spells = pygame.sprite.Group()

        # UI
        self.hud = HUD()
        self.death_panel = DeathPanel()
        self.show_death_dialog = False
        self.wave_display = WaveDisplay()
        self.sign_panel = SignReferencePanel()

        # Camera input (ASL detection)
        self.camera_input = None
        self.camera_letter_display = CameraLetterDisplay()
        self._no_target_timer = 0.0
        self._no_target_letter = None
        self._camera_initialized = False
        self._waiting_for_camera_ready = False
        self._camera_ready_font = pygame.font.Font(None, 36)

        # Spell type cycling
        self._spell_type_index = 0

        # Fonts
        self.font = pygame.font.Font(None, 24)

        # Spawn points for enemies
        self._enemy_spawn_tiles = spawn_points.get('enemy_spawns', [])
        if not isinstance(self._enemy_spawn_tiles, list):
            self._enemy_spawn_tiles = []

        # Survival wave state
        self.time_between_waves = 5.0
        self.current_wave_number = 0  # 0 means none spawned yet
        self.next_wave_number = 1
        self._in_intermission = True
        self._intermission_timer = self.time_between_waves
        self.unlocked_letters: set[str] = set()

        # Start with a preview for wave 1
        self._start_intermission(self.next_wave_number)

    def on_enter(self):
        """Resume theme music and initialize camera."""
        sound_manager.play_theme()
        self._initialize_camera()

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        # Handle camera startup pause
        if self._waiting_for_camera_ready:
            if event.key == pygame.K_RETURN:
                camera_ready = self.camera_input is not None and self.camera_input.is_available()
                camera_failed = (
                    self.camera_input is None or
                    self.camera_input.get_error_message() is not None
                )
                if camera_ready or camera_failed:
                    self._waiting_for_camera_ready = False
            return

        # Handle death dialog input
        if self.show_death_dialog:
            self.next_scene = 'menu'
            return

        if event.key == pygame.K_ESCAPE:
            self.next_scene = 'menu'

    def _initialize_camera(self):
        """Initialize shared camera input once per scene."""
        if self._camera_initialized or not CAMERA_ENABLED:
            return

        self._camera_initialized = True
        self.camera_input = self.game.get_camera_input()

        camera_already_running = (
            self.camera_input is not None and
            self.camera_input.is_available()
        )
        self._waiting_for_camera_ready = CAMERA_ENABLED and not camera_already_running

    # ── Wave logic ─────────────────────────────────────────────────────

    def _get_wave_letters(self, wave_number: int) -> list[str]:
        """Wave 1: A+B, Wave 2 adds C, Wave 3 adds D, ... up to Z."""
        count = max(2, wave_number + 1)
        count = min(len(string.ascii_uppercase), count)
        return list(string.ascii_uppercase[:count])

    def _start_intermission(self, upcoming_wave: int):
        """Enter the 5s between-wave preview state."""
        self._in_intermission = True
        self._intermission_timer = self.time_between_waves
        self.next_wave_number = max(1, upcoming_wave)

        letters = self._get_wave_letters(self.next_wave_number)
        self.unlocked_letters = set(letters)

        labels = {'B': 'Block'} if 'B' in letters else {}
        self.sign_panel.set_letters(letters, labels=labels)
        self.sign_panel.show(title=f"Wave {self.next_wave_number} Preview")

        # Clear lingering enemy spells for a fair intermission
        self.undine_manager.spells.clear()

    def _begin_wave(self, wave_number: int):
        """Spawn the next wave and hide preview UI."""
        self.current_wave_number = max(1, wave_number)
        self._in_intermission = False
        self.sign_panel.hide()

        # Ensure unlocked letters match the wave
        letters = self._get_wave_letters(self.current_wave_number)
        self.unlocked_letters = set(letters)

        self._spawn_wave(self.current_wave_number)

    def _generate_wave_counts(self, wave_number: int) -> tuple[int, int, int]:
        """Return (slimes, skeletons, undines) for a wave."""
        base_total = 4 + wave_number
        jitter = max(1, int(base_total * 0.25))
        total = random.randint(max(1, base_total - jitter), base_total + jitter)
        total = max(1, min(total, 50))

        skeleton_frac = min(0.5, 0.10 + wave_number * 0.02)
        undine_frac = min(0.25, max(0, wave_number - 3) * 0.02)

        skeletons = int(total * skeleton_frac)
        undines = int(total * undine_frac)

        if skeletons > 0:
            skeletons = max(0, skeletons + random.randint(-1, 1))
        if undines > 0:
            undines = max(0, undines + random.randint(-1, 1))

        # Ensure at least 1 slime and that we don't exceed total
        if skeletons + undines > total - 1:
            overflow = skeletons + undines - (total - 1)
            reduce_skel = min(overflow, skeletons)
            skeletons -= reduce_skel
            overflow -= reduce_skel
            undines = max(0, undines - overflow)

        slimes = max(1, total - skeletons - undines)
        return slimes, skeletons, undines

    def _pick_enemy_spawn_pos(self) -> pygame.Vector2:
        """Pick a spawn point (outside the arena) in world pixels."""
        tile_px = self.tilemap.tile_size * SCALE

        if not self._enemy_spawn_tiles:
            # Fallback: corners
            choices = [
                {'x': 1, 'y': 1},
                {'x': self.tilemap.width - 2, 'y': 1},
                {'x': 1, 'y': self.tilemap.height - 2},
                {'x': self.tilemap.width - 2, 'y': self.tilemap.height - 2},
            ]
            spawn = random.choice(choices)
        else:
            spawn = random.choice(self._enemy_spawn_tiles)

        x = spawn.get('x', 1) * tile_px + (tile_px // 2)
        y = spawn.get('y', 1) * tile_px + (tile_px // 2)
        return pygame.Vector2(x, y)

    def _generate_letter_assignments(self, total: int, letters: list[str]) -> list[str]:
        """Generate a list of letters with at least one of each (when possible)."""
        if total <= 0:
            return []
        if not letters:
            return ['A'] * total

        assignments: list[str] = []
        if total >= len(letters):
            assignments.extend(letters)
            remaining = total - len(letters)
        else:
            remaining = total

        for _ in range(remaining):
            assignments.append(random.choice(letters))

        random.shuffle(assignments)
        return assignments

    def _spawn_wave(self, wave_number: int):
        """Spawn enemies for this wave."""
        wave_letters = self._get_wave_letters(wave_number)
        enemy_letters = [l for l in wave_letters if l != 'B']
        if not enemy_letters:
            enemy_letters = ['A']

        slime_count, skeleton_count, undine_count = self._generate_wave_counts(wave_number)
        total = slime_count + skeleton_count + undine_count
        letter_assignments = self._generate_letter_assignments(total, enemy_letters)

        # Spawn slimes
        for _ in range(slime_count):
            pos = self._pick_enemy_spawn_pos()
            letter = letter_assignments.pop() if letter_assignments else random.choice(enemy_letters)
            enemy = Slime(pos.x, pos.y, letter=letter)
            enemy.set_target(self.player)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

        # Spawn skeletons
        for _ in range(skeleton_count):
            pos = self._pick_enemy_spawn_pos()
            letter = letter_assignments.pop() if letter_assignments else random.choice(enemy_letters)
            enemy = Skeleton(pos.x, pos.y, letter=letter)
            enemy.set_target(self.player)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

        # Spawn undines
        for _ in range(undine_count):
            pos = self._pick_enemy_spawn_pos()
            letter = letter_assignments.pop() if letter_assignments else random.choice(enemy_letters)
            self.undine_manager.spawn_undine(pos.x, pos.y, letter=letter)

    def _is_wave_cleared(self) -> bool:
        alive_enemies = any(e.is_alive for e in self.enemies)
        alive_undines = any(u.alive for u in self.undine_manager.undines)
        return not alive_enemies and not alive_undines

    # ── Update ─────────────────────────────────────────────────────────

    def update(self, dt: float):
        # Pause while waiting for camera
        if self._waiting_for_camera_ready:
            return

        # Stop updates when dead
        if self.show_death_dialog:
            return

        # Get input
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)

        # Process camera input
        self._process_camera_input(dt)

        # Store old position for collision resolution
        old_pos = pygame.Vector2(self.player.pos)

        # Update player
        self.player.update(dt)

        # Clamp player to world bounds
        margin = 24 * SCALE // 3
        self.player.pos.x = max(margin, min(self.world_pixel_width - margin, self.player.pos.x))
        self.player.pos.y = max(margin, min(self.world_pixel_height - margin, self.player.pos.y))

        # Tile/decor collision with sliding
        self._resolve_collision_with_slide(self.player, old_pos)

        # Update camera
        self.camera.update(dt)

        # Update enemies
        for enemy in list(self.enemies):
            old_enemy_pos = pygame.Vector2(enemy.pos)
            enemy.update(dt)

            enemy_margin = 16 * SCALE // 3
            enemy.pos.x = max(enemy_margin, min(self.world_pixel_width - enemy_margin, enemy.pos.x))
            enemy.pos.y = max(enemy_margin, min(self.world_pixel_height - enemy_margin, enemy.pos.y))

            self._resolve_collision_with_slide(enemy, old_enemy_pos)

            # Cleanup dead enemies once death animation finishes
            if not enemy.is_alive and enemy.is_animation_finished():
                if enemy in self.enemies:
                    self.enemies.remove(enemy)
                if enemy in self.all_sprites:
                    self.all_sprites.remove(enemy)

        # Update spells
        for spell in list(self.spells):
            spell.update(dt)

            # Remove dead or out-of-bounds spells
            if (not spell.is_alive) or (not self._is_in_world_bounds(spell.pos)):
                if spell in self.spells:
                    self.spells.remove(spell)
                if spell in self.all_sprites:
                    self.all_sprites.remove(spell)

        # Update undines (and their spells)
        self.undine_manager.update(dt, self.player)

        # Combat checks
        self._check_spell_combat()
        self._check_spell_undine_combat()
        self._check_undine_spell_player_combat()

        # Intermission / wave progression
        if self._in_intermission:
            self._intermission_timer -= dt
            if self._intermission_timer <= 0:
                self._begin_wave(self.next_wave_number)
        else:
            if self._is_wave_cleared():
                self._start_intermission(self.current_wave_number + 1)

        # Check for player death
        if not self.player.is_alive and self.player.is_animation_finished():
            if not self.show_death_dialog:
                self.show_death_dialog = True
                self.death_panel.show_death()
                sound_manager.play_game_over()

    # ── Collision / Combat helpers (mostly copied from WorldScene) ─────

    def _sync_rect(self, entity):
        if getattr(entity, 'rect', None) is not None:
            entity.rect.center = (int(entity.pos.x), int(entity.pos.y))

    def _resolve_collision_with_slide(self, entity, old_pos: pygame.Vector2):
        """If entity is in collision, try sliding along X or Y before reverting."""
        if not self._check_tile_collision(entity):
            return

        new_pos = pygame.Vector2(entity.pos)

        # Try reverting Y only
        entity.pos.y = old_pos.y
        if not self._check_tile_collision(entity):
            self._sync_rect(entity)
            return

        # Try reverting X only
        entity.pos.y = new_pos.y
        entity.pos.x = old_pos.x
        if not self._check_tile_collision(entity):
            self._sync_rect(entity)
            return

        # Full revert
        entity.pos.x = old_pos.x
        entity.pos.y = old_pos.y
        self._sync_rect(entity)

    def _check_tile_collision(self, entity) -> bool:
        """Check if an entity collides with collision tiles or decoration objects."""
        tile_x = entity.pos.x / SCALE
        tile_y = entity.pos.y / SCALE

        check_radius = 8
        for dx in [-check_radius, 0, check_radius]:
            for dy in [-check_radius, 0, check_radius]:
                if self.tilemap.is_position_blocked(tile_x + dx, tile_y + dy):
                    return True

        entity_rect = pygame.Rect(
            entity.pos.x - 8 * SCALE,
            entity.pos.y - 4 * SCALE,
            16 * SCALE,
            8 * SCALE
        )
        for collision_rect in self.decoration_collision_rects:
            if entity_rect.colliderect(collision_rect):
                return True

        return False

    def _is_in_world_bounds(self, pos: pygame.Vector2) -> bool:
        margin = 50
        return (
            -margin < pos.x < self.world_pixel_width + margin and
            -margin < pos.y < self.world_pixel_height + margin
        )

    def _check_spell_combat(self):
        for spell in list(self.spells):
            if not spell.is_alive:
                continue

            spell_hitbox = spell.get_hitbox()

            for enemy in self.enemies:
                if enemy.is_alive:
                    enemy_hitbox = enemy.get_hitbox()
                    if spell_hitbox.colliderect(enemy_hitbox):
                        if not spell.can_hit_target(enemy.letter):
                            continue

                        enemy.take_damage(spell.damage)
                        spell.destroy()
                        sound_manager.play_spell_impact()

                        if spell in self.spells:
                            self.spells.remove(spell)
                        if spell in self.all_sprites:
                            self.all_sprites.remove(spell)
                        break

    def _check_spell_undine_combat(self):
        for spell in list(self.spells):
            if not spell.is_alive:
                continue

            spell_hitbox = spell.get_hitbox()

            for undine in self.undine_manager.undines:
                if undine.alive and spell_hitbox.colliderect(undine.rect):
                    if not spell.can_hit_target(undine.letter):
                        continue

                    undine.take_damage(spell.damage)
                    spell.destroy()
                    sound_manager.play_spell_impact()

                    if spell in self.spells:
                        self.spells.remove(spell)
                    if spell in self.all_sprites:
                        self.all_sprites.remove(spell)
                    break

    def _check_undine_spell_player_combat(self):
        for spell in list(self.undine_manager.spells):
            if not spell.is_alive:
                continue

            spell_hitbox = spell.get_hitbox()
            player_hitbox = self.player.get_hitbox()

            if spell_hitbox.colliderect(player_hitbox):
                if self.player.is_blocking:
                    spell.destroy()
                    if spell in self.undine_manager.spells:
                        self.undine_manager.spells.remove(spell)
                else:
                    self.player.take_damage(spell.damage)
                    spell.destroy()
                    if spell in self.undine_manager.spells:
                        self.undine_manager.spells.remove(spell)
                break

    # ── Camera input ───────────────────────────────────────────────────

    def _process_camera_input(self, dt: float):
        if self._no_target_timer > 0:
            self._no_target_timer -= dt
            if self._no_target_timer <= 0:
                self._no_target_letter = None

        if self.camera_input is None or not self.camera_input.is_available():
            return

        pending_letters = self.camera_input.get_pending_letters()
        for letter in pending_letters:
            self._handle_camera_letter(letter)

    def _handle_camera_letter(self, letter: str):
        if not self.player.is_alive:
            return

        letter = letter.upper()

        # Enforce wave unlocks
        if letter not in self.unlocked_letters:
            return

        # B is always block in Survival
        if letter == 'B':
            self.player.start_block()
            return

        target = find_closest_enemy_by_letter(self.enemies, letter, self.player.pos)
        target_undine = self._find_closest_undine_by_letter(letter)

        if target and target_undine:
            dist_enemy = self.player.pos.distance_to(target.pos)
            dist_undine = self.player.pos.distance_to(target_undine.pos)
            if dist_undine < dist_enemy:
                target = None
            else:
                target_undine = None

        if target:
            spell_type = self._next_spell_type()
            spell = SpellProjectile.create_targeted(
                self.player.pos,
                target.pos,
                spell_type,
                letter
            )
            self.spells.add(spell)
            self.all_sprites.add(spell)
            self.player.play_cast_toward(target.pos)
            sound_manager.play_spell_sound(spell_type)
        elif target_undine:
            spell_type = self._next_spell_type()
            spell = SpellProjectile.create_targeted(
                self.player.pos,
                target_undine.pos,
                spell_type,
                letter
            )
            self.spells.add(spell)
            self.all_sprites.add(spell)
            self.player.play_cast_toward(target_undine.pos)
            sound_manager.play_spell_sound(spell_type)
        else:
            self._no_target_timer = 1.5
            self._no_target_letter = letter

    def _next_spell_type(self) -> str:
        spell_type = SPELL_TYPES[self._spell_type_index]
        self._spell_type_index = (self._spell_type_index + 1) % len(SPELL_TYPES)
        return spell_type

    def _find_closest_undine_by_letter(self, letter: str):
        letter = letter.upper()
        matching = [u for u in self.undine_manager.undines if u.alive and u.letter == letter]
        if not matching:
            return None

        closest = None
        closest_dist = float('inf')
        for undine in matching:
            dist = self.player.pos.distance_to(undine.pos)
            if dist < closest_dist:
                closest_dist = dist
                closest = undine
        return closest

    # ── Rendering helpers ──────────────────────────────────────────────

    def _render_scaled_background(self):
        base_surface = self.tilemap.render_base_layers()
        scaled_width = base_surface.get_width() * SCALE
        scaled_height = base_surface.get_height() * SCALE
        self.background = pygame.transform.scale(base_surface, (scaled_width, scaled_height))

    def _prepare_decorations(self):
        self.decorations = []
        self.decoration_collision_rects = []

        raw_decorations = self.tilemap.get_decoration_tiles()
        for surface, pixel_x, pixel_y, sort_y in raw_decorations:
            scaled_surface = pygame.transform.scale(
                surface,
                (surface.get_width() * SCALE, surface.get_height() * SCALE)
            )
            world_x = pixel_x * SCALE
            world_y = pixel_y * SCALE
            world_sort_y = sort_y * SCALE
            self.decorations.append((scaled_surface, world_x, world_y, world_sort_y))

        raw_collision_rects = self.tilemap.get_decoration_collision_rects()
        for rect in raw_collision_rects:
            scaled_rect = pygame.Rect(
                rect.x * SCALE,
                rect.y * SCALE,
                rect.width * SCALE,
                rect.height * SCALE
            )
            self.decoration_collision_rects.append(scaled_rect)

    def _draw_entity_health_bars(self, screen: pygame.Surface):
        # Player health bar
        player_screen_x, player_screen_y = self.camera.world_to_screen(
            self.player.pos.x, self.player.pos.y - 35
        )
        self._draw_health_bar(screen, player_screen_x, player_screen_y,
                              self.player.health, self.player.max_health)

        # Enemies
        for enemy in self.enemies:
            if enemy.is_alive:
                enemy_screen_x, enemy_screen_y = self.camera.world_to_screen(
                    enemy.pos.x, enemy.pos.y - 25
                )
                self._draw_health_bar(screen, enemy_screen_x, enemy_screen_y,
                                      enemy.health, enemy.max_health, width=30, height=4)

            enemy_center_x, enemy_center_y = self.camera.world_to_screen(
                enemy.pos.x, enemy.pos.y
            )
            enemy.draw_letter(screen, enemy_center_x, enemy_center_y)

        # Undines
        for undine in self.undine_manager.undines:
            if undine.alive and undine.health < undine.max_health:
                undine_screen_x, undine_screen_y = self.camera.world_to_screen(
                    undine.pos.x, undine.pos.y - 40
                )
                self._draw_health_bar(screen, undine_screen_x, undine_screen_y,
                                      undine.health, undine.max_health, width=40, height=4)
            if undine.alive:
                undine_center_x, undine_center_y = self.camera.world_to_screen(
                    undine.pos.x, undine.pos.y
                )
                undine.draw_letter(screen, undine_center_x, undine_center_y)

    def _draw_health_bar(self, surface, x, y, health, max_health, width=50, height=5):
        health_ratio = max(0, health / max_health)
        pygame.draw.rect(surface, (80, 20, 20), (x - width/2, y, width, height))
        pygame.draw.rect(surface, (50, 180, 50), (x - width/2, y, width * health_ratio, height))
        pygame.draw.rect(surface, (40, 40, 40), (x - width/2, y, width, height), 1)

    def _draw_debug_hitboxes(self, screen: pygame.Surface):
        # Player hitbox
        player_hitbox = self.player.get_hitbox()
        screen_x, screen_y = self.camera.world_to_screen(player_hitbox.x, player_hitbox.y)
        pygame.draw.rect(screen, (0, 255, 0),
                         (screen_x, screen_y, player_hitbox.width, player_hitbox.height), 2)

        # Enemy hitboxes
        for enemy in self.enemies:
            if enemy.is_alive:
                hitbox = enemy.get_hitbox()
                screen_x, screen_y = self.camera.world_to_screen(hitbox.x, hitbox.y)
                pygame.draw.rect(screen, (255, 0, 0),
                                 (screen_x, screen_y, hitbox.width, hitbox.height), 2)

        # Undine hitboxes
        for undine in self.undine_manager.undines:
            if undine.alive:
                screen_x, screen_y = self.camera.world_to_screen(undine.rect.x, undine.rect.y)
                pygame.draw.rect(screen, (255, 0, 255),
                                 (screen_x, screen_y, undine.rect.width, undine.rect.height), 2)

        # Undine spell hitboxes
        for spell in self.undine_manager.spells:
            if spell.is_alive:
                spell_hitbox = spell.get_hitbox()
                screen_x, screen_y = self.camera.world_to_screen(spell_hitbox.x, spell_hitbox.y)
                pygame.draw.rect(screen, (0, 255, 255),
                                 (screen_x, screen_y, spell_hitbox.width, spell_hitbox.height), 2)

        # Player spell hitboxes
        for spell in self.spells:
            if spell.is_alive:
                spell_hitbox = spell.get_hitbox()
                screen_x, screen_y = self.camera.world_to_screen(spell_hitbox.x, spell_hitbox.y)
                pygame.draw.rect(screen, (0, 100, 255),
                                 (screen_x, screen_y, spell_hitbox.width, spell_hitbox.height), 2)

    def _draw_camera_preview(self, screen: pygame.Surface):
        frame_surface = self.camera_input.get_preview_surface() if self.camera_input else None
        if frame_surface is None:
            return

        preview = pygame.transform.scale(frame_surface, (CAMERA_PREVIEW_WIDTH, CAMERA_PREVIEW_HEIGHT))

        mx, my = CAMERA_PREVIEW_MARGIN_X, CAMERA_PREVIEW_MARGIN_Y
        pw, ph = CAMERA_PREVIEW_WIDTH, CAMERA_PREVIEW_HEIGHT

        corner = CAMERA_PREVIEW_CORNER
        if corner == 'top_left':
            x, y = mx, my
        elif corner == 'top_right':
            x, y = SCREEN_WIDTH - pw - mx, my
        elif corner == 'bottom_left':
            x, y = mx, SCREEN_HEIGHT - ph - my
        else:
            x, y = SCREEN_WIDTH - pw - mx, SCREEN_HEIGHT - ph - my

        border = 2
        pygame.draw.rect(screen, (30, 30, 30), (x - border, y - border, pw + border * 2, ph + border * 2))
        screen.blit(preview, (x, y))

    def _draw_camera_startup_overlay(self, screen: pygame.Surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title = self._camera_ready_font.render("Starting camera...", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)))

        msg = "Press Enter to continue"
        if self.camera_input is not None:
            err = self.camera_input.get_error_message()
            if err:
                msg = f"Camera unavailable: {err} (Press Enter)"

        hint = self.font.render(msg, True, (220, 220, 220))
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)))

    # ── Draw ───────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        screen.fill((20, 30, 20))

        # Background
        self.camera.apply_to_surface(self.background, screen)

        # Combined y-sort list
        y_sort_items: list[tuple[float, str, object]] = []

        for sprite in self.all_sprites:
            y_sort_items.append((sprite.pos.y, 'sprite', sprite))

        for undine in self.undine_manager.undines:
            if undine.alive:
                y_sort_items.append((undine.pos.y, 'undine', undine))

        for spell in self.undine_manager.spells:
            if spell.is_alive:
                y_sort_items.append((spell.pos.y, 'spell', spell))

        for surface, world_x, world_y, sort_y in self.decorations:
            y_sort_items.append((sort_y, 'decor', (surface, world_x, world_y)))

        y_sort_items.sort(key=lambda item: item[0])

        for _, item_type, data in y_sort_items:
            if item_type == 'sprite':
                sprite = data
                screen_x, screen_y = self.camera.world_to_screen(sprite.rect.x, sprite.rect.y)
                screen.blit(sprite.image, (screen_x, screen_y))
            elif item_type == 'undine':
                undine = data
                screen_x, screen_y = self.camera.world_to_screen(undine.rect.x, undine.rect.y)
                screen.blit(undine.image, (screen_x, screen_y))
            elif item_type == 'spell':
                spell = data
                screen_x, screen_y = self.camera.world_to_screen(spell.rect.x, spell.rect.y)
                screen.blit(spell.image, (screen_x, screen_y))
            else:
                surface, world_x, world_y = data
                screen_x, screen_y = self.camera.world_to_screen(world_x, world_y)
                screen.blit(surface, (screen_x, screen_y))

        # Health bars + letters
        self._draw_entity_health_bars(screen)

        if DEBUG_SHOW_HITBOXES:
            self._draw_debug_hitboxes(screen)

        # HUD
        self.hud.draw(screen, self.player, game_state)

        # Wave UI
        display_wave = self.next_wave_number if self._in_intermission else self.current_wave_number
        display_wave = max(1, int(display_wave))
        if self._in_intermission:
            self.wave_display.draw(
                screen,
                display_wave,
                True,
                max(0.0, self._intermission_timer),
                message_line1="Next Wave",
                message_line2="",
            )
        else:
            self.wave_display.draw(screen, display_wave)

        # Controls
        controls = self.font.render("WASD: Move | ESC: Menu", True, (180, 180, 180))
        screen.blit(controls, (10, SCREEN_HEIGHT - 25))

        # Enemy count
        enemy_count = len([e for e in self.enemies if e.is_alive])
        undine_count = len([u for u in self.undine_manager.undines if u.alive])
        total_count = enemy_count + undine_count
        count_text = self.font.render(f"Enemies: {total_count}", True, (200, 200, 200))
        screen.blit(count_text, (SCREEN_WIDTH - 140, SCREEN_HEIGHT - 25))

        # Camera letter display
        if self.camera_input is not None and not self._waiting_for_camera_ready:
            detected_letter, hold_progress = self.camera_input.get_current_detection()
            state = self.camera_input.get_state()
            self.camera_letter_display.draw(
                screen,
                detected_letter,
                hold_progress,
                state,
                self._no_target_letter,
                self._no_target_timer > 0,
            )

        # Camera preview
        if CAMERA_SHOW_PREVIEW and self.camera_input is not None and not self._waiting_for_camera_ready:
            self._draw_camera_preview(screen)

        if self._waiting_for_camera_ready:
            self._draw_camera_startup_overlay(screen)

        # Panels
        self.death_panel.draw(screen)

        # Wave preview panel (during intermission)
        self.sign_panel.draw(screen)
