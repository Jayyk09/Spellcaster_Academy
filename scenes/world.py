"""World scene - main gameplay area with tilemap and camera."""
from entities.lich import Lich, LichLightning
import pygame
import os
import json
import random
from core.scene import Scene
from core.game_state import game_state
from core.ui import HUD, DeathPanel, HealthBar, CameraLetterDisplay, WaveDisplay, ASLPopup, SignReferencePanel
from core.camera import Camera
from core.map_loader import load_map_data, create_tilemap_from_data, get_spawn_points
from entities.player import Player
from entities.enemy import Slime, Skeleton, find_closest_enemy_by_letter
from entities.undine import UndineManager
from entities.spell import SpellProjectile
from entities.npc import MageGuardian
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SPRITES_DIR,
    TILE_SIZE, SCALE, WORLD_WIDTH, WORLD_HEIGHT,
    WORLD_WIDTH_TILES, WORLD_HEIGHT_TILES, CAMERA_DRAG_MARGIN,
    SPELL_DAMAGE, CAMERA_ENABLED, CAMERA_DEFAULT_SPELL,
    SPELL_TYPES
)


class WorldScene(Scene):
    """Main world gameplay scene with tilemap rendering and camera."""
    
    def __init__(self, game, **kwargs):
        super().__init__(game)
        
        # Load map data
        self.map_data = load_map_data('world_map')
        if self.map_data is None:
            raise RuntimeError("Failed to load world map data")
        
        # Create tilemap
        self.tilemap = create_tilemap_from_data(self.map_data)
        
        # Calculate world dimensions in pixels (at scale)
        self.world_pixel_width = WORLD_WIDTH_TILES * TILE_SIZE * SCALE
        self.world_pixel_height = WORLD_HEIGHT_TILES * TILE_SIZE * SCALE
        
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
        
        # Get spawn points from map data
        spawn_points = get_spawn_points(self.map_data)
        
        # Create player at spawn point
        player_spawn = spawn_points.get('player_start', {'x': 3, 'y': 6})
        start_x = player_spawn['x'] * TILE_SIZE * SCALE + (TILE_SIZE * SCALE // 2)
        start_y = player_spawn['y'] * TILE_SIZE * SCALE + (TILE_SIZE * SCALE // 2)
        self.player = Player(start_x, start_y)
        
        # Set camera to follow player with velocity for directional offset
        self.camera.set_target(self.player.pos, self.player.velocity)
        self.camera.center_on(self.player.pos.x, self.player.pos.y)
        
        # Initialize enemy groups (populated by wave system)
        self.enemies = pygame.sprite.Group()
        
        # Mushrooms disabled - sprite removed
        self.mushrooms = []
        
        # Create Undine manager (populated by wave system)
        self.undine_manager = UndineManager(self.world_pixel_width, self.world_pixel_height)
        
        # All sprites for rendering
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        
        # Wave system
        self.wave_config = self._load_wave_config()
        self.current_wave_index = 0
        self.wave_display = WaveDisplay()

        # Region-based wave system
        self.regions = self._build_regions()
        self.barriers = self._build_barriers()
        self.active_region_index = 0
        self.region_cleared = [False] * len(self.regions)
        self.wave_cleared_timer = 0.0  # Timer for "Wave Cleared!" notification
        self.wave_cleared_duration = 3.0  # Show notification for 3 seconds

        # Track which enemies belong to which region (for clamping)
        self.enemy_region_map = {}  # enemy id -> region_index
        
        # Spell projectiles
        self.spells = pygame.sprite.Group()
        
        # UI
        self.hud = HUD()
        self.death_panel = DeathPanel()
        self.show_death_dialog = False
        
        # ASL Popup for learning new letters
        self.asl_popup = ASLPopup()
        self._showing_asl_popup = False
        self._letters_learned = set()  # Track which letters have been shown
        self._pending_letters = []  # Letters to show in next popup
        
        # Show ASL popup for first wave letters before spawning
        first_wave_data = self._get_wave_data(0)
        first_letters = first_wave_data.get('letters', ['A'])
        self._show_asl_popup_for_letters(first_letters)
        
        # Camera input (ASL detection) - get from game (shared across scenes)
        self.camera_input = None
        self.camera_letter_display = CameraLetterDisplay()
        self._no_target_timer = 0.0  # Timer for "No Target" feedback
        self._no_target_letter = None  # Letter that had no target
        self._camera_initialized = False  # Delay camera init until after ASL popup
        
        # Font for extra UI
        self.font = pygame.font.Font(None, 24)
        
        # Camera startup pause - will be set after ASL popup closes
        self._waiting_for_camera_ready = False
        self._camera_ready_font = pygame.font.Font(None, 36)
        
        # Spell type cycling - rotate through spell types each cast
        self._spell_type_index = 0
        
        # NPC - Mage Guardian
        npc_spawn = spawn_points.get('npc_start', {'x': 35, 'y': 25})
        npc_x = npc_spawn['x'] * TILE_SIZE * SCALE + (TILE_SIZE * SCALE // 2)
        npc_y = npc_spawn['y'] * TILE_SIZE * SCALE + (TILE_SIZE * SCALE // 2)
        self.npc = MageGuardian(npc_x, npc_y)
        self.all_sprites.add(self.npc)
        
        # Sign reference panel (shown when near NPC)
        self.sign_panel = SignReferencePanel()
    
    def _render_scaled_background(self):
        """Pre-render and scale the tilemap background."""
        # Render base layers at native resolution
        base_surface = self.tilemap.render_base_layers()
        
        # Scale up by SCALE factor
        scaled_width = base_surface.get_width() * SCALE
        scaled_height = base_surface.get_height() * SCALE
        self.background = pygame.transform.scale(base_surface, (scaled_width, scaled_height))
    
    def _prepare_decorations(self):
        """
        Pre-render and scale ysort decoration objects.
        
        Stores list of (scaled_surface, world_x, world_y, sort_y) tuples.
        All coordinates are in world space (scaled pixels).
        Also pre-computes scaled collision rects for blocking objects.
        """
        self.decorations = []
        self.decoration_collision_rects = []
        
        # Get decoration tiles from tilemap (native resolution)
        raw_decorations = self.tilemap.get_decoration_tiles()
        
        for surface, pixel_x, pixel_y, sort_y in raw_decorations:
            # Scale the surface
            scaled_width = surface.get_width() * SCALE
            scaled_height = surface.get_height() * SCALE
            scaled_surface = pygame.transform.scale(surface, (scaled_width, scaled_height))
            
            # Scale world positions
            world_x = pixel_x * SCALE
            world_y = pixel_y * SCALE
            world_sort_y = sort_y * SCALE
            
            self.decorations.append((scaled_surface, world_x, world_y, world_sort_y))
        
        # Get collision rects for decoration objects and scale them
        raw_collision_rects = self.tilemap.get_decoration_collision_rects()
        for rect in raw_collision_rects:
            scaled_rect = pygame.Rect(
                rect.x * SCALE,
                rect.y * SCALE,
                rect.width * SCALE,
                rect.height * SCALE
            )
            self.decoration_collision_rects.append(scaled_rect)
    
    def _load_wave_config(self) -> dict:
        """Load wave configuration from JSON file."""
        try:
            waves_path = os.path.join('data', 'waves.json')
            with open(waves_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading waves.json: {e}")
            # Return default config
            return {
                'waves': [
                    {
                        'wave_number': 1,
                        'letters': ['A', 'C', 'D', 'E'],
                        'enemies': {'slime': 2, 'skeleton': 1, 'undine': 1}
                    }
                ],
                'time_between_waves_seconds': 5
            }
    
    def _build_regions(self) -> list[dict]:
        """Build region definitions from wave config, converting tile coords to pixels."""
        regions = []
        waves = self.wave_config.get('waves', [])
        tile_px = TILE_SIZE * SCALE
        for wave in waves:
            region = wave.get('region', {})
            regions.append({
                'min_y': region.get('min_y', 0) * tile_px,
                'max_y': region.get('max_y', WORLD_HEIGHT_TILES) * tile_px,
                'min_x': region.get('min_x', 0) * tile_px,
                'max_x': region.get('max_x', WORLD_WIDTH_TILES) * tile_px,
            })
        return regions

    def _build_barriers(self) -> list[dict]:
        """Build barrier objects from wave config."""
        barriers = []
        tile_px = TILE_SIZE * SCALE
        barrier_defs = self.wave_config.get('barriers', [])
        for i, bdef in enumerate(barrier_defs):
            barriers.append({
                'y': bdef['y'] * tile_px,
                'min_x': bdef['min_x'] * tile_px,
                'max_x': (bdef['max_x'] + 1) * tile_px,  # +1 to include the tile
                'active': True,
                'wave_index': i,  # Barrier i is removed when wave i is cleared
            })
        return barriers

    def _get_wave_data(self, wave_index: int) -> dict:
        """
        Get wave data for a specific index.
        
        If index exceeds available waves, returns the last wave.
        """
        waves = self.wave_config.get('waves', [])
        if not waves:
            return {'letters': ['A'], 'enemies': {'slime': 1, 'skeleton': 0, 'undine': 0}}
        
        # Clamp index to last wave if beyond available waves
        actual_index = min(wave_index, len(waves) - 1)
        return waves[actual_index]
    
    def _get_random_spawn_position(self, min_distance_from_player: float = 150, region_index: int | None = None) -> tuple[float, float]:
        """
        Get a random valid spawn position within a region.

        Args:
            min_distance_from_player: Minimum distance from player position
            region_index: Region to constrain spawn to (uses self.active_region_index if None)

        Returns:
            (x, y) tuple of world coordinates
        """
        if region_index is None:
            region_index = self.active_region_index

        region = self.regions[region_index] if region_index < len(self.regions) else None
        margin = 80  # Stay away from world edges
        max_attempts = 50

        if region:
            min_x = max(margin, region['min_x'] + margin)
            max_x = min(self.world_pixel_width - margin, region['max_x'] - margin)
            min_y = max(margin, region['min_y'] + margin)
            max_y = min(self.world_pixel_height - margin, region['max_y'] - margin)
        else:
            min_x = margin
            max_x = self.world_pixel_width - margin
            min_y = margin
            max_y = self.world_pixel_height - margin

        for _ in range(max_attempts):
            x = random.randint(int(min_x), int(max_x))
            y = random.randint(int(min_y), int(max_y))

            # Check distance from player
            player_dist = ((x - self.player.pos.x) ** 2 + (y - self.player.pos.y) ** 2) ** 0.5
            if player_dist < min_distance_from_player:
                continue

            # Create a temporary test entity to check collision
            class TempEntity:
                def __init__(self, px, py):
                    self.pos = pygame.Vector2(px, py)

            temp = TempEntity(x, y)
            if not self._check_tile_collision(temp):
                return (x, y)

        # Fallback: return center of region
        x = (min_x + max_x) // 2
        y = (min_y + max_y) // 2
        return (x, y)
    
    def _show_asl_popup_for_letters(self, letters: list[str], subtitle: str = ""):
        """Show ASL popup for new letters that haven't been learned yet."""
        # Filter to only letters A-F that are in our sprites
        valid_letters = [l.upper() for l in letters if l.upper() in ['A', 'B', 'C', 'D', 'E', 'F']]
        
        # Find letters that haven't been shown yet
        new_letters = [l for l in valid_letters if l not in self._letters_learned]
        
        if new_letters:
            # Add new letters to learned set
            self._letters_learned.update(new_letters)
            # Show popup with only the NEW letters
            self.asl_popup.show(new_letters, subtitle)
            self._showing_asl_popup = True
            return True
        
        return False

    def _spawn_wave(self, wave_index: int):
        """
        Spawn enemies for a specific wave.

        Args:
            wave_index: 0-based wave index
        """
        wave_data = self._get_wave_data(wave_index)
        letters = wave_data.get('letters', ['A', 'B', 'C', 'D', 'E'])
        enemies_config = wave_data.get('enemies', {})

        # Spawn slimes
        slime_count = enemies_config.get('slime', 0)
        for _ in range(slime_count):
            x, y = self._get_random_spawn_position(region_index=wave_index)
            letter = random.choice(letters)
            enemy = Slime(x, y, letter=letter)
            enemy.set_target(self.player)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)
            self.enemy_region_map[id(enemy)] = wave_index

        # Spawn skeletons
        skeleton_count = enemies_config.get('skeleton', 0)
        for _ in range(skeleton_count):
            x, y = self._get_random_spawn_position(region_index=wave_index)
            letter = random.choice(letters)
            enemy = Skeleton(x, y, letter=letter)
            enemy.set_target(self.player)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)
            self.enemy_region_map[id(enemy)] = wave_index

        # Spawn undines within region
        undine_count = enemies_config.get('undine', 0)
        if undine_count > 0 and wave_index < len(self.regions):
            region = self.regions[wave_index]
            center_x = (region['min_x'] + region['max_x']) / 2
            center_y = (region['min_y'] + region['max_y']) / 2
            undines = self.undine_manager.spawn_near(
                undine_count,
                center_x=center_x,
                center_y=center_y,
                radius=100,
                letters=letters
            )
            # Track undine regions (if undine_manager supports returning spawned undines)
            for undine in undines if undines else []:
                if hasattr(undine, '_region_index'):
                    undine._region_index = wave_index

        lich_count = enemies_config.get('lich', 0)
        for _ in range(lich_count):
            x, y = self._get_random_spawn_position(region_index=wave_index)
            letter = random.choice(letters)
            enemy = Lich(x, y, letter=letter)
            enemy.set_target(self.player)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)
            self.enemy_region_map[id(enemy)] = wave_index
    
    def _check_wave_completion(self) -> bool:
        """Check if all enemies in the current wave are defeated."""
        alive_enemies = len([e for e in self.enemies if e.is_alive])
        alive_undines = self.undine_manager.get_alive_count()
        return alive_enemies == 0 and alive_undines == 0
    
    def _start_next_wave(self):
        """Start the next wave after transition period."""
        self.current_wave_index += 1
        
        # Check if there are new letters to learn
        wave_data = self._get_wave_data(self.current_wave_index)
        
        # Before wave 2, prepend B (block) so it shows as B, C in the popup
        if self.current_wave_index == 1:
            letters = ['B'] + wave_data.get('letters', [])
            showing_popup = self._show_asl_popup_for_letters(
                letters, "Sign B to Block!"
            )
        else:
            letters = wave_data.get('letters', [])
            showing_popup = self._show_asl_popup_for_letters(letters)
        
        # Only spawn if popup is not showing (otherwise wait for ready)
        if not showing_popup:
            self._spawn_wave(self.current_wave_index)
    
    def _get_current_wave_number(self) -> int:
        """Get the current wave number (1-indexed for display)."""
        return self.current_wave_index + 1
    
    def handle_event(self, event):
        # Handle ASL popup events first
        if self._showing_asl_popup:
            self.asl_popup.handle_event(event)
            return
        
        if event.type == pygame.KEYDOWN:
            # Handle camera startup pause
            if self._waiting_for_camera_ready:
                if event.key == pygame.K_RETURN:
                    self._waiting_for_camera_ready = False
                return
            
            # Handle death dialog input
            if self.show_death_dialog:
                if event.key == pygame.K_y and game_state.game_has_savegame:
                    # Load save and restart world
                    game_state.load_game()
                    self.next_scene = 'world'
                elif event.key == pygame.K_n:
                    # Quit to menu
                    self.next_scene = 'menu'
                return
            
            
            if event.key == pygame.K_ESCAPE:
                self.next_scene = 'menu'
            
            # Debug: respawn
            if event.key == pygame.K_r and self.map_data:
                spawn_points = get_spawn_points(self.map_data)
                player_spawn = spawn_points.get('player_start', {'x': 3, 'y': 6})
                start_x = player_spawn['x'] * TILE_SIZE * SCALE + (TILE_SIZE * SCALE // 2)
                start_y = player_spawn['y'] * TILE_SIZE * SCALE + (TILE_SIZE * SCALE // 2)
                self.player.respawn(start_x, start_y)
                self.show_death_dialog = False
                self.death_panel.hide()
    
    def _initialize_camera(self):
        """Initialize camera input after ASL popup is closed."""
        if self._camera_initialized or not CAMERA_ENABLED:
            return
        
        self._camera_initialized = True
        self.camera_input = self.game.get_camera_input()
        
        # Check if we need to wait for camera to be ready
        camera_already_running = (
            self.camera_input is not None and 
            self.camera_input.is_available()
        )
        self._waiting_for_camera_ready = CAMERA_ENABLED and not camera_already_running
    
    def update(self, dt: float):
        # Don't update game while waiting for camera ready or ASL popup
        if self._waiting_for_camera_ready:
            return
        
        # Check if ASL popup is showing - don't update game while learning
        if self._showing_asl_popup:
            if self.asl_popup.is_ready():
                self._showing_asl_popup = False
                # Now spawn the wave that was waiting
                self._spawn_wave(self.current_wave_index)
                # Initialize camera after popup closes
                self._initialize_camera()
            return
        
        # Get input
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        # Process camera input (ASL letter detection)
        self._process_camera_input(dt)
        
        # Store old position for collision resolution
        old_pos = pygame.Vector2(self.player.pos)
        
        # Update player
        self.player.update(dt)
        
        # Clamp player to world bounds (accounting for sprite size)
        margin = 24 * SCALE // 3  # Adjust margin based on sprite
        self.player.pos.x = max(margin, min(self.world_pixel_width - margin, self.player.pos.x))
        self.player.pos.y = max(margin, min(self.world_pixel_height - margin, self.player.pos.y))
        
        # Check tile collision
        if self._check_tile_collision(self.player):
            # Revert to old position if blocked
            self.player.pos.x = old_pos.x
            self.player.pos.y = old_pos.y
        
        # Update camera to follow player
        self.camera.update(dt)
        
        # Update enemies
        for enemy in self.enemies:
            old_enemy_pos = pygame.Vector2(enemy.pos)
            enemy.update(dt)

            # Clamp enemy to world bounds
            enemy_margin = 16 * SCALE // 3
            enemy.pos.x = max(enemy_margin, min(self.world_pixel_width - enemy_margin, enemy.pos.x))
            enemy.pos.y = max(enemy_margin, min(self.world_pixel_height - enemy_margin, enemy.pos.y))

            # Clamp enemy to their spawn region
            enemy_id = id(enemy)
            if enemy_id in self.enemy_region_map:
                region_idx = self.enemy_region_map[enemy_id]
                if region_idx < len(self.regions):
                    region = self.regions[region_idx]
                    enemy.pos.x = max(region['min_x'] + enemy_margin,
                                      min(region['max_x'] - enemy_margin, enemy.pos.x))
                    enemy.pos.y = max(region['min_y'] + enemy_margin,
                                      min(region['max_y'] - enemy_margin, enemy.pos.y))

            # Check tile collision for enemies
            if self._check_tile_collision(enemy):
                enemy.pos.x = old_enemy_pos.x
                enemy.pos.y = old_enemy_pos.y
        
        # Update spells
        for spell in list(self.spells):
            spell.update(dt)
            
            # Remove spells that are out of bounds or expired
            if not spell.is_alive:
                self.spells.remove(spell)
                self.all_sprites.remove(spell)
            elif not self._is_in_world_bounds(spell.pos):
                spell.destroy()
                self.spells.remove(spell)
                self.all_sprites.remove(spell)
        
        # Check spell-enemy combat
        self._check_spell_combat()
        
        # Update undines
        self.undine_manager.update(dt, self.player)

        # Apply barrier collision to undines (keep them in their region)
        if self.active_region_index < len(self.barriers):
            barrier = self.barriers[self.active_region_index]
            if barrier['active']:
                for undine in self.undine_manager.undines:
                    if undine.alive and undine.pos.y < barrier['y']:
                        # Undine tried to cross barrier - push it back
                        undine.pos.y = barrier['y']
                        undine.direction.y = abs(undine.direction.y)  # Bounce downward

        # Check spell-undine combat
        self._check_spell_undine_combat()
        
        # Check undine spell collisions with player
        self._check_undine_spell_player_combat()
        
        # Lich integration: pick up summoned skeletons and update lightning bolts
        for enemy in self.enemies:
            if isinstance(enemy, Lich):
                # Add any pending summoned skeletons to the world
                for skel in enemy.pending_skeletons:
                    self.enemies.add(skel)
                    self.all_sprites.add(skel)
                enemy.pending_skeletons.clear()
                # Update lightning bolts
                for bolt in list(enemy.lightning_bolts):
                    bolt.update(dt)
                    if not bolt.is_alive:
                        enemy.lightning_bolts.remove(bolt)
        
        # Check lich lightning collisions with player
        self._check_lich_lightning_player_combat()
        
        # Update NPC and sign reference panel
        self.npc.update(dt, self.player)
        if self.npc.is_player_nearby():
            # Build list of all active letters (learned so far + B for block if wave >= 2)
            active_letters = sorted(self._letters_learned)
            labels = {}
            if self.current_wave_index >= 1 and 'B' not in active_letters:
                active_letters = sorted(active_letters | {'B'})
            if 'B' in active_letters:
                labels['B'] = 'Block'
            self.sign_panel.set_letters(active_letters, labels)
            self.sign_panel.show()
        else:
            self.sign_panel.hide()
        
        # Mushrooms disabled - sprite removed
        
        # Clean up dead enemies
        for enemy in list(self.enemies):
            if not enemy.is_alive and enemy.is_animation_finished():
                self.enemies.remove(enemy)
                self.all_sprites.remove(enemy)
        
        # Wave system: check for wave completion and handle barrier removal
        if not self.region_cleared[self.active_region_index]:
            if self._check_wave_completion():
                # Mark region as cleared
                self.region_cleared[self.active_region_index] = True
                self.wave_cleared_timer = self.wave_cleared_duration
                # Deactivate barrier for this region (if any)
                if self.active_region_index < len(self.barriers):
                    self.barriers[self.active_region_index]['active'] = False
        else:
            # Decrement wave cleared notification timer
            if self.wave_cleared_timer > 0:
                self.wave_cleared_timer -= dt

        # Check barrier collision for player (only the current active barrier)
        if self.active_region_index < len(self.barriers):
            barrier = self.barriers[self.active_region_index]
            if barrier['active']:
                # Check if player is crossing the barrier (moving upward through it)
                player_y = self.player.pos.y
                barrier_y = barrier['y']
                player_x = self.player.pos.x
                # Block player from crossing upward past the barrier
                if old_pos.y >= barrier_y and player_y < barrier_y:
                    # Block the player at the barrier line
                    self.player.pos.y = barrier_y

        # Check if player crossed into next region
        if self.active_region_index < len(self.regions) - 1:
            next_region = self.regions[self.active_region_index + 1]
            if self.player.pos.y < next_region['max_y']:
                # Player entered next region
                self.active_region_index += 1
                self.current_wave_index += 1
                # Show ASL popup for new letters
                wave_data = self._get_wave_data(self.current_wave_index)
                letters = wave_data.get('letters', [])
                showing_popup = self._show_asl_popup_for_letters(letters)
                # Only spawn if popup is not showing
                if not showing_popup:
                    self._spawn_wave(self.current_wave_index)
        
        # Check for player death
        if not self.player.is_alive and self.player.is_animation_finished():
            if not self.show_death_dialog:
                self.show_death_dialog = True
                self.death_panel.show_death(game_state.game_has_savegame)
    
    def _check_tile_collision(self, entity) -> bool:
        """
        Check if an entity collides with collision tiles or decoration objects.
        
        Args:
            entity: Entity with pos attribute
            
        Returns:
            True if collision detected
        """
        # Convert entity position to tilemap coordinates (unscaled)
        tile_x = entity.pos.x / SCALE
        tile_y = entity.pos.y / SCALE
        
        # Check a small area around the entity center for cliff collision
        check_radius = 8  # pixels in tilemap space
        
        for dx in [-check_radius, 0, check_radius]:
            for dy in [-check_radius, 0, check_radius]:
                if self.tilemap.is_position_blocked(tile_x + dx, tile_y + dy):
                    return True
        
        # Check collision with decoration objects (trees, rocks, etc.)
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
        """Check if a position is within the world boundaries."""
        margin = 50  # Some buffer for spells
        return (
            -margin < pos.x < self.world_pixel_width + margin and
            -margin < pos.y < self.world_pixel_height + margin
        )
    
    def _check_spell_combat(self):
        """Check for spell-enemy collisions."""
        for spell in list(self.spells):
            if not spell.is_alive:
                continue
            
            spell_hitbox = spell.get_hitbox()
            
            for enemy in self.enemies:
                if enemy.is_alive:
                    enemy_hitbox = enemy.get_hitbox()
                    if spell_hitbox.colliderect(enemy_hitbox):
                        # Check if spell can hit this target (letter restriction)
                        if not spell.can_hit_target(enemy.letter):
                            continue  # Spell passes through - wrong letter
                        
                        # Spell hits enemy
                        enemy.take_damage(spell.damage)
                        spell.destroy()
                        # Remove spell from groups
                        if spell in self.spells:
                            self.spells.remove(spell)
                        if spell in self.all_sprites:
                            self.all_sprites.remove(spell)
                        break  # Spell can only hit one enemy
    
    def _check_spell_undine_combat(self):
        """Check for spell-undine collisions."""
        for spell in list(self.spells):
            if not spell.is_alive:
                continue
            
            spell_hitbox = spell.get_hitbox()
            
            for undine in self.undine_manager.undines:
                if undine.alive:
                    if spell_hitbox.colliderect(undine.rect):
                        # Check if spell can hit this target (letter restriction)
                        if not spell.can_hit_target(undine.letter):
                            continue  # Spell passes through - wrong letter
                        
                        # Spell hits undine
                        undine.take_damage(spell.damage)
                        spell.destroy()
                        # Remove spell from groups
                        if spell in self.spells:
                            self.spells.remove(spell)
                        if spell in self.all_sprites:
                            self.all_sprites.remove(spell)
                        break  # Spell can only hit one undine
    
    def _check_undine_spell_player_combat(self):
        """Check for undine spell collisions with player."""
        for spell in list(self.undine_manager.spells):
            if not spell.is_alive:
                continue
            
            spell_hitbox = spell.get_hitbox()
            player_hitbox = self.player.rect
            
            if spell_hitbox.colliderect(player_hitbox):
                if self.player.is_blocking:
                    # Player is blocking - destroy the spell without taking damage
                    spell.destroy()
                    if spell in self.undine_manager.spells:
                        self.undine_manager.spells.remove(spell)
                else:
                    # Undine spell hits player
                    self.player.take_damage(spell.damage)
                    spell.destroy()
                    # Remove spell from manager
                    if spell in self.undine_manager.spells:
                        self.undine_manager.spells.remove(spell)
                break  # Spell can only hit once
    
    def _check_lich_lightning_player_combat(self):
        """Check for lich lightning bolt collisions with player."""
        for enemy in self.enemies:
            if not isinstance(enemy, Lich):
                continue
            for bolt in list(enemy.lightning_bolts):
                if not bolt.is_alive:
                    continue
                bolt_hitbox = bolt.get_hitbox()
                player_hitbox = self.player.rect
                if bolt_hitbox.colliderect(player_hitbox):
                    if self.player.is_blocking:
                        bolt.destroy()
                        if bolt in enemy.lightning_bolts:
                            enemy.lightning_bolts.remove(bolt)
                    else:
                        self.player.take_damage(bolt.damage)
                        bolt.destroy()
                        if bolt in enemy.lightning_bolts:
                            enemy.lightning_bolts.remove(bolt)
                    break  # One bolt hit per frame

    def _process_camera_input(self, dt: float):
        """Process camera input for ASL letter detection."""
        # Update no-target feedback timer
        if self._no_target_timer > 0:
            self._no_target_timer -= dt
            if self._no_target_timer <= 0:
                self._no_target_letter = None
        
        if self.camera_input is None or not self.camera_input.is_available():
            return
        
        # Get pending confirmed letters
        pending_letters = self.camera_input.get_pending_letters()
        
        for letter in pending_letters:
            self._handle_camera_letter(letter)
    
    def _handle_camera_letter(self, letter: str):
        """
        Handle a confirmed letter from camera input.
        
        'B' is reserved for blocking (unlocked from wave 2 onward).
        All other letters find the closest enemy and fire a spell at it.
        """
        if not self.player.is_alive:
            return
        
        # B is always the block command (unlocked at wave 2)
        if letter.upper() == 'B':
            if self.current_wave_index >= 1:  # wave 2 = index 1
                self.player.start_block()
            return
        
        # Find closest enemy with matching letter
        target = find_closest_enemy_by_letter(self.enemies, letter, self.player.pos)
        
        # Also check undines
        target_undine = self._find_closest_undine_by_letter(letter)
        
        # Compare distances if both found
        if target and target_undine:
            dist_enemy = self.player.pos.distance_to(target.pos)
            dist_undine = self.player.pos.distance_to(target_undine.pos)
            if dist_undine < dist_enemy:
                target = None  # Use undine instead
            else:
                target_undine = None  # Use enemy instead
        
        # Fire at target
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
        else:
            # No target found - show feedback
            self._no_target_timer = 1.5  # Show "No Target" for 1.5 seconds
            self._no_target_letter = letter
    
    def _next_spell_type(self) -> str:
        """Get the next spell type in the rotation and advance the index."""
        spell_type = SPELL_TYPES[self._spell_type_index]
        self._spell_type_index = (self._spell_type_index + 1) % len(SPELL_TYPES)
        return spell_type
    
    def _find_closest_undine_by_letter(self, letter: str):
        """Find the closest alive undine with matching letter."""
        letter = letter.upper()
        matching = [u for u in self.undine_manager.undines 
                   if u.alive and u.letter == letter]
        
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
    
    def _draw_barriers(self, screen: pygame.Surface):
        """Draw the active barrier for the current region as a shiny magic wall."""
        import math
        time = pygame.time.get_ticks() / 1000.0

        # Only draw the barrier for the current active region
        if self.active_region_index >= len(self.barriers):
            return

        barrier = self.barriers[self.active_region_index]
        if not barrier['active']:
            return

        # Get screen Y position (barrier spans full screen width)
        _, screen_y = self.camera.world_to_screen(0, barrier['y'])

        # Faster, more dramatic pulse
        pulse = (math.sin(time * 3) + 1) / 2  # 0 to 1
        alpha = int(100 + pulse * 100)  # 100 to 200, very visible

        # Draw shiny gradient wall across entire screen
        barrier_height = 8
        screen_width = screen.get_width()
        barrier_surface = pygame.Surface((screen_width, barrier_height), pygame.SRCALPHA)

        # Gradient from purple to bright pink/magenta
        for y in range(barrier_height):
            ratio = y / barrier_height
            r = int(140 + ratio * 60)
            g = int(80 + ratio * 40)
            b = int(200 + ratio * 55)
            color = (r, g, b, alpha)
            pygame.draw.line(barrier_surface, color, (0, y), (screen_width, y))

        screen.blit(barrier_surface, (0, screen_y - barrier_height // 2))

        # Draw sparkling particles
        num_sparkles = 8
        for i in range(num_sparkles):
            sparkle_x = (screen_width * i / num_sparkles) + math.sin(time * 2 + i) * 30
            sparkle_y = screen_y - barrier_height // 2 + math.cos(time * 3 + i) * 12
            sparkle_alpha = int(180 + pulse * 75)
            sparkle_size = int(3 + pulse * 2)
            pygame.draw.circle(screen, (220, 180, 255, sparkle_alpha),
                               (int(sparkle_x), int(sparkle_y)), sparkle_size)

    def draw(self, screen: pygame.Surface):
        # Clear screen
        screen.fill((20, 30, 20))
        
        # Draw tilemap background with camera offset
        self.camera.apply_to_surface(self.background, screen)

        # Draw active barriers (magic walls)
        self._draw_barriers(screen)

        # Build combined list of sprites and decorations for y-sorting
        # Each item: (sort_y, type, data)
        # type 'sprite': data = sprite
        # type 'decor': data = (surface, world_x, world_y)
        # type 'undine': data = undine
        y_sort_items = []
        
        # Add sprites
        for sprite in self.all_sprites:
            y_sort_items.append((sprite.pos.y, 'sprite', sprite))
        
        # Add undines
        for undine in self.undine_manager.undines:
            if undine.alive:
                y_sort_items.append((undine.pos.y, 'undine', undine))
        
        # Add undine spells
        for spell in self.undine_manager.spells:
            if spell.is_alive:
                y_sort_items.append((spell.pos.y, 'spell', spell))
        
        # Add lich lightning bolts
        for enemy in self.enemies:
            if isinstance(enemy, Lich):
                for bolt in enemy.lightning_bolts:
                    if bolt.is_alive:
                        y_sort_items.append((bolt.pos.y, 'spell', bolt))
        
        # Add decorations
        for surface, world_x, world_y, sort_y in self.decorations:
            y_sort_items.append((sort_y, 'decor', (surface, world_x, world_y)))
        
        # Sort by y position
        y_sort_items.sort(key=lambda item: item[0])
        
        # Draw sorted items
        for sort_y, item_type, data in y_sort_items:
            if item_type == 'sprite':
                sprite = data
                screen_x, screen_y = self.camera.world_to_screen(
                    sprite.rect.x, sprite.rect.y
                )
                screen.blit(sprite.image, (screen_x, screen_y))
            elif item_type == 'undine':
                undine = data
                screen_x, screen_y = self.camera.world_to_screen(
                    undine.rect.x, undine.rect.y
                )
                screen.blit(undine.image, (screen_x, screen_y))
            elif item_type == 'spell':
                spell = data
                screen_x, screen_y = self.camera.world_to_screen(
                    spell.rect.x, spell.rect.y
                )
                screen.blit(spell.image, (screen_x, screen_y))
            else:  # 'decor'
                surface, world_x, world_y = data
                screen_x, screen_y = self.camera.world_to_screen(world_x, world_y)
                screen.blit(surface, (screen_x, screen_y))
        
        # Draw entity health bars (in screen space)
        self._draw_entity_health_bars(screen)
        
        # Draw HUD (fixed to screen, not affected by camera)
        self.hud.draw(screen, self.player, game_state)
        
        # Draw wave display (top center)
        wave_cleared_notification = self.wave_cleared_timer > 0
        self.wave_display.draw(
            screen,
            self._get_current_wave_number(),
            wave_cleared_notification
        )
        
        # Controls
        controls = self.font.render("WASD: Move | ESC: Menu", True, (180, 180, 180))
        screen.blit(controls, (10, SCREEN_HEIGHT - 25))
        
        # Enemy count (including undines)
        enemy_count = len([e for e in self.enemies if e.is_alive])
        undine_count = self.undine_manager.get_alive_count()
        count_text = self.font.render(f"Enemies: {enemy_count}", True, (200, 200, 200))
        screen.blit(count_text, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 25))
        
        # Camera letter display (ASL detection feedback)
        if self.camera_input is not None and not self._waiting_for_camera_ready:
            detected_letter, hold_progress = self.camera_input.get_current_detection()
            state = self.camera_input.get_state()
            self.camera_letter_display.draw(
                screen, 
                detected_letter, 
                hold_progress,
                state,
                self._no_target_letter,
                self._no_target_timer > 0
            )
        
        # Camera startup overlay
        if self._waiting_for_camera_ready:
            self._draw_camera_startup_overlay(screen)
        
        # Death panel
        self.death_panel.draw(screen)
        
        # ASL Popup (shown over everything else)
        if self._showing_asl_popup:
            self.asl_popup.draw(screen)
        
        # Sign reference panel (NPC interaction)
        self.sign_panel.draw(screen)
    
    def _draw_entity_health_bars(self, screen):
        """Draw health bars and letters above entities (in screen space)."""
        # Player health bar above sprite
        player_screen_x, player_screen_y = self.camera.world_to_screen(
            self.player.pos.x, self.player.pos.y - 35
        )
        self._draw_health_bar(screen, player_screen_x, player_screen_y,
                              self.player.health, self.player.max_health)
        
        # Enemy health bars and letters
        for enemy in self.enemies:
            if enemy.is_alive:
                enemy_screen_x, enemy_screen_y = self.camera.world_to_screen(
                    enemy.pos.x, enemy.pos.y - 25
                )
                self._draw_health_bar(screen, enemy_screen_x, enemy_screen_y,
                                     enemy.health, enemy.max_health, width=30, height=4)
            # Draw letter always (even when dead, per requirements)
            enemy_center_x, enemy_center_y = self.camera.world_to_screen(
                enemy.pos.x, enemy.pos.y
            )
            enemy.draw_letter(screen, enemy_center_x, enemy_center_y)
        
        # Undine health bars and letters
        for undine in self.undine_manager.undines:
            if undine.alive and undine.health < undine.max_health:
                undine_screen_x, undine_screen_y = self.camera.world_to_screen(
                    undine.pos.x, undine.pos.y - 40
                )
                self._draw_health_bar(screen, undine_screen_x, undine_screen_y,
                                     undine.health, undine.max_health, width=40, height=4)
            # Draw letter always (even when dead, per requirements)
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
    
    def _draw_camera_startup_overlay(self, screen: pygame.Surface):
        """Draw overlay while waiting for camera to be ready."""
        # Semi-transparent dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Check camera status
        camera_ready = self.camera_input is not None and self.camera_input.is_available()
        
        # Title
        title_text = self._camera_ready_font.render("Camera Setup", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        screen.blit(title_text, title_rect)
        
        # Status message
        if camera_ready:
            status_color = (100, 255, 100)
            status_msg = "Camera is ready!"
            instruction_msg = "Position your camera window, then press ENTER to start"
        else:
            status_color = (255, 200, 100)
            if self.camera_input is None:
                status_msg = "Camera not available"
                instruction_msg = "Press ENTER to start without camera"
            else:
                error = self.camera_input.get_error_message()
                if error:
                    status_msg = f"Camera error: {error}"
                    instruction_msg = "Press ENTER to start without camera"
                else:
                    status_msg = "Waiting for camera to initialize..."
                    instruction_msg = "Please wait..."
        
        status_text = self._camera_ready_font.render(status_msg, True, status_color)
        status_rect = status_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(status_text, status_rect)
        
        # Instruction
        instruction_font = pygame.font.Font(None, 28)
        instruction_text = instruction_font.render(instruction_msg, True, (200, 200, 200))
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        screen.blit(instruction_text, instruction_rect)
        
        # Tips
        tips = [
            "Tips:",
            "- Position the camera window where you can see it",
            "- Make sure your hand is visible in the camera",
            "- Good lighting helps with detection"
        ]
        tip_font = pygame.font.Font(None, 22)
        tip_y = SCREEN_HEIGHT // 2 + 90
        for tip in tips:
            tip_text = tip_font.render(tip, True, (150, 150, 150))
            tip_rect = tip_text.get_rect(center=(SCREEN_WIDTH // 2, tip_y))
            screen.blit(tip_text, tip_rect)
            tip_y += 25
