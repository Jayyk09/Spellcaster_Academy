"""Camp scene - safe area with save point."""
import pygame
from core.scene import Scene
from core.game_state import game_state
from entities.player import Player
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, SPRITES_DIR
import os


class CampScene(Scene):
    """Camp/safe area with campfire save point."""
    
    def __init__(self, game, **kwargs):
        super().__init__(game)
        
        # Load background
        self.background = self._create_background()
        
        # Create player at exit position or load position
        start_x, start_y = game_state.player_exit_pos
        self.player = Player(start_x, start_y)
        
        # Campfire position
        self.campfire_pos = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.campfire_radius = 40
        
        # Load campfire sprite
        campfire_path = os.path.join(SPRITES_DIR, 'objects', 'campfire.png')
        try:
            self.campfire_sheet = pygame.image.load(campfire_path).convert_alpha()
            self.campfire_frames = []
            for i in range(4):
                frame = pygame.Surface((32, 32), pygame.SRCALPHA)
                frame.blit(self.campfire_sheet, (0, 0), (i * 32, 0, 32, 32))
                self.campfire_frames.append(frame)
        except pygame.error:
            self.campfire_frames = [pygame.Surface((32, 32), pygame.SRCALPHA)]
            pygame.draw.circle(self.campfire_frames[0], (255, 100, 0), (16, 16), 12)
        
        self.campfire_frame = 0
        self.campfire_timer = 0.0
        
        # UI state
        self.near_campfire = False
        self.show_save_prompt = False
        self.show_saved_message = False
        self.saved_message_timer = 0.0
        
        # Exit to world
        self.exit_to_world = pygame.Rect(SCREEN_WIDTH - 20, 100, 20, 100)
        
        # Font
        self.font = pygame.font.Font(None, 24)
        self.prompt_font = pygame.font.Font(None, 28)
    
    def _create_background(self) -> pygame.Surface:
        """Create the camp background with wooden floor."""
        bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Dark outer area
        bg_surface.fill((35, 30, 28))
        
        # Try to load wooden floor tile
        floor_path = os.path.join(SPRITES_DIR, 'tilesets', 'wooden.png')
        try:
            floor_tile = pygame.image.load(floor_path).convert()
            tile_size = floor_tile.get_width()
            
            # Tile the floor in the center area
            floor_rect = pygame.Rect(40, 40, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80)
            for y in range(floor_rect.top, floor_rect.bottom, tile_size):
                for x in range(floor_rect.left, floor_rect.right, tile_size):
                    bg_surface.blit(floor_tile, (x, y))
        except pygame.error as e:
            print(f"Warning: Could not load floor tile: {e}")
            # Fallback to solid color
            pygame.draw.rect(bg_surface, (60, 50, 45), (40, 40, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80))
        
        return bg_surface
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.player.handle_attack_input(event.key)
            
            if event.key == pygame.K_ESCAPE:
                self.next_scene = 'menu'
            
            # Save game when near campfire
            if event.key == pygame.K_y and self.near_campfire:
                if game_state.save_game():
                    self.show_saved_message = True
                    self.saved_message_timer = 2.0
                    # Heal player on save
                    self.player.health = self.player.max_health
    
    def update(self, dt: float):
        # Get input
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        # Update player
        self.player.update(dt)
        
        # Clamp player to screen
        self.player.pos.x = max(24, min(SCREEN_WIDTH - 24, self.player.pos.x))
        self.player.pos.y = max(24, min(SCREEN_HEIGHT - 24, self.player.pos.y))
        
        # Update campfire animation
        self.campfire_timer += dt
        if self.campfire_timer >= 0.2:
            self.campfire_timer = 0.0
            self.campfire_frame = (self.campfire_frame + 1) % len(self.campfire_frames)
        
        # Check if near campfire
        distance = self.player.pos.distance_to(self.campfire_pos)
        self.near_campfire = distance <= self.campfire_radius
        
        # Update saved message timer
        if self.show_saved_message:
            self.saved_message_timer -= dt
            if self.saved_message_timer <= 0:
                self.show_saved_message = False
        
        # Check scene transitions
        player_rect = self.player.get_collision_rect()
        if player_rect.colliderect(self.exit_to_world):
            game_state.player_start_pos = (50, self.player.pos.y)
            self.next_scene = 'world'
    
    def draw(self, screen: pygame.Surface):
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Draw exit area
        pygame.draw.rect(screen, (100, 150, 255), self.exit_to_world, 2)
        exit_font = pygame.font.Font(None, 18)
        exit_text = exit_font.render("World", True, (150, 200, 255))
        screen.blit(exit_text, (SCREEN_WIDTH - 18, self.exit_to_world.centery - 8))
        
        # Draw campfire glow (behind campfire)
        glow_surface = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (255, 150, 50, 40), (60, 60), 60)
        screen.blit(glow_surface, (self.campfire_pos.x - 60, self.campfire_pos.y - 60))
        
        # Draw campfire
        campfire_rect = self.campfire_frames[self.campfire_frame].get_rect()
        campfire_rect.center = (int(self.campfire_pos.x), int(self.campfire_pos.y))
        screen.blit(self.campfire_frames[self.campfire_frame], campfire_rect)
        
        # Draw player
        screen.blit(self.player.image, self.player.rect)
        
        # Draw health bar
        health_ratio = self.player.health / self.player.max_health
        bar_x, bar_y = self.player.pos.x - 25, self.player.pos.y - 35
        pygame.draw.rect(screen, (80, 20, 20), (bar_x, bar_y, 50, 5))
        pygame.draw.rect(screen, (50, 180, 50), (bar_x, bar_y, 50 * health_ratio, 5))
        pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, 50, 5), 1)
        
        # UI
        self._draw_ui(screen)
    
    def _draw_ui(self, screen):
        # Scene label
        scene_text = self.font.render("CAMP", True, (255, 200, 100))
        screen.blit(scene_text, (SCREEN_WIDTH - 60, 10))
        
        # Stats
        stats_text = self.font.render(
            f"HP: {self.player.health}/{self.player.max_health} | EXP: {game_state.player_exp} | Shrooms: {game_state.shroom_chunks}",
            True, (255, 255, 255)
        )
        screen.blit(stats_text, (10, 10))
        
        # Save prompt
        if self.near_campfire:
            prompt_text = self.prompt_font.render("Press Y to Save Game", True, (255, 255, 100))
            prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
            screen.blit(prompt_text, prompt_rect)
        
        # Saved message
        if self.show_saved_message:
            saved_text = self.prompt_font.render("Game Saved!", True, (100, 255, 100))
            saved_rect = saved_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
            screen.blit(saved_text, saved_rect)
        
        # Controls
        controls = self.font.render("WASD: Move | ESC: Menu", True, (180, 180, 180))
        screen.blit(controls, (10, SCREEN_HEIGHT - 25))
