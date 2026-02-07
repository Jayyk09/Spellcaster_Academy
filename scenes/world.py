"""World scene - main gameplay area with tilemap and camera."""
import pygame
import os
from core.scene import Scene
from core.game_state import game_state
from core.ui import HUD, DeathPanel, HealthBar
from core.camera import Camera
from core.map_loader import load_map_data, create_tilemap_from_data, get_spawn_points, get_transitions
from entities.player import Player
from entities.enemy import Slime
from entities.collectibles import Mushroom
from entities.spell import SpellProjectile
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SPRITES_DIR,
    TILE_SIZE, SCALE, WORLD_WIDTH, WORLD_HEIGHT,
    WORLD_WIDTH_TILES, WORLD_HEIGHT_TILES, CAMERA_DRAG_MARGIN,
    SPELL_DAMAGE
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
            slime = Slime(x, y)
            slime.set_target(self.player)
            self.enemies.add(slime)
        
        # Create collectibles at spawn points
        self.mushrooms: list[Mushroom] = []
        mushroom_spawns = spawn_points.get('mushrooms', [])
        for spawn in mushroom_spawns:
            x = spawn['x'] * TILE_SIZE * SCALE + (TILE_SIZE * SCALE // 2)
            y = spawn['y'] * TILE_SIZE * SCALE + (TILE_SIZE * SCALE // 2)
            mushroom = Mushroom(x, y)
            self.mushrooms.append(mushroom)
        
        # All sprites for rendering
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        for enemy in self.enemies:
            self.all_sprites.add(enemy)
        for mushroom in self.mushrooms:
            self.all_sprites.add(mushroom)
        
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
        
        # Update mushrooms - now harvested by spells
        for mushroom in list(self.mushrooms):
            # Check if any spell hits the mushroom
            for spell in list(self.spells):
                if spell.is_alive:
                    spell_hitbox = spell.get_hitbox()
                    mushroom_hitbox = pygame.Rect(
                        mushroom.pos.x - 10, mushroom.pos.y - 10, 20, 20
                    )
                    if spell_hitbox.colliderect(mushroom_hitbox) and not mushroom.collected:
                        mushroom.try_harvest(spell_hitbox)
                        # Don't destroy spell on mushroom hit, let it pass through
            
            chunks = mushroom.update(dt)
            if chunks > 0:
                game_state.shroom_chunks += chunks
            if mushroom.is_fully_collected():
                self.mushrooms.remove(mushroom)
                self.all_sprites.remove(mushroom)
        
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
        Check if an entity collides with collision tiles.
        
        Args:
            entity: Entity with pos attribute
            
        Returns:
            True if collision detected
        """
        # Convert entity position to tilemap coordinates (unscaled)
        tile_x = entity.pos.x / SCALE
        tile_y = entity.pos.y / SCALE
        
        # Check a small area around the entity center
        check_radius = 8  # pixels in tilemap space
        
        for dx in [-check_radius, 0, check_radius]:
            for dy in [-check_radius, 0, check_radius]:
                if self.tilemap.is_position_blocked(tile_x + dx, tile_y + dy):
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
                        # Spell hits enemy
                        enemy.take_damage(spell.damage)
                        spell.destroy()
                        # Remove spell from groups
                        if spell in self.spells:
                            self.spells.remove(spell)
                        if spell in self.all_sprites:
                            self.all_sprites.remove(spell)
                        break  # Spell can only hit one enemy
    
    def _check_transitions(self):
        """Check if player entered a transition area."""
        player_rect = self.player.get_collision_rect()
        
        if player_rect.colliderect(self.exit_to_camp):
            game_state.player_exit_pos = (SCREEN_WIDTH - 50, self.player.pos.y)
            self.next_scene = 'camp'
    
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
        
        # Y-sort and draw sprites (apply camera offset)
        sorted_sprites = sorted(self.all_sprites, key=lambda s: s.pos.y)
        for sprite in sorted_sprites:
            # Convert world position to screen position
            screen_x, screen_y = self.camera.world_to_screen(
                sprite.rect.x, sprite.rect.y
            )
            screen.blit(sprite.image, (screen_x, screen_y))
        
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
        
        # Enemy/mushroom count
        enemy_count = len([e for e in self.enemies if e.is_alive])
        mushroom_count = len([m for m in self.mushrooms if not m.collected])
        count_text = self.font.render(f"Enemies: {enemy_count} | Mushrooms: {mushroom_count}", True, (200, 200, 200))
        screen.blit(count_text, (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 25))
        
        # Death panel
        self.death_panel.draw(screen)
    
    def _draw_entity_health_bars(self, screen):
        """Draw health bars above entities (in screen space)."""
        # Player health bar above sprite
        player_screen_x, player_screen_y = self.camera.world_to_screen(
            self.player.pos.x, self.player.pos.y - 35
        )
        self._draw_health_bar(screen, player_screen_x, player_screen_y,
                              self.player.health, self.player.max_health)
        
        # Enemy health bars
        for enemy in self.enemies:
            if enemy.is_alive:
                enemy_screen_x, enemy_screen_y = self.camera.world_to_screen(
                    enemy.pos.x, enemy.pos.y - 25
                )
                self._draw_health_bar(screen, enemy_screen_x, enemy_screen_y,
                                     enemy.health, enemy.max_health, width=30, height=4)
    
    def _draw_health_bar(self, surface, x, y, health, max_health, width=50, height=5):
        health_ratio = max(0, health / max_health)
        pygame.draw.rect(surface, (80, 20, 20), (x - width/2, y, width, height))
        pygame.draw.rect(surface, (50, 180, 50), (x - width/2, y, width * health_ratio, height))
        pygame.draw.rect(surface, (40, 40, 40), (x - width/2, y, width, height), 1)
