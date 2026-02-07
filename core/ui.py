"""UI components for the game."""
import pygame
import os
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, SPRITES_DIR, FONTS_DIR


class HealthBar:
    """Visual health bar component."""
    
    def __init__(self, x: float, y: float, width: int = 50, height: int = 6):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        self.bg_color = (60, 0, 0)
        self.fill_color = (0, 180, 0)
        self.border_color = (30, 30, 30)
    
    def draw(self, screen: pygame.Surface, current: int, maximum: int):
        """Draw the health bar."""
        ratio = max(0, min(1, current / maximum))
        
        # Background
        pygame.draw.rect(screen, self.bg_color, 
                        (self.x, self.y, self.width, self.height))
        # Fill
        if ratio > 0:
            pygame.draw.rect(screen, self.fill_color, 
                            (self.x, self.y, self.width * ratio, self.height))
        # Border
        pygame.draw.rect(screen, self.border_color, 
                        (self.x, self.y, self.width, self.height), 1)
    
    def set_position(self, x: float, y: float):
        """Update position (for following entities)."""
        self.x = x - self.width / 2
        self.y = y


class Panel:
    """UI Panel for dialogs and messages."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = False
        
        # Colors
        self.bg_color = (40, 35, 45)
        self.border_color = (100, 90, 80)
        self.text_color = (220, 220, 200)
        
        # Font
        try:
            font_path = os.path.join(FONTS_DIR, 'Comicoro.ttf')
            self.font = pygame.font.Font(font_path, 24)
            self.small_font = pygame.font.Font(font_path, 18)
        except:
            self.font = pygame.font.Font(None, 28)
            self.small_font = pygame.font.Font(None, 22)
        
        # Content
        self.title = ""
        self.message = ""
        self.options: list[str] = []
    
    def show(self, title: str = "", message: str = "", options: list[str] | None = None):
        """Show the panel with content."""
        self.visible = True
        self.title = title
        self.message = message
        self.options = options or []
    
    def hide(self):
        """Hide the panel."""
        self.visible = False
    
    def draw(self, screen: pygame.Surface):
        """Draw the panel."""
        if not self.visible:
            return
        
        # Draw background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 3)
        
        # Draw title
        if self.title:
            title_surf = self.font.render(self.title, True, self.text_color)
            title_rect = title_surf.get_rect(centerx=self.rect.centerx, top=self.rect.top + 15)
            screen.blit(title_surf, title_rect)
        
        # Draw message
        if self.message:
            msg_surf = self.small_font.render(self.message, True, self.text_color)
            msg_rect = msg_surf.get_rect(centerx=self.rect.centerx, top=self.rect.top + 50)
            screen.blit(msg_surf, msg_rect)
        
        # Draw options
        if self.options:
            option_y = self.rect.bottom - 40
            for i, option in enumerate(self.options):
                opt_surf = self.small_font.render(option, True, (180, 180, 100))
                opt_rect = opt_surf.get_rect(centerx=self.rect.centerx, top=option_y - len(self.options) * 20 + i * 25)
                screen.blit(opt_surf, opt_rect)


class DeathPanel(Panel):
    """Panel shown when player dies."""
    
    def __init__(self):
        width, height = 300, 150
        x = (SCREEN_WIDTH - width) // 2
        y = (SCREEN_HEIGHT - height) // 2
        super().__init__(x, y, width, height)
    
    def show_death(self, has_save: bool = False):
        """Show death dialog."""
        if has_save:
            options = ["[Y] Load Last Save", "[N] Quit to Menu"]
        else:
            options = ["[N] Quit to Menu"]
        
        self.show(
            title="You Died",
            message="Your spirit lingers...",
            options=options
        )


class HUD:
    """Heads-up display with player stats."""
    
    def __init__(self):
        try:
            font_path = os.path.join(FONTS_DIR, 'Comicoro.ttf')
            self.font = pygame.font.Font(font_path, 20)
        except:
            self.font = pygame.font.Font(None, 24)
        
        self.text_color = (230, 230, 220)
        self.shadow_color = (30, 30, 30)
        
        # Health bar in top left
        self.health_bar = HealthBar(10, 10, 150, 16)
        self.health_bar.fill_color = (180, 40, 40)
        self.health_bar.bg_color = (60, 20, 20)
    
    def draw(self, screen: pygame.Surface, player, game_state):
        """Draw the HUD."""
        # Health bar
        self.health_bar.draw(screen, player.health, player.max_health)
        
        # HP text on bar
        hp_text = self.font.render(f"{player.health}/{player.max_health}", True, self.text_color)
        screen.blit(hp_text, (15, 8))
        
        # Stats below health bar
        y = 32
        
        # EXP
        exp_text = self.font.render(f"EXP: {game_state.player_exp}", True, self.text_color)
        screen.blit(exp_text, (10, y))
        
        # Level
        level_text = self.font.render(f"LVL: {game_state.player_level}", True, self.text_color)
        screen.blit(level_text, (100, y))
        
        # Shrooms (if any)
        if game_state.shroom_chunks > 0:
            shroom_text = self.font.render(f"Shrooms: {game_state.shroom_chunks}", True, (150, 200, 150))
            screen.blit(shroom_text, (10, y + 20))
    
    def draw_text_with_shadow(self, screen, text, pos, color=None):
        """Draw text with a shadow effect."""
        if color is None:
            color = self.text_color
        
        # Shadow
        shadow_surf = self.font.render(text, True, self.shadow_color)
        screen.blit(shadow_surf, (pos[0] + 1, pos[1] + 1))
        
        # Text
        text_surf = self.font.render(text, True, color)
        screen.blit(text_surf, pos)
