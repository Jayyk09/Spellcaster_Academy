"""Main menu scene."""
import pygame
import os
from core.scene import Scene
from core.game_state import game_state
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, SPRITES_DIR, FONTS_DIR


class MainMenuScene(Scene):
    """Main menu with New Game, Load Game, and Quit options."""
    
    def __init__(self, game, **kwargs):
        super().__init__(game)
        
        # Load background
        bg_path = os.path.join(SPRITES_DIR, 'ui', 'background.png')
        try:
            self.background = pygame.image.load(bg_path).convert()
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error as e:
            print(f"Warning: Could not load background: {e}")
            self.background = None
        except Exception as e:
            print(f"Warning: Unexpected error loading background: {e}")
            self.background = None
        
        # Load font
        font_path = os.path.join(FONTS_DIR, 'Alkhemikal.ttf')
        try:
            self.title_font = pygame.font.Font(font_path, 48)
            self.menu_font = pygame.font.Font(font_path, 32)
        except:
            self.title_font = pygame.font.Font(None, 48)
            self.menu_font = pygame.font.Font(None, 32)
        
        # Menu options
        self.menu_items = ['New Game', 'Load Game', 'Quit']
        self.selected_index = 0
        
        # Check for save game
        game_state.check_savegame_exists()
        
        # Colors
        self.color_normal = (200, 200, 200)
        self.color_selected = (255, 255, 100)
        self.color_disabled = (100, 100, 100)
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._select_option()
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False
    
    def _select_option(self):
        option = self.menu_items[self.selected_index]
        
        if option == 'New Game':
            game_state.reset()
            self.next_scene = 'world'
        elif option == 'Load Game':
            if game_state.check_savegame_exists():
                game_state.load_game()
                self.next_scene = 'world'
        elif option == 'Quit':
            self.game.running = False
    
    def update(self, dt: float):
        pass
    
    def draw(self, screen: pygame.Surface):
        # Draw background
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((30, 30, 50))
        
        # Draw title
        title_text = self.title_font.render("Die Insel", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_text, title_rect)
        
        # Draw menu items
        start_y = 200
        for i, item in enumerate(self.menu_items):
            # Determine color
            if i == self.selected_index:
                color = self.color_selected
            elif item == 'Load Game' and not game_state.game_has_savegame:
                color = self.color_disabled
            else:
                color = self.color_normal
            
            # Add indicator for selected
            display_text = f"> {item} <" if i == self.selected_index else item
            
            text = self.menu_font.render(display_text, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 50))
            screen.blit(text, text_rect)
        
        # Draw controls hint
        hint_font = pygame.font.Font(None, 20)
        hint_text = hint_font.render("Arrow Keys to Select, Enter to Confirm", True, (150, 150, 150))
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        screen.blit(hint_text, hint_rect)
