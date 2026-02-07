"""World scene - main gameplay area."""
import pygame
from core.scene import Scene
from core.game_state import game_state
from core.ui import HUD, DeathPanel, HealthBar
from entities.player import Player
from entities.enemy import Slime
from entities.collectibles import Mushroom
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_ATTACK_DAMAGE


class WorldScene(Scene):
    """Main world gameplay scene."""
    
    def __init__(self, game, **kwargs):
        super().__init__(game)
        
        # Create player
        start_x, start_y = game_state.player_start_pos
        self.player = Player(start_x, start_y)
        
        # Create enemies
        self.enemies = pygame.sprite.Group()
        self._spawn_enemies()
        
        # Create collectibles
        self.mushrooms: list[Mushroom] = []
        self._spawn_mushrooms()
        
        # All sprites for rendering
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        for enemy in self.enemies:
            self.all_sprites.add(enemy)
        for mushroom in self.mushrooms:
            self.all_sprites.add(mushroom)
        
        # Scene exit area (to camp)
        self.exit_to_camp = pygame.Rect(0, 100, 20, 100)  # Left edge
        
        # UI
        self.hud = HUD()
        self.death_panel = DeathPanel()
        self.show_death_dialog = False
        
        # Font for extra UI
        self.font = pygame.font.Font(None, 24)
    
    def _spawn_enemies(self):
        """Spawn enemies in the world."""
        enemy_positions = [
            (600, 300),
            (200, 150),
            (500, 400),
        ]
        
        for x, y in enemy_positions:
            slime = Slime(x, y)
            slime.set_target(self.player)
            self.enemies.add(slime)
    
    def _spawn_mushrooms(self):
        """Spawn collectible mushrooms."""
        mushroom_positions = [
            (350, 100),
            (650, 200),
            (150, 350),
            (450, 450),
        ]
        
        for x, y in mushroom_positions:
            mushroom = Mushroom(x, y)
            self.mushrooms.append(mushroom)
    
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
            
            self.player.handle_attack_input(event.key)
            
            if event.key == pygame.K_ESCAPE:
                self.next_scene = 'menu'
            
            # Debug: respawn
            if event.key == pygame.K_r:
                self.player.respawn(*game_state.player_start_pos)
                self.show_death_dialog = False
                self.death_panel.hide()
    
    def update(self, dt: float):
        # Get input
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        # Update player
        self.player.update(dt)
        
        # Clamp player to screen
        self.player.pos.x = max(24, min(SCREEN_WIDTH - 24, self.player.pos.x))
        self.player.pos.y = max(24, min(SCREEN_HEIGHT - 24, self.player.pos.y))
        
        # Update enemies
        for enemy in self.enemies:
            enemy.update(dt)
            enemy.pos.x = max(16, min(SCREEN_WIDTH - 16, enemy.pos.x))
            enemy.pos.y = max(16, min(SCREEN_HEIGHT - 16, enemy.pos.y))
        
        # Check combat
        self._check_combat()
        
        # Update mushrooms
        attack_hitbox = self.player.get_attack_hitbox()
        for mushroom in list(self.mushrooms):
            # Try to harvest if player is attacking
            mushroom.try_harvest(attack_hitbox)
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
    
    def _check_combat(self):
        """Check for combat interactions."""
        attack_hitbox = self.player.get_attack_hitbox()
        if attack_hitbox:
            for enemy in self.enemies:
                if enemy.is_alive:
                    enemy_hitbox = enemy.get_hitbox()
                    if attack_hitbox.colliderect(enemy_hitbox):
                        enemy.take_damage(PLAYER_ATTACK_DAMAGE)
    
    def _check_transitions(self):
        """Check if player entered a transition area."""
        player_rect = self.player.get_collision_rect()
        
        if player_rect.colliderect(self.exit_to_camp):
            game_state.player_exit_pos = (SCREEN_WIDTH - 50, self.player.pos.y)
            self.next_scene = 'camp'
    
    def draw(self, screen: pygame.Surface):
        # Background
        screen.fill((45, 65, 45))  # Grass green
        
        # Draw exit area indicator
        pygame.draw.rect(screen, (100, 150, 255), self.exit_to_camp, 2)
        exit_font = pygame.font.Font(None, 18)
        exit_text = exit_font.render("Camp", True, (150, 200, 255))
        screen.blit(exit_text, (2, self.exit_to_camp.centery - 8))
        
        # Y-sort and draw sprites
        sorted_sprites = sorted(self.all_sprites, key=lambda s: s.pos.y)
        for sprite in sorted_sprites:
            screen.blit(sprite.image, sprite.rect)
        
        # Draw attack hitbox (debug - can be removed)
        hitbox = self.player.get_attack_hitbox()
        if hitbox:
            pygame.draw.rect(screen, (255, 100, 100, 128), hitbox, 1)
        
        # Draw entity health bars
        self._draw_entity_health_bars(screen)
        
        # Draw HUD
        self.hud.draw(screen, self.player, game_state)
        
        # Scene label
        scene_text = self.font.render("WORLD", True, (200, 200, 100))
        screen.blit(scene_text, (SCREEN_WIDTH - 70, 10))
        
        # Controls
        controls = self.font.render("WASD: Move | Space: Attack | ESC: Menu", True, (180, 180, 180))
        screen.blit(controls, (10, SCREEN_HEIGHT - 25))
        
        # Enemy/mushroom count
        enemy_count = len([e for e in self.enemies if e.is_alive])
        mushroom_count = len([m for m in self.mushrooms if not m.collected])
        count_text = self.font.render(f"Enemies: {enemy_count} | Mushrooms: {mushroom_count}", True, (200, 200, 200))
        screen.blit(count_text, (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 25))
        
        # Death panel
        self.death_panel.draw(screen)
    
    def _draw_entity_health_bars(self, screen):
        """Draw health bars above entities."""
        # Player health bar above sprite
        self._draw_health_bar(screen, self.player.pos.x, self.player.pos.y - 35,
                              self.player.health, self.player.max_health)
        
        # Enemy health bars
        for enemy in self.enemies:
            if enemy.is_alive:
                self._draw_health_bar(screen, enemy.pos.x, enemy.pos.y - 25,
                                     enemy.health, enemy.max_health, width=30, height=4)
    
    def _draw_health_bar(self, surface, x, y, health, max_health, width=50, height=5):
        health_ratio = max(0, health / max_health)
        pygame.draw.rect(surface, (80, 20, 20), (x - width/2, y, width, height))
        pygame.draw.rect(surface, (50, 180, 50), (x - width/2, y, width * health_ratio, height))
        pygame.draw.rect(surface, (40, 40, 40), (x - width/2, y, width, height), 1)
