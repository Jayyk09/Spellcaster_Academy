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
    
    def show_death(self):
        """Show death dialog."""
        
        self.show(
            title="You Died",
            message="Your spirit lingers...",
            options=["[N] Quit to Menu"]
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


class ASLPopup:
    """
    Popup that displays ASL sign examples for letters before waves start.
    
    Loads the ASL spritesheet and displays individual letter signs
    alongside their letter names. Requires user to click "Ready" to continue.
    """
    
    def __init__(self):
        self.visible = False
        self.letters = []
        self.ready = False
        
        # Colors
        self.bg_color = (30, 30, 40, 230)
        self.border_color = (100, 90, 80)
        self.title_color = (255, 255, 255)
        self.letter_color = (255, 255, 255)
        self.button_color = (80, 120, 80)
        self.button_hover_color = (100, 150, 100)
        self.button_text_color = (255, 255, 255)
        
        # Panel dimensions
        self.panel_width = 700
        self.panel_height = 400
        self.panel_rect = pygame.Rect(
            (SCREEN_WIDTH - self.panel_width) // 2,
            (SCREEN_HEIGHT - self.panel_height) // 2,
            self.panel_width,
            self.panel_height
        )
        
        # Fonts - use same font as enemy letters (Alkhemikal.ttf size 24)
        try:
            font_path = os.path.join(FONTS_DIR, 'Alkhemikal.ttf')
            self.title_font = pygame.font.Font(font_path, 36)
            self.letter_font = pygame.font.Font(font_path, 24)  # Match enemy letter font
            self.button_font = pygame.font.Font(font_path, 28)
        except:
            self.title_font = pygame.font.Font(None, 40)
            self.letter_font = pygame.font.Font(None, 24)
            self.button_font = pygame.font.Font(None, 32)
        
        # Load ASL sprites
        self._load_asl_sprites()
        
        # Ready button
        self.button_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 80,
            self.panel_rect.bottom - 70,
            160,
            50
        )
        self.button_hover = False
    
    def _load_asl_sprites(self):
        """Load and split the ASL spritesheet into individual letter images."""
        self.asl_sprites = {}
        
        try:
            sprite_path = os.path.join(SPRITES_DIR, 'ui', 'asl-sprites.png')
            spritesheet = pygame.image.load(sprite_path).convert_alpha()
            sheet_width, sheet_height = spritesheet.get_size()
            
            # Sprite sheet has A-F (6 letters) evenly divided
            letters = ['A', 'B', 'C', 'D', 'E', 'F']
            sprite_width = sheet_width // len(letters)
            
            for i, letter in enumerate(letters):
                # Extract sprite for this letter
                x = i * sprite_width
                sprite = spritesheet.subsurface(pygame.Rect(x, 0, sprite_width, sheet_height))
                
                # Scale up for better visibility
                scaled_width = sprite_width * 2
                scaled_height = sheet_height * 2
                self.asl_sprites[letter] = pygame.transform.scale(sprite, (scaled_width, scaled_height))
                
        except Exception as e:
            print(f"Warning: Could not load ASL sprites: {e}")
            # Create placeholder sprites
            for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
                placeholder = pygame.Surface((100, 100), pygame.SRCALPHA)
                pygame.draw.rect(placeholder, (100, 100, 100), (0, 0, 100, 100), 2)
                text = self.letter_font.render(letter, True, (200, 200, 200))
                text_rect = text.get_rect(center=(50, 50))
                placeholder.blit(text, text_rect)
                self.asl_sprites[letter] = placeholder
    
    def show(self, letters: list[str], subtitle: str = ""):
        """Show the popup with the specified letters and optional subtitle."""
        self.visible = True
        self.letters = [l.upper() for l in letters if l.upper() in self.asl_sprites]
        self.subtitle = subtitle
        self.ready = False
    
    def hide(self):
        """Hide the popup."""
        self.visible = False
        self.ready = False
    
    def is_visible(self) -> bool:
        """Check if the popup is currently visible."""
        return self.visible
    
    def is_ready(self) -> bool:
        """Check if the user clicked ready."""
        return self.ready
    
    def handle_event(self, event):
        """Handle mouse events for the ready button."""
        if not self.visible:
            return
        
        if event.type == pygame.MOUSEMOTION:
            self.button_hover = self.button_rect.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.button_rect.collidepoint(event.pos):
                self.ready = True
                self.visible = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.ready = True
                self.visible = False
    
    def draw(self, screen: pygame.Surface):
        """Draw the popup with ASL examples."""
        if not self.visible:
            return
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Draw panel background
        bg_surface = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        bg_surface.fill(self.bg_color)
        screen.blit(bg_surface, self.panel_rect.topleft)
        
        # Draw border
        pygame.draw.rect(screen, self.border_color, self.panel_rect, 3)
        
        # Draw title
        title_text = self.title_font.render("Learn These Signs", True, self.title_color)
        title_rect = title_text.get_rect(centerx=SCREEN_WIDTH // 2, top=self.panel_rect.top + 20)
        screen.blit(title_text, title_rect)
        
        # Draw optional subtitle
        subtitle_offset = 0
        if hasattr(self, 'subtitle') and self.subtitle:
            sub_text = self.letter_font.render(self.subtitle, True, (200, 200, 100))
            sub_rect = sub_text.get_rect(centerx=SCREEN_WIDTH // 2, top=title_rect.bottom + 5)
            screen.blit(sub_text, sub_rect)
            subtitle_offset = sub_text.get_height() + 5
        
        # Draw ASL examples for each letter
        if self.letters:
            # Calculate layout
            num_letters = len(self.letters)
            sprite_width = 120  # Scaled sprite width
            sprite_height = 100  # Scaled sprite height
            spacing = 20
            
            total_width = num_letters * sprite_width + (num_letters - 1) * spacing
            start_x = SCREEN_WIDTH // 2 - total_width // 2 + sprite_width // 2
            start_y = self.panel_rect.top + 80 + subtitle_offset
            
            for i, letter in enumerate(self.letters):
                x = start_x + i * (sprite_width + spacing)
                
                # Draw letter label (white font)
                letter_text = self.letter_font.render(letter, True, self.letter_color)
                letter_rect = letter_text.get_rect(centerx=x, top=start_y)
                screen.blit(letter_text, letter_rect)
                
                # Draw ASL sprite below the letter
                if letter in self.asl_sprites:
                    sprite = self.asl_sprites[letter]
                    sprite_rect = sprite.get_rect(centerx=x, top=start_y + 40)
                    screen.blit(sprite, sprite_rect)
        
        # Draw Ready button
        button_color = self.button_hover_color if self.button_hover else self.button_color
        pygame.draw.rect(screen, button_color, self.button_rect, border_radius=8)
        pygame.draw.rect(screen, (200, 200, 200), self.button_rect, 2, border_radius=8)
        
        button_text = self.button_font.render("Ready!", True, self.button_text_color)
        button_text_rect = button_text.get_rect(center=self.button_rect.center)
        screen.blit(button_text, button_text_rect)


class WaveDisplay:
    """
    UI component to display current wave number and wave transition messages.
    
    Displays:
    - Current wave number at top center
    - "Wave Complete!" message during transition
    - Countdown timer for next wave
    """
    
    def __init__(self):
        # Position (top center of screen)
        self.x = SCREEN_WIDTH // 2
        self.y = 15
        
        # Colors
        self.wave_color = (255, 220, 100)
        self.complete_color = (100, 255, 100)
        self.countdown_color = (200, 200, 200)
        self.bg_color = (30, 30, 40, 180)
        
        # Fonts
        try:
            font_path = os.path.join(FONTS_DIR, 'Alkhemikal.ttf')
            self.wave_font = pygame.font.Font(font_path, 28)
            self.message_font = pygame.font.Font(font_path, 24)
            self.countdown_font = pygame.font.Font(font_path, 20)
        except:
            self.wave_font = pygame.font.Font(None, 32)
            self.message_font = pygame.font.Font(None, 28)
            self.countdown_font = pygame.font.Font(None, 24)
    
    def draw(self, screen: pygame.Surface, current_wave: int,
             wave_cleared: bool = False, countdown: float = 0.0):
        """
        Draw the wave display.

        Args:
            screen: Surface to draw on
            current_wave: Current wave number (1-indexed)
            wave_cleared: Whether to show "Wave Cleared!" notification
            countdown: Seconds remaining before barrier drops
        """
        # Draw wave number
        wave_text = f"Wave {current_wave}"
        wave_surf = self.wave_font.render(wave_text, True, self.wave_color)
        wave_rect = wave_surf.get_rect(centerx=self.x, top=self.y)

        # Background panel
        panel_width = wave_surf.get_width() + 30
        panel_height = wave_surf.get_height() + 10

        if wave_cleared:
            # Larger panel for cleared message + countdown below
            panel_height += 80
            panel_width = max(panel_width, 280)

        panel_rect = pygame.Rect(
            self.x - panel_width // 2,
            self.y - 5,
            panel_width,
            panel_height
        )

        # Draw semi-transparent background
        bg_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        bg_surface.fill(self.bg_color)
        screen.blit(bg_surface, panel_rect.topleft)

        # Draw border
        pygame.draw.rect(screen, (80, 80, 100), panel_rect, 2)

        # Draw wave number
        screen.blit(wave_surf, wave_rect)

        # Draw "Wave Cleared!" notification
        if wave_cleared:
            complete_surf = self.message_font.render("Wave Cleared!", True, self.complete_color)
            complete_rect = complete_surf.get_rect(centerx=self.x, top=wave_rect.bottom + 5)
            screen.blit(complete_surf, complete_rect)

            path_surf = self.countdown_font.render("Path ahead is open!", True, self.countdown_color)
            path_rect = path_surf.get_rect(centerx=self.x, top=complete_rect.bottom + 3)
            screen.blit(path_surf, path_rect)
            
            # Countdown
            countdown_int = int(countdown) + 1  # Show ceiling value (5, 4, 3, 2, 1)
            countdown_text = f"Next wave in {countdown_int}..."
            countdown_surf = self.countdown_font.render(countdown_text, True, self.countdown_color)
            countdown_rect = countdown_surf.get_rect(centerx=self.x, top=path_rect.bottom + 3)
            screen.blit(countdown_surf, countdown_rect)


class SignReferencePanel:
    """
    Floating panel that shows all active ASL letter signs when the player
    is near the Mage Guardian NPC. Auto-shows/hides based on proximity.
    """

    def __init__(self):
        self.visible = False
        self.letters: list[str] = []  # Current active letters to display
        self.labels: dict[str, str] = {}  # Optional label per letter (e.g. B -> "Block")

        # Colors
        self.bg_color = (25, 30, 50, 210)
        self.border_color = (120, 110, 90)
        self.title_color = (255, 255, 255)
        self.letter_color = (255, 255, 255)
        self.label_color = (200, 200, 100)

        # Fonts
        try:
            font_path = os.path.join(FONTS_DIR, 'Alkhemikal.ttf')
            self.title_font = pygame.font.Font(font_path, 30)
            self.letter_font = pygame.font.Font(font_path, 20)
        except Exception:
            self.title_font = pygame.font.Font(None, 34)
            self.letter_font = pygame.font.Font(None, 22)

        # Load ASL sprites (same sheet as ASLPopup)
        self.asl_sprites: dict[str, pygame.Surface] = {}
        self._load_asl_sprites()

    def _load_asl_sprites(self):
        """Load ASL letter sprites from the shared spritesheet."""
        try:
            sprite_path = os.path.join(SPRITES_DIR, 'ui', 'asl-sprites.png')
            spritesheet = pygame.image.load(sprite_path).convert_alpha()
            sheet_w, sheet_h = spritesheet.get_size()
            all_letters = ['A', 'B', 'C', 'D', 'E', 'F']
            sprite_w = sheet_w // len(all_letters)
            for i, letter in enumerate(all_letters):
                sub = spritesheet.subsurface(pygame.Rect(i * sprite_w, 0, sprite_w, sheet_h))
                scaled = pygame.transform.scale(sub, (sprite_w * 2, sheet_h * 2))
                self.asl_sprites[letter] = scaled
        except Exception as e:
            print(f"Warning: SignReferencePanel could not load ASL sprites: {e}")
            for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
                ph = pygame.Surface((100, 100), pygame.SRCALPHA)
                pygame.draw.rect(ph, (100, 100, 100), (0, 0, 100, 100), 2)
                txt = self.letter_font.render(letter, True, (200, 200, 200))
                ph.blit(txt, txt.get_rect(center=(50, 50)))
                self.asl_sprites[letter] = ph

    def set_letters(self, letters: list[str], labels: dict[str, str] | None = None):
        """Set which letters to display, with optional per-letter labels."""
        self.letters = [l.upper() for l in letters if l.upper() in self.asl_sprites]
        self.labels = labels or {}

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def draw(self, screen: pygame.Surface):
        if not self.visible or not self.letters:
            return

        num = len(self.letters)
        sprite_w = 100
        spacing = 16
        total_w = num * sprite_w + (num - 1) * spacing + 40  # 40 padding
        panel_h = 200
        panel_w = max(total_w, 260)

        # Position at top-center
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = 60

        # Background
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg.fill(self.bg_color)
        screen.blit(bg, (panel_x, panel_y))
        pygame.draw.rect(screen, self.border_color,
                         pygame.Rect(panel_x, panel_y, panel_w, panel_h), 3)

        # Title
        title = self.title_font.render("Sign Reference", True, self.title_color)
        screen.blit(title, title.get_rect(centerx=SCREEN_WIDTH // 2, top=panel_y + 10))

        # Letters row
        row_start_x = SCREEN_WIDTH // 2 - (num * (sprite_w + spacing) - spacing) // 2
        row_y = panel_y + 50

        for i, letter in enumerate(self.letters):
            cx = row_start_x + i * (sprite_w + spacing) + sprite_w // 2

            # Letter label
            lbl_text = letter
            if letter in self.labels:
                lbl_text = f"{letter} ({self.labels[letter]})"
            lbl = self.letter_font.render(lbl_text, True,
                                          self.label_color if letter in self.labels else self.letter_color)
            screen.blit(lbl, lbl.get_rect(centerx=cx, top=row_y))

            # Sprite
            if letter in self.asl_sprites:
                spr = self.asl_sprites[letter]
                # Scale down a bit to fit in panel
                thumb = pygame.transform.scale(spr, (80, 80))
                screen.blit(thumb, thumb.get_rect(centerx=cx, top=row_y + 25))
