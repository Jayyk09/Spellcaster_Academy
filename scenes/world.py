"""World scene - main gameplay area."""
import pygame
from core.scene import Scene
from core.game_state import game_state
from entities.player import Player
from entities.enemy import Slime
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
        
        # All sprites for rendering
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        for enemy in self.enemies:
            self.all_sprites.add(enemy)
        
        # Scene exit area (to camp)
        self.exit_to_camp = pygame.Rect(0, 100, 20, 100)  # Left edge
        
        # Font for UI
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
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.player.handle_attack_input(event.key)
            
            if event.key == pygame.K_ESCAPE:
                self.next_scene = 'menu'
            
            # Debug: respawn
            if event.key == pygame.K_r:
                self.player.respawn(*game_state.player_start_pos)
    
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
            # Go back to menu or show death screen
            pass  # We'll handle this later with a death dialog
    
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
        
        # Draw exit area (debug)
        pygame.draw.rect(screen, (100, 100, 255, 100), self.exit_to_camp, 2)
        
        # Y-sort and draw sprites
        sorted_sprites = sorted(self.all_sprites, key=lambda s: s.pos.y)
        for sprite in sorted_sprites:
            screen.blit(sprite.image, sprite.rect)
        
        # Draw attack hitbox
        hitbox = self.player.get_attack_hitbox()
        if hitbox:
            pygame.draw.rect(screen, (255, 100, 100), hitbox, 2)
        
        # Draw health bars
        self._draw_health_bar(screen, self.player.pos.x, self.player.pos.y - 35, 
                              self.player.health, self.player.max_health)
        
        for enemy in self.enemies:
            if enemy.is_alive:
                self._draw_health_bar(screen, enemy.pos.x, enemy.pos.y - 25,
                                     enemy.health, enemy.max_health, width=30, height=4)
        
        # UI
        self._draw_ui(screen)
    
    def _draw_health_bar(self, surface, x, y, health, max_health, width=50, height=5):
        health_ratio = max(0, health / max_health)
        pygame.draw.rect(surface, (100, 0, 0), (x - width/2, y, width, height))
        pygame.draw.rect(surface, (0, 200, 0), (x - width/2, y, width * health_ratio, height))
    
    def _draw_ui(self, screen):
        # State info
        state_text = self.font.render(
            f"HP: {self.player.health}/{self.player.max_health} | EXP: {game_state.player_exp}", 
            True, (255, 255, 255)
        )
        screen.blit(state_text, (10, 10))
        
        # Scene label
        scene_text = self.font.render("WORLD", True, (200, 200, 100))
        screen.blit(scene_text, (SCREEN_WIDTH - 70, 10))
        
        # Controls
        controls = self.font.render("WASD: Move | Space: Attack | ESC: Menu", True, (180, 180, 180))
        screen.blit(controls, (10, SCREEN_HEIGHT - 25))
        
        # Enemy count
        enemy_count = len([e for e in self.enemies if e.is_alive])
        enemy_text = self.font.render(f"Enemies: {enemy_count}", True, (255, 255, 255))
        screen.blit(enemy_text, (10, 35))
