"""TileMap classes for rendering layered tile-based worlds."""
import pygame
from typing import Dict, List, Tuple, Optional, Set
from core.tileset import TileSetManager, OBJECTS_REGIONS


class TileMapLayer:
    """
    A single layer of tiles in a tilemap.
    
    Each layer stores tile data as a 2D grid. Tiles are referenced by
    (tileset_name, col, row) tuples.
    
    Layers can be:
    - Ground layers (rendered first, no collision)
    - Collision layers (cliffs, water - block movement)
    - Y-sort layers (objects that need depth sorting with entities)
    """
    
    def __init__(self, width: int, height: int, tile_size: int = 16):
        """
        Initialize an empty tile layer.
        
        Args:
            width: Layer width in tiles
            height: Layer height in tiles
            tile_size: Size of each tile in pixels
        """
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.y_sort = False  # Whether this layer uses y-sorting
        self.has_collision = False  # Whether tiles in this layer block movement
        
        # Tile data: grid[y][x] = (tileset_name, tile_col, tile_row) or None
        self.grid: List[List[Optional[Tuple[str, int, int]]]] = [
            [None for _ in range(width)] for _ in range(height)
        ]
        
        # Cached surface for non-y-sorted layers
        self._cached_surface: Optional[pygame.Surface] = None
        self._cache_dirty = True
    
    def set_tile(self, x: int, y: int, tileset_name: str, tile_col: int, tile_row: int):
        """
        Set a tile at the given grid position.
        
        Args:
            x: Grid x coordinate (column)
            y: Grid y coordinate (row)
            tileset_name: Name of the tileset containing the tile
            tile_col: Column in the tileset
            tile_row: Row in the tileset
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = (tileset_name, tile_col, tile_row)
            self._cache_dirty = True
    
    def get_tile(self, x: int, y: int) -> Optional[Tuple[str, int, int]]:
        """Get the tile data at a grid position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None
    
    def clear_tile(self, x: int, y: int):
        """Remove the tile at a grid position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = None
            self._cache_dirty = True
    
    def fill(self, tileset_name: str, tile_col: int, tile_row: int):
        """Fill the entire layer with a single tile type."""
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y][x] = (tileset_name, tile_col, tile_row)
        self._cache_dirty = True
    
    def render_to_surface(self, tileset_manager: TileSetManager) -> pygame.Surface:
        """
        Render this layer to a surface.
        
        Uses caching for non-y-sorted layers to improve performance.
        
        Args:
            tileset_manager: Manager containing the tilesets
            
        Returns:
            Surface containing the rendered layer
        """
        # Use cache if available and not dirty
        if not self._cache_dirty and self._cached_surface is not None:
            return self._cached_surface
        
        # Create surface for this layer
        surface = pygame.Surface(
            (self.width * self.tile_size, self.height * self.tile_size),
            pygame.SRCALPHA
        )
        
        # Render each tile
        for y in range(self.height):
            for x in range(self.width):
                tile_data = self.grid[y][x]
                if tile_data:
                    tileset_name, tile_col, tile_row = tile_data
                    tile = tileset_manager.get_tile(tileset_name, tile_col, tile_row)
                    if tile:
                        surface.blit(tile, (x * self.tile_size, y * self.tile_size))
        
        # Cache for non-y-sorted layers
        if not self.y_sort:
            self._cached_surface = surface
            self._cache_dirty = False
        
        return surface
    
    def get_collision_tiles(self) -> Set[Tuple[int, int]]:
        """
        Get all grid positions that have collision tiles.
        
        Returns:
            Set of (x, y) grid coordinates with collision
        """
        if not self.has_collision:
            return set()
        
        collision_tiles = set()
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] is not None:
                    collision_tiles.add((x, y))
        return collision_tiles


class TileMap:
    """
    A complete tilemap consisting of multiple layers.
    
    Manages rendering order and provides collision detection.
    Layer order (bottom to top) - matching Godot die-insel tutorial:
    1. ground - Base terrain (grass) with terrain edge overlays
    2. lvl1 - Cliff fill/lower level (below walking surface)
    3. cliffs - Cliff edge tiles with collision
    4. ysort - Objects that y-sort with entities (trees, rocks, bushes)
    """
    
    LAYER_ORDER = ['ground', 'lvl1', 'cliffs', 'ysort']
    
    def __init__(self, width: int, height: int, tile_size: int = 16):
        """
        Initialize a tilemap with the standard layers.
        
        Args:
            width: Map width in tiles
            height: Map height in tiles
            tile_size: Size of each tile in pixels
        """
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.pixel_width = width * tile_size
        self.pixel_height = height * tile_size
        
        # Create standard layers
        self.layers: Dict[str, TileMapLayer] = {}
        for layer_name in self.LAYER_ORDER:
            layer = TileMapLayer(width, height, tile_size)
            
            # Set layer properties
            if layer_name == 'cliffs':
                layer.has_collision = True
            if layer_name == 'ysort':
                layer.y_sort = True
            
            self.layers[layer_name] = layer
        
        # Tileset manager
        self.tileset_manager = TileSetManager()
        
        # Cached combined surface (without y-sorted layers)
        self._combined_surface: Optional[pygame.Surface] = None
        self._combined_dirty = True
    
    def load_tilesets(self):
        """Load all required tilesets."""
        self.tileset_manager.load_tileset('grass', 'grass.png', 16)
        self.tileset_manager.load_tileset('plains', 'plains.png', 16)
        # Load objects with multi-tile region definitions
        self.tileset_manager.load_tileset('objects', 'objects.png', 16, OBJECTS_REGIONS)
        self.tileset_manager.load_tileset('water', 'water-sheet.png', 16)
        self.tileset_manager.load_tileset('decor16', 'decor_16x16.png', 16)
        self.tileset_manager.load_tileset('decor8', 'decor_8x8.png', 8)
        self.tileset_manager.load_tileset('flooring', 'flooring.png', 16)
    
    def get_layer(self, name: str) -> Optional[TileMapLayer]:
        """Get a layer by name."""
        return self.layers.get(name)
    
    def set_tile(self, layer_name: str, x: int, y: int, 
                 tileset_name: str, tile_col: int, tile_row: int):
        """Set a tile in a specific layer."""
        layer = self.layers.get(layer_name)
        if layer:
            layer.set_tile(x, y, tileset_name, tile_col, tile_row)
            self._combined_dirty = True
    
    def get_collision_rects(self) -> List[pygame.Rect]:
        """
        Get all collision rectangles from collision layers.
        
        Returns:
            List of pygame.Rect objects for collision detection
        """
        rects = []
        for layer_name in ('cliffs',):
            layer = self.layers.get(layer_name)
            if layer and layer.has_collision:
                for (x, y) in layer.get_collision_tiles():
                    rect = pygame.Rect(
                        x * self.tile_size,
                        y * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                    rects.append(rect)
        return rects
    
    def is_position_blocked(self, pixel_x: float, pixel_y: float) -> bool:
        """
        Check if a pixel position is blocked by collision tiles.
        
        Args:
            pixel_x: X position in pixels
            pixel_y: Y position in pixels
            
        Returns:
            True if the position is blocked
        """
        # Convert to grid coordinates
        grid_x = int(pixel_x // self.tile_size)
        grid_y = int(pixel_y // self.tile_size)
        
        # Check collision layers
        for layer_name in ('cliffs',):
            layer = self.layers.get(layer_name)
            if layer and layer.has_collision:
                tile = layer.get_tile(grid_x, grid_y)
                if tile is not None:
                    return True
        
        return False
    
    def is_rect_blocked(self, rect: pygame.Rect) -> bool:
        """
        Check if a rectangle overlaps any collision tiles.
        
        Args:
            rect: Rectangle to check
            
        Returns:
            True if any part of the rect is blocked
        """
        # Get grid bounds that the rect covers
        start_x = int(rect.left // self.tile_size)
        end_x = int((rect.right - 1) // self.tile_size) + 1
        start_y = int(rect.top // self.tile_size)
        end_y = int((rect.bottom - 1) // self.tile_size) + 1
        
        # Check all tiles in the range
        for layer_name in ('cliffs',):
            layer = self.layers.get(layer_name)
            if layer and layer.has_collision:
                for y in range(start_y, end_y):
                    for x in range(start_x, end_x):
                        if layer.get_tile(x, y) is not None:
                            return True
        
        return False
    
    def render_base_layers(self) -> pygame.Surface:
        """
        Render all non-y-sorted layers to a combined surface.
        
        Returns:
            Surface containing ground, lvl1, and cliffs layers
        """
        if not self._combined_dirty and self._combined_surface is not None:
            return self._combined_surface
        
        # Create combined surface
        surface = pygame.Surface(
            (self.pixel_width, self.pixel_height),
            pygame.SRCALPHA
        )
        
        # Render layers in order (skip ysort - that's rendered with entities)
        for layer_name in self.LAYER_ORDER:
            if layer_name == 'ysort':
                continue
            layer = self.layers.get(layer_name)
            if layer:
                layer_surface = layer.render_to_surface(self.tileset_manager)
                surface.blit(layer_surface, (0, 0))
        
        self._combined_surface = surface
        self._combined_dirty = False
        
        return surface
    
    def get_decoration_tiles(self) -> List[Tuple[pygame.Surface, int, int, int]]:
        """
        Get ysort layer tiles for y-sorted rendering with entities.
        
        Returns:
            List of (surface, pixel_x, pixel_y, sort_y) tuples for each object.
            sort_y is the y-coordinate used for depth sorting (includes y_sort_origin).
        """
        decorations = []
        layer = self.layers.get('ysort')
        if not layer:
            return decorations
        
        for y in range(layer.height):
            for x in range(layer.width):
                tile_data = layer.grid[y][x]
                if tile_data:
                    tileset_name, tile_col, tile_row = tile_data
                    
                    # Get multi-tile region with y_sort_origin
                    region_data = self.tileset_manager.get_region(tileset_name, tile_col, tile_row)
                    if region_data:
                        surface, y_sort_origin = region_data
                        pixel_x = x * self.tile_size
                        pixel_y = y * self.tile_size
                        # sort_y is where the object's "feet" are for depth sorting
                        sort_y = pixel_y + y_sort_origin
                        decorations.append((surface, pixel_x, pixel_y, sort_y))
        
        return decorations
