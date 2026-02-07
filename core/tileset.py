"""TileSet class for loading and managing tileset images."""
import pygame
import os
from typing import Dict, List, Tuple, Optional
from config.settings import SPRITES_DIR


class TileSet:
    """
    Loads a tileset image and provides access to individual tiles.
    
    Tilesets are sprite sheets containing multiple tiles arranged in a grid.
    Each tile can be accessed by its atlas coordinates (column, row).
    """
    
    def __init__(self, filename: str, tile_size: int = 16):
        """
        Initialize a tileset from an image file.
        
        Args:
            filename: Name of the tileset image file (in assets/sprites/tilesets/)
            tile_size: Size of each tile in pixels (assumes square tiles)
        """
        self.tile_size = tile_size
        self.tiles: Dict[Tuple[int, int], pygame.Surface] = {}
        
        # Load the tileset image
        path = os.path.join(SPRITES_DIR, 'tilesets', filename)
        try:
            self.image = pygame.image.load(path).convert_alpha()
        except pygame.error as e:
            print(f"Warning: Could not load tileset {filename}: {e}")
            self.image = None
            self.cols = 0
            self.rows = 0
            return
        
        # Calculate grid dimensions
        self.cols = self.image.get_width() // tile_size
        self.rows = self.image.get_height() // tile_size
        
        # Extract all tiles
        self._extract_tiles()
    
    def _extract_tiles(self):
        """Extract individual tiles from the tileset image."""
        if self.image is None:
            return
        
        for row in range(self.rows):
            for col in range(self.cols):
                # Create a surface for this tile
                tile_surface = pygame.Surface(
                    (self.tile_size, self.tile_size),
                    pygame.SRCALPHA
                )
                
                # Blit the tile region from the tileset
                tile_surface.blit(
                    self.image,
                    (0, 0),
                    (col * self.tile_size, row * self.tile_size,
                     self.tile_size, self.tile_size)
                )
                
                self.tiles[(col, row)] = tile_surface
    
    def get_tile(self, col: int, row: int) -> Optional[pygame.Surface]:
        """
        Get a tile by its atlas coordinates.
        
        Args:
            col: Column index (0-based, left to right)
            row: Row index (0-based, top to bottom)
            
        Returns:
            The tile surface, or None if coordinates are invalid
        """
        return self.tiles.get((col, row))
    
    def get_tile_by_id(self, tile_id: int) -> Optional[pygame.Surface]:
        """
        Get a tile by a single ID (row-major order).
        
        Args:
            tile_id: Tile ID (0 = top-left, increases left-to-right, top-to-bottom)
            
        Returns:
            The tile surface, or None if ID is invalid
        """
        if self.cols == 0:
            return None
        col = tile_id % self.cols
        row = tile_id // self.cols
        return self.get_tile(col, row)


class TileSetManager:
    """
    Manages multiple tilesets and provides unified tile access.
    
    This mirrors the Godot TileSet resource which combines multiple
    TileSetAtlasSource entries into one resource.
    """
    
    def __init__(self):
        self.tilesets: Dict[str, TileSet] = {}
    
    def load_tileset(self, name: str, filename: str, tile_size: int = 16) -> TileSet:
        """
        Load a tileset and register it with a name.
        
        Args:
            name: Identifier for this tileset (e.g., 'grass', 'plains')
            filename: Image file name
            tile_size: Tile size in pixels
            
        Returns:
            The loaded TileSet
        """
        tileset = TileSet(filename, tile_size)
        self.tilesets[name] = tileset
        return tileset
    
    def get_tileset(self, name: str) -> Optional[TileSet]:
        """Get a tileset by name."""
        return self.tilesets.get(name)
    
    def get_tile(self, tileset_name: str, col: int, row: int) -> Optional[pygame.Surface]:
        """
        Get a tile from a named tileset.
        
        Args:
            tileset_name: Name of the tileset
            col: Column index
            row: Row index
            
        Returns:
            The tile surface, or None if not found
        """
        tileset = self.tilesets.get(tileset_name)
        if tileset:
            return tileset.get_tile(col, row)
        return None
