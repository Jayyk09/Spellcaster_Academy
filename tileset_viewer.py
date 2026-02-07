#!/usr/bin/env python3
"""
Tileset Viewer - Interactive tool for viewing and inspecting tilesets.

Usage:
    python tileset_viewer.py                    # List available tilesets
    python tileset_viewer.py <tileset>          # View tileset with default 16px tiles
    python tileset_viewer.py <tileset> --size 8 # View tileset with 8px tiles
    python tileset_viewer.py plains.png         # View specific tileset file
    python tileset_viewer.py --list             # List all available tilesets

Controls:
    Arrow Keys / WASD  - Pan the view
    +/- or Scroll      - Zoom in/out
    R                  - Reset view
    G                  - Toggle grid
    C                  - Toggle coordinates
    Q / ESC            - Quit
    Click              - Show tile info (col, row)
"""

import argparse
import os
import sys
import pygame

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import TILESETS_DIR


def get_available_tilesets():
    """Get list of available tileset files."""
    tilesets = []
    for root, dirs, files in os.walk(TILESETS_DIR):
        for file in files:
            if file.endswith('.png'):
                rel_path = os.path.relpath(os.path.join(root, file), TILESETS_DIR)
                tilesets.append(rel_path)
    return sorted(tilesets)


def list_tilesets():
    """Print available tilesets."""
    print("\nAvailable tilesets:")
    print("-" * 40)
    for ts in get_available_tilesets():
        print(f"  {ts}")
    print("-" * 40)
    print(f"\nUsage: python tileset_viewer.py <tileset_name>")
    print(f"Example: python tileset_viewer.py plains.png")


class TilesetViewer:
    """Interactive tileset viewer with pan, zoom, and tile inspection."""
    
    def __init__(self, tileset_path: str, tile_size: int = 16):
        self.tile_size = tile_size
        self.tileset_path = tileset_path
        
        # Display settings
        self.window_width = 800
        self.window_height = 600
        self.bg_color = (40, 40, 40)
        self.grid_color = (100, 100, 100)
        self.highlight_color = (255, 255, 0)
        self.text_color = (255, 255, 255)
        self.coord_color = (200, 200, 200)
        
        # View state
        self.offset_x = 50
        self.offset_y = 80
        self.zoom = 2.0
        self.show_grid = True
        self.show_coords = True
        self.selected_tile = None  # (col, row)
        self.hovered_tile = None   # (col, row)
        
        # Pan state
        self.panning = False
        self.pan_start = (0, 0)
        self.pan_offset_start = (0, 0)
        
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.window_width, self.window_height),
            pygame.RESIZABLE
        )
        pygame.display.set_caption(f"Tileset Viewer - {os.path.basename(tileset_path)}")
        
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        self.load_tileset()
        self.clock = pygame.time.Clock()
    
    def load_tileset(self):
        """Load the tileset image."""
        try:
            self.tileset = pygame.image.load(self.tileset_path).convert_alpha()
            self.tileset_width = self.tileset.get_width()
            self.tileset_height = self.tileset.get_height()
            self.cols = self.tileset_width // self.tile_size
            self.rows = self.tileset_height // self.tile_size
            print(f"Loaded: {self.tileset_path}")
            print(f"Size: {self.tileset_width}x{self.tileset_height}px")
            print(f"Grid: {self.cols} cols x {self.rows} rows ({self.tile_size}px tiles)")
        except pygame.error as e:
            print(f"Error loading tileset: {e}")
            sys.exit(1)
    
    def screen_to_tile(self, screen_x: int, screen_y: int):
        """Convert screen coordinates to tile coordinates."""
        # Account for zoom and offset
        world_x = (screen_x - self.offset_x) / self.zoom
        world_y = (screen_y - self.offset_y) / self.zoom
        
        col = int(world_x // self.tile_size)
        row = int(world_y // self.tile_size)
        
        # Check bounds
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return (col, row)
        return None
    
    def tile_to_screen(self, col: int, row: int):
        """Convert tile coordinates to screen coordinates."""
        screen_x = self.offset_x + col * self.tile_size * self.zoom
        screen_y = self.offset_y + row * self.tile_size * self.zoom
        return (screen_x, screen_y)
    
    def handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    return False
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                elif event.key == pygame.K_c:
                    self.show_coords = not self.show_coords
                elif event.key == pygame.K_r:
                    self.reset_view()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    self.zoom_at_center(1.2)
                elif event.key == pygame.K_MINUS:
                    self.zoom_at_center(0.8)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    tile = self.screen_to_tile(*event.pos)
                    if tile:
                        self.selected_tile = tile
                        col, row = tile
                        print(f"Selected: col={col}, row={row} -> [\"tileset\", {col}, {row}]")
                elif event.button == 2:  # Middle click - start pan
                    self.panning = True
                    self.pan_start = event.pos
                    self.pan_offset_start = (self.offset_x, self.offset_y)
                elif event.button == 4:  # Scroll up - zoom in
                    self.zoom_at_mouse(1.1, event.pos)
                elif event.button == 5:  # Scroll down - zoom out
                    self.zoom_at_mouse(0.9, event.pos)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    self.panning = False
            
            elif event.type == pygame.MOUSEMOTION:
                self.hovered_tile = self.screen_to_tile(*event.pos)
                if self.panning:
                    dx = event.pos[0] - self.pan_start[0]
                    dy = event.pos[1] - self.pan_start[1]
                    self.offset_x = self.pan_offset_start[0] + dx
                    self.offset_y = self.pan_offset_start[1] + dy
            
            elif event.type == pygame.VIDEORESIZE:
                self.window_width = event.w
                self.window_height = event.h
                self.screen = pygame.display.set_mode(
                    (self.window_width, self.window_height),
                    pygame.RESIZABLE
                )
        
        # Handle held keys for panning
        keys = pygame.key.get_pressed()
        pan_speed = 10
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.offset_x += pan_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.offset_x -= pan_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.offset_y += pan_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.offset_y -= pan_speed
        
        return True
    
    def zoom_at_mouse(self, factor: float, mouse_pos: tuple):
        """Zoom centered on mouse position."""
        old_zoom = self.zoom
        self.zoom = max(0.5, min(10.0, self.zoom * factor))
        
        # Adjust offset to keep mouse position fixed
        mx, my = mouse_pos
        self.offset_x = mx - (mx - self.offset_x) * (self.zoom / old_zoom)
        self.offset_y = my - (my - self.offset_y) * (self.zoom / old_zoom)
    
    def zoom_at_center(self, factor: float):
        """Zoom centered on screen center."""
        center = (self.window_width // 2, self.window_height // 2)
        self.zoom_at_mouse(factor, center)
    
    def reset_view(self):
        """Reset view to default."""
        self.offset_x = 50
        self.offset_y = 80
        self.zoom = 2.0
    
    def draw(self):
        """Draw the viewer."""
        self.screen.fill(self.bg_color)
        
        # Draw checkerboard background for transparency
        self.draw_checkerboard()
        
        # Draw scaled tileset
        scaled_width = int(self.tileset_width * self.zoom)
        scaled_height = int(self.tileset_height * self.zoom)
        scaled_tileset = pygame.transform.scale(self.tileset, (scaled_width, scaled_height))
        self.screen.blit(scaled_tileset, (self.offset_x, self.offset_y))
        
        # Draw grid
        if self.show_grid:
            self.draw_grid()
        
        # Draw coordinates
        if self.show_coords:
            self.draw_coordinates()
        
        # Highlight hovered tile
        if self.hovered_tile:
            self.draw_tile_highlight(self.hovered_tile, (100, 100, 255, 100))
        
        # Highlight selected tile
        if self.selected_tile:
            self.draw_tile_highlight(self.selected_tile, (255, 255, 0, 150))
        
        # Draw info panel
        self.draw_info_panel()
        
        pygame.display.flip()
    
    def draw_checkerboard(self):
        """Draw checkerboard pattern behind tileset."""
        check_size = int(8 * self.zoom)
        if check_size < 2:
            check_size = 2
        
        start_x = max(0, int(self.offset_x))
        start_y = max(0, int(self.offset_y))
        end_x = min(self.window_width, int(self.offset_x + self.tileset_width * self.zoom))
        end_y = min(self.window_height, int(self.offset_y + self.tileset_height * self.zoom))
        
        for y in range(start_y, end_y, check_size):
            for x in range(start_x, end_x, check_size):
                tile_x = (x - int(self.offset_x)) // check_size
                tile_y = (y - int(self.offset_y)) // check_size
                if (tile_x + tile_y) % 2 == 0:
                    color = (60, 60, 60)
                else:
                    color = (50, 50, 50)
                rect = pygame.Rect(x, y, check_size, check_size)
                rect = rect.clip(pygame.Rect(start_x, start_y, end_x - start_x, end_y - start_y))
                pygame.draw.rect(self.screen, color, rect)
    
    def draw_grid(self):
        """Draw tile grid overlay."""
        scaled_tile = self.tile_size * self.zoom
        
        # Vertical lines
        for col in range(self.cols + 1):
            x = self.offset_x + col * scaled_tile
            if 0 <= x <= self.window_width:
                pygame.draw.line(
                    self.screen, self.grid_color,
                    (x, self.offset_y),
                    (x, self.offset_y + self.tileset_height * self.zoom)
                )
        
        # Horizontal lines
        for row in range(self.rows + 1):
            y = self.offset_y + row * scaled_tile
            if 0 <= y <= self.window_height:
                pygame.draw.line(
                    self.screen, self.grid_color,
                    (self.offset_x, y),
                    (self.offset_x + self.tileset_width * self.zoom, y)
                )
    
    def draw_coordinates(self):
        """Draw column and row numbers."""
        scaled_tile = self.tile_size * self.zoom
        
        # Only draw if tiles are big enough
        if scaled_tile < 20:
            return
        
        # Column numbers (top)
        for col in range(self.cols):
            x = self.offset_x + col * scaled_tile + scaled_tile // 2
            y = self.offset_y - 15
            if 0 <= x <= self.window_width and y > 0:
                text = self.small_font.render(str(col), True, self.coord_color)
                text_rect = text.get_rect(center=(x, y))
                self.screen.blit(text, text_rect)
        
        # Row numbers (left)
        for row in range(self.rows):
            x = self.offset_x - 20
            y = self.offset_y + row * scaled_tile + scaled_tile // 2
            if x > 0 and 0 <= y <= self.window_height:
                text = self.small_font.render(str(row), True, self.coord_color)
                text_rect = text.get_rect(center=(x, y))
                self.screen.blit(text, text_rect)
    
    def draw_tile_highlight(self, tile: tuple, color: tuple):
        """Draw highlight around a tile."""
        col, row = tile
        x, y = self.tile_to_screen(col, row)
        scaled_tile = self.tile_size * self.zoom
        
        # Draw filled rect with alpha
        s = pygame.Surface((scaled_tile, scaled_tile), pygame.SRCALPHA)
        s.fill(color)
        self.screen.blit(s, (x, y))
        
        # Draw border
        border_color = (color[0], color[1], color[2])
        pygame.draw.rect(self.screen, border_color, (x, y, scaled_tile, scaled_tile), 2)
    
    def draw_info_panel(self):
        """Draw information panel at the top."""
        # Background
        panel_height = 60
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, self.window_width, panel_height))
        pygame.draw.line(self.screen, (60, 60, 60), (0, panel_height), (self.window_width, panel_height))
        
        # Title
        title = f"{os.path.basename(self.tileset_path)} - {self.cols}x{self.rows} tiles ({self.tile_size}px)"
        title_text = self.font.render(title, True, self.text_color)
        self.screen.blit(title_text, (10, 8))
        
        # Controls hint
        controls = "G:Grid  C:Coords  R:Reset  +/-:Zoom  Arrows:Pan  Click:Select  Q:Quit"
        controls_text = self.small_font.render(controls, True, (150, 150, 150))
        self.screen.blit(controls_text, (10, 35))
        
        # Zoom level
        zoom_text = self.small_font.render(f"Zoom: {self.zoom:.1f}x", True, self.coord_color)
        self.screen.blit(zoom_text, (self.window_width - 80, 8))
        
        # Selected/Hovered tile info
        tile_info = None
        if self.selected_tile:
            col, row = self.selected_tile
            tile_info = f"Selected: [{col}, {row}]"
        elif self.hovered_tile:
            col, row = self.hovered_tile
            tile_info = f"Hover: [{col}, {row}]"
        
        if tile_info:
            info_text = self.font.render(tile_info, True, self.highlight_color)
            self.screen.blit(info_text, (self.window_width - 180, 35))
    
    def run(self):
        """Main loop."""
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(
        description="Interactive tileset viewer for pygame games.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Controls:
  Arrow Keys / WASD  - Pan the view
  +/- or Scroll      - Zoom in/out
  R                  - Reset view
  G                  - Toggle grid
  C                  - Toggle coordinates
  Click              - Show tile info
  Q / ESC            - Quit

Examples:
  python tileset_viewer.py                    # List available tilesets
  python tileset_viewer.py plains.png         # View plains tileset
  python tileset_viewer.py objects.png -s 16  # View with 16px tile size
  python tileset_viewer.py floors/flooring.png
        """
    )
    
    parser.add_argument(
        'tileset',
        nargs='?',
        help='Tileset filename (e.g., plains.png, floors/flooring.png)'
    )
    parser.add_argument(
        '-s', '--size',
        type=int,
        default=16,
        help='Tile size in pixels (default: 16)'
    )
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List available tilesets'
    )
    
    args = parser.parse_args()
    
    # List mode
    if args.list or args.tileset is None:
        list_tilesets()
        return
    
    # Find tileset path
    tileset_path = None
    
    # Check if it's a full path
    if os.path.isfile(args.tileset):
        tileset_path = args.tileset
    else:
        # Check in tilesets directory
        candidate = os.path.join(TILESETS_DIR, args.tileset)
        if os.path.isfile(candidate):
            tileset_path = candidate
        else:
            # Try adding .png extension
            candidate = os.path.join(TILESETS_DIR, args.tileset + '.png')
            if os.path.isfile(candidate):
                tileset_path = candidate
    
    if tileset_path is None:
        print(f"Error: Tileset '{args.tileset}' not found.")
        list_tilesets()
        sys.exit(1)
    
    # Run viewer
    viewer = TilesetViewer(tileset_path, args.size)
    viewer.run()


if __name__ == '__main__':
    main()
