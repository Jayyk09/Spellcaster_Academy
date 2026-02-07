"""World scene - main gameplay area with tilemap and camera."""
import pygame
import os
from core.scene import Scene
from core.game_state import game_state
from core.ui import HUD, DeathPanel, HealthBar, CameraLetterDisplay
from core.camera import Camera
from core.map_loader import load_map_data, create_tilemap_from_data, get_spawn_points, get_transitions
from entities.player import Player
from entities.enemy import Slime, Skeleton, find_closest_enemy_by_letter
from entities.undine import UndineManager
from entities.spell import SpellProjectile
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SPRITES_DIR,
    TILE_SIZE, SCALE, WORLD_WIDTH, WORLD_HEIGHT,
    WORLD_WIDTH_TILES, WORLD_HEIGHT_TILES, CAMERA_DRAG_MARGIN,
    SPELL_DAMAGE, CAMERA_ENABLED, CAMERA_HOLD_TIME, CAMERA_CONFIDENCE,
    CAMERA_DEFAULT_SPELL, CAMERA_SHOW_PREVIEW
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
        
        # Set camera to follow player
        self.camera.set_target(self.player.pos)
        self.camera.center_on(self.player.pos.x, self.player.pos.y)
        
        # Create enemies at spawn points
        self.enemies = pygame.sprite.Group()
        enemy_spawns = spawn_points.get('enemies', [])
        for spawn in enemy_spawns:
            x = spawn['x'] * TILE_SIZE * SCALE + (TILE_SIZE * SCALE // 2)
            y = spawn['y'] * TILE_SIZE * SCALE + (TILE_SIZE * SCALE // 2)
            enemy_type = spawn.get('type', 'slime')
            
            if enemy_type == 'skeleton':
                enemy = Skeleton(x, y)
            else:
                enemy = Slime(x, y)
            
            enemy.set_target(self.player)
            self.enemies.add(enemy)
        
        # Mushrooms disabled - sprite removed
        self.mushrooms = []
        
        # Create Undine manager and spawn undines
        self.undine_manager = UndineManager(self.world_pixel_width, self.world_pixel_height)
        self.undine_manager.spawn_random(5)  # Spawn 5 undines at random positions
        
        # All sprites for rendering
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        for enemy in self.enemies:
            self.all_sprites.add(enemy)
        
        # Spell projectiles
        self.spells = pygame.sprite.Group()
        
        # Scene exit area (to camp) from map data
        transitions = get_transitions(self.map_data)
        camp_transition = transitions.get('to_camp', {'x': 0, 'y': 4, 'width': 1, 'height': 6})
        self.exit_to_camp = pygame.Rect(
            camp_transition['x'] * TILE_SIZE * SCALE,
            camp_transition['y'] * TILE_SIZE * SCALE,
            camp_transition['width'] * TILE_SIZE * SCALE,
            camp_transition['height'] * TILE_SIZE * SCALE
        )
        
        # UI
        self.hud = HUD()
        self.death_panel = DeathPanel()
        self.show_death_dialog = False
        
        # Camera input (ASL detection)
        self.camera_input = None
        self.camera_letter_display = CameraLetterDisplay()
        self._no_target_timer = 0.0  # Timer for "No Target" feedback
        self._no_target_letter = None  # Letter that had no target
        
        if CAMERA_ENABLED:
            try:
                from vision.camera_input import CameraInput
                self.camera_input = CameraInput(
                    hold_time=CAMERA_HOLD_TIME,
                    confidence_threshold=CAMERA_CONFIDENCE,
                    show_preview=CAMERA_SHOW_PREVIEW
                )
                self.camera_input.start()
            except Exception as e:
                print(f"Camera input not available: {e}")
                self.camera_input = None
        
        # Font for extra UI
        self.font = pygame.font.Font(None, 24)
    
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
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Handle death dialog input
            if self.show_death_dialog:
                if event.key == pygame.K_y and game_state.game_has_savegame:
                    # Load save and go to camp
                    game_state.load_game()
                    self.next_scene = 'camp'
                elif event.key == pygame.K_n:
                    # Quit to menu
                    self.next_scene = 'menu'
                return
            
            # Handle spell casting
            spell = self.player.handle_spell_input(event.key)
            if spell:
                self.spells.add(spell)
                self.all_sprites.add(spell)
            
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
    
    def update(self, dt: float):
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
        
        # Check spell-undine combat
        self._check_spell_undine_combat()
        
        # Mushrooms disabled - sprite removed
        
        # Clean up dead enemies
        for enemy in list(self.enemies):
            if not enemy.is_alive and enemy.is_animation_finished():
                game_state.player_exp += enemy.xp_value
                self.enemies.remove(enemy)
                self.all_sprites.remove(enemy)
        
        # Check scene transitions
        self._check_transitions()
        
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
    
    def _check_transitions(self):
        """Check if player entered a transition area."""
        player_rect = self.player.get_collision_rect()
        
        if player_rect.colliderect(self.exit_to_camp):
            game_state.player_exit_pos = (SCREEN_WIDTH - 50, self.player.pos.y)
            self.next_scene = 'camp'
    
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
        
        Finds the closest enemy with matching letter and fires a spell at it.
        """
        if not self.player.is_alive:
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
            spell = SpellProjectile.create_targeted(
                self.player.pos,
                target.pos,
                CAMERA_DEFAULT_SPELL,
                letter
            )
            self.spells.add(spell)
            self.all_sprites.add(spell)
        elif target_undine:
            spell = SpellProjectile.create_targeted(
                self.player.pos,
                target_undine.pos,
                CAMERA_DEFAULT_SPELL,
                letter
            )
            self.spells.add(spell)
            self.all_sprites.add(spell)
        else:
            # No target found - show feedback
            self._no_target_timer = 1.5  # Show "No Target" for 1.5 seconds
            self._no_target_letter = letter
    
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
    
    def draw(self, screen: pygame.Surface):
        # Clear screen
        screen.fill((20, 30, 20))
        
        # Draw tilemap background with camera offset
        self.camera.apply_to_surface(self.background, screen)
        
        # Draw exit area indicator (in world coords, apply camera)
        exit_screen_rect = self.camera.apply_to_rect(self.exit_to_camp)
        pygame.draw.rect(screen, (100, 150, 255), exit_screen_rect, 2)
        exit_font = pygame.font.Font(None, 18)
        exit_text = exit_font.render("Camp", True, (150, 200, 255))
        screen.blit(exit_text, (exit_screen_rect.x + 2, exit_screen_rect.centery - 8))
        
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
            else:  # 'decor'
                surface, world_x, world_y = data
                screen_x, screen_y = self.camera.world_to_screen(world_x, world_y)
                screen.blit(surface, (screen_x, screen_y))
        
        # Draw entity health bars (in screen space)
        self._draw_entity_health_bars(screen)
        
        # Draw HUD (fixed to screen, not affected by camera)
        self.hud.draw(screen, self.player, game_state)
        
        # Scene label
        scene_text = self.font.render("WORLD", True, (200, 200, 100))
        screen.blit(scene_text, (SCREEN_WIDTH - 70, 10))
        
        # Current spell indicator
        spell_name = self.player.get_current_spell_name().capitalize()
        spell_text = self.font.render(f"Next Spell: {spell_name}", True, (150, 200, 255))
        screen.blit(spell_text, (SCREEN_WIDTH - 150, 35))
        
        # Controls
        controls = self.font.render("WASD: Move | Space: Cast Spell | ESC: Menu", True, (180, 180, 180))
        screen.blit(controls, (10, SCREEN_HEIGHT - 25))
        
        # Enemy count (including undines)
        enemy_count = len([e for e in self.enemies if e.is_alive])
        undine_count = self.undine_manager.get_alive_count()
        count_text = self.font.render(f"Enemies: {enemy_count} | Undines: {undine_count}", True, (200, 200, 200))
        screen.blit(count_text, (SCREEN_WIDTH - 220, SCREEN_HEIGHT - 25))
        
        # Camera letter display (ASL detection feedback)
        if self.camera_input is not None:
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
        
        # Death panel
        self.death_panel.draw(screen)
    
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
