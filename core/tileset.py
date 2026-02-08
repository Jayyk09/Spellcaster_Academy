"""TileSet class for loading and managing tileset images."""
import pygame
import os
from typing import Dict, List, Tuple, Optional
from config.settings import SPRITES_DIR


# Multi-tile region definitions for objects.png (256x208, 16 cols x 13 rows)
# Format: (col, row) -> (width_tiles, height_tiles, y_sort_origin, has_collision)
# y_sort_origin formula: (height_tiles - 1 - foot_offset) * 16 + 15
# has_collision indicates if this object should block movement
# Mappings based on actual objects.png tileset layout
OBJECTS_REGIONS = {
    # === ENVIRONMENT (nature objects) ===
    (0, 5): (3, 4, 15, True),      # tree_green (3x4, foot_offset=2)
    (3, 5): (3, 4, 15, True),      # tree_apple (3x4, foot_offset=2)
    (0, 9): (3, 4, 15, True),      # tree_green_long (3x4, foot_offset=2)
    (3, 9): (3, 4, 15, True),      # tree_apple_long (3x4, foot_offset=2)
    (6, 7): (2, 2, 15, True),      # bush_large (2x2, foot_offset=1)
    (6, 5): (2, 1, 15, True),      # log_mushroom (2x1)
    (6, 6): (2, 1, 15, True),      # log_hollow (2x1)
    (6, 9): (3, 1, 15, True),      # log_long (3x1)
    (8, 6): (2, 3, 15, True),      # small_tree (2x3, foot_offset=1)
    (10, 7): (2, 2, 15, True),     # trunk_large (2x2, foot_offset=1)
    
    # === PROPS (small objects) ===
    (0, 0): (1, 1, 15, True),      # signpost
    (0, 1): (1, 1, 15, True),      # rock_medium
    (1, 1): (1, 1, 15, True),      # rock_small_a
    (2, 1): (1, 1, 15, True),      # rock_small_b
    (6, 0): (1, 1, 15, True),      # tombstone
    (8, 0): (1, 1, 15, True),      # skull
    (8, 1): (1, 1, 15, True),      # ditch
}

FENCES_REGIONS = {
    (0, 0): (1, 3, 15, False),      # fence_vertical
    (1, 3): (3, 1, 15, False),      # fence_horizontal
    (0, 3): (1, 1, 15, False),      # singular_fence_post
}

class TileSet:
    """
    Loads a tileset image and provides access to individual tiles.
    
    Tilesets are sprite sheets containing multiple tiles arranged in a grid.
    Each tile can be accessed by its atlas coordinates (column, row).
    
    Supports multi-tile regions for objects that span multiple tiles.
    """
    
    def __init__(self, filename: str, tile_size: int = 16, 
                 regions: Optional[Dict] = None):
        """
        Initialize a tileset from an image file.
        
        Args:
            filename: Name of the tileset image file (in assets/sprites/tilesets/)
            tile_size: Size of each tile in pixels (assumes square tiles)
            regions: Optional dict of (col, row) -> (width, height, y_sort_origin, has_collision)
                     for multi-tile regions
        """
        self.tile_size = tile_size
        self.tiles: Dict[Tuple[int, int], pygame.Surface] = {}
        self.regions = regions or {}
        
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
        
        # Extract all tiles (single-tile only, multi-tile extracted on demand)
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
    
    def get_region(self, col: int, row: int) -> Optional[Tuple[pygame.Surface, int, bool]]:
        """
        Get a multi-tile region by its atlas coordinates.
        
        Args:
            col: Column index of top-left tile
            row: Row index of top-left tile
            
        Returns:
            Tuple of (surface, y_sort_origin, has_collision) or None if not a region
        """
        if self.image is None:
            return None
            
        region_info = self.regions.get((col, row))
        if not region_info:
            # Fall back to single tile with default y_sort_origin, no collision
            tile = self.get_tile(col, row)
            if tile:
                return (tile, self.tile_size - 1, False)  # Default: bottom of tile, no collision
            return None
        
        # Handle both old 3-tuple and new 4-tuple format
        if len(region_info) == 4:
            width_tiles, height_tiles, y_sort_origin, has_collision = region_info
        else:
            width_tiles, height_tiles, y_sort_origin = region_info
            has_collision = False
        
        # Create surface for multi-tile region
        pixel_width = width_tiles * self.tile_size
        pixel_height = height_tiles * self.tile_size
        
        surface = pygame.Surface((pixel_width, pixel_height), pygame.SRCALPHA)
        surface.blit(
            self.image,
            (0, 0),
            (col * self.tile_size, row * self.tile_size, pixel_width, pixel_height)
        )
        
        return (surface, y_sort_origin, has_collision)
    
    def get_region_size(self, col: int, row: int) -> Tuple[int, int]:
        """
        Get the size of a region in tiles.
        
        Returns:
            (width_tiles, height_tiles) - defaults to (1, 1) for single tiles
        """
        region_info = self.regions.get((col, row))
        if region_info:
            return (region_info[0], region_info[1])
        return (1, 1)
    
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
    
    def load_tileset(self, name: str, filename: str, tile_size: int = 16,
                     regions: Optional[Dict] = None) -> TileSet:
        """
        Load a tileset and register it with a name.
        
        Args:
            name: Identifier for this tileset (e.g., 'grass', 'plains')
            filename: Image file name
            tile_size: Tile size in pixels
            regions: Optional multi-tile region definitions
            
        Returns:
            The loaded TileSet
        """
        tileset = TileSet(filename, tile_size, regions)
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
    
    def get_region(self, tileset_name: str, col: int, row: int) -> Optional[Tuple[pygame.Surface, int, bool]]:
        """
        Get a multi-tile region from a named tileset.
        
        Args:
            tileset_name: Name of the tileset
            col: Column index
            row: Row index
            
        Returns:
            Tuple of (surface, y_sort_origin, has_collision) or None
        """
        tileset = self.tilesets.get(tileset_name)
        if tileset:
            return tileset.get_region(col, row)
        return None
    
    def get_region_size(self, tileset_name: str, col: int, row: int) -> Tuple[int, int]:
        """
        Get the size of a region in tiles.
        
        Returns:
            (width_tiles, height_tiles)
        """
        tileset = self.tilesets.get(tileset_name)
        if tileset:
            return tileset.get_region_size(col, row)
        return (1, 1)
