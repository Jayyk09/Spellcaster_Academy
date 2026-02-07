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


class CameraLetterDisplay:
    """
    UI component to show camera-detected letter and hold progress.
    
    Displays:
    - Currently detected letter
    - Hold progress bar (filling up as letter is held)
    - "No Target" feedback when letter doesn't match any enemy
    """
    
    def __init__(self):
        # Position (bottom-center of screen)
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 80
        
        # Dimensions
        self.letter_size = 48
        self.progress_bar_width = 80
        self.progress_bar_height = 8
        
        # Colors
        self.bg_color = (30, 30, 40, 200)
        self.letter_color = (255, 255, 255)
        self.letter_holding_color = (255, 220, 100)
        self.letter_confirmed_color = (100, 255, 100)
        self.progress_bg_color = (60, 60, 70)
        self.progress_fill_color = (100, 200, 255)
        self.no_target_color = (255, 100, 100)
        
        # Fonts
        try:
            font_path = os.path.join(FONTS_DIR, 'Alkhemikal.ttf')
            self.letter_font = pygame.font.Font(font_path, self.letter_size)
            self.label_font = pygame.font.Font(font_path, 16)
        except:
            self.letter_font = pygame.font.Font(None, self.letter_size)
            self.label_font = pygame.font.Font(None, 18)
    
    def draw(self, screen: pygame.Surface, detected_letter: str | None, 
             hold_progress: float, state: str, 
             no_target_letter: str | None = None, show_no_target: bool = False):
        """
        Draw the camera letter display.
        
        Args:
            screen: Surface to draw on
            detected_letter: Currently detected letter (or None)
            hold_progress: 0.0 to 1.0 progress of hold time
            state: Current state ('waiting', 'holding', 'debouncing')
            no_target_letter: Letter that had no matching target
            show_no_target: Whether to show "No Target" feedback
        """
        # Don't draw anything if no letter and no feedback needed
        if detected_letter is None and not show_no_target:
            return
        
        # Background panel
        panel_width = 120
        panel_height = 90
        panel_rect = pygame.Rect(
            self.x - panel_width // 2,
            self.y - panel_height // 2,
            panel_width,
            panel_height
        )
        
        # Draw semi-transparent background
        bg_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        bg_surface.fill(self.bg_color)
        screen.blit(bg_surface, panel_rect.topleft)
        
        # Draw border
        pygame.draw.rect(screen, (80, 80, 100), panel_rect, 2)
        
        # Determine letter color based on state
        if state == 'debouncing':
            letter_color = self.letter_confirmed_color
        elif state == 'holding':
            letter_color = self.letter_holding_color
        else:
            letter_color = self.letter_color
        
        # Draw letter
        display_letter = detected_letter if detected_letter else "?"
        letter_surf = self.letter_font.render(display_letter, True, letter_color)
        letter_rect = letter_surf.get_rect(centerx=self.x, centery=self.y - 15)
        screen.blit(letter_surf, letter_rect)
        
        # Draw progress bar (only when holding)
        if state == 'holding' and hold_progress > 0:
            bar_x = self.x - self.progress_bar_width // 2
            bar_y = self.y + 15
            
            # Background
            pygame.draw.rect(screen, self.progress_bg_color,
                           (bar_x, bar_y, self.progress_bar_width, self.progress_bar_height))
            
            # Fill
            fill_width = int(self.progress_bar_width * hold_progress)
            if fill_width > 0:
                pygame.draw.rect(screen, self.progress_fill_color,
                               (bar_x, bar_y, fill_width, self.progress_bar_height))
            
            # Border
            pygame.draw.rect(screen, (100, 100, 120),
                           (bar_x, bar_y, self.progress_bar_width, self.progress_bar_height), 1)
        
        # Draw "No Target" feedback
        if show_no_target and no_target_letter:
            no_target_text = f"No target for '{no_target_letter}'"
            no_target_surf = self.label_font.render(no_target_text, True, self.no_target_color)
            no_target_rect = no_target_surf.get_rect(centerx=self.x, top=self.y + 30)
            screen.blit(no_target_surf, no_target_rect)
        
        # Draw state label
        if state == 'debouncing':
            label = "Release hand..."
            label_color = self.letter_confirmed_color
        elif state == 'holding':
            label = "Hold..."
            label_color = self.letter_holding_color
        elif detected_letter:
            label = "Detected"
            label_color = (150, 150, 150)
        else:
            label = ""
            label_color = (150, 150, 150)
        
        if label and not show_no_target:
            label_surf = self.label_font.render(label, True, label_color)
            label_rect = label_surf.get_rect(centerx=self.x, top=self.y + 30)
            screen.blit(label_surf, label_rect)
