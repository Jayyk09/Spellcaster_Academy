"""Map loader for loading tilemap data from JSON files."""
import json
import os
from typing import Dict, Any, Optional
from core.tilemap import TileMap
from config.settings import BASE_DIR


def load_map_data(map_name: str) -> Optional[Dict[str, Any]]:
    """
    Load raw map data from a JSON file.
    
    Args:
        map_name: Name of the map file (without .json extension)
        
    Returns:
        Dictionary with map data, or None if loading failed
    """
    path = os.path.join(BASE_DIR, 'data', f'{map_name}.json')
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load map {map_name}: {e}")
        return None


def create_tilemap_from_data(map_data: Dict[str, Any]) -> TileMap:
    """
    Create a TileMap from loaded map data.
    
    Args:
        map_data: Dictionary with map configuration
        
    Returns:
        Configured TileMap instance
    """
    width = map_data.get('width', 25)
    height = map_data.get('height', 14)
    tile_size = map_data.get('tile_size', 16)
    
    tilemap = TileMap(width, height, tile_size)
    tilemap.load_tilesets()
    
    layers_data = map_data.get('layers', {})
    
    for layer_name, layer_data in layers_data.items():
        layer = tilemap.get_layer(layer_name)
        if not layer:
            continue
        
        # Handle fill directive
        fill = layer_data.get('fill')
        if fill:
            tileset_name, tile_col, tile_row = fill
            layer.fill(tileset_name, tile_col, tile_row)
        
        # Handle individual tiles
        tiles = layer_data.get('tiles', [])
        for tile_entry in tiles:
            # Skip comment entries
            if 'comment' in tile_entry and 'x' not in tile_entry:
                continue
            
            x = tile_entry.get('x')
            y = tile_entry.get('y')
            tileset = tile_entry.get('tileset')
            col = tile_entry.get('col')
            row = tile_entry.get('row')
            
            if all(v is not None for v in [x, y, tileset, col, row]):
                layer.set_tile(x, y, tileset, col, row)
    
    return tilemap


def load_tilemap(map_name: str) -> Optional[TileMap]:
    """
    Load and create a TileMap from a JSON file.
    
    Args:
        map_name: Name of the map (e.g., 'world_map')
        
    Returns:
        Configured TileMap instance, or None if loading failed
    """
    map_data = load_map_data(map_name)
    if map_data is None:
        return None
    
    return create_tilemap_from_data(map_data)


def get_spawn_points(map_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get spawn point data from map data.
    
    Args:
        map_data: Dictionary with map configuration
        
    Returns:
        Dictionary with spawn point configurations
    """
    return map_data.get('spawn_points', {})


def get_transitions(map_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get transition zone data from map data.
    
    Args:
        map_data: Dictionary with map configuration
        
    Returns:
        Dictionary with transition zone configurations
    """
    return map_data.get('transitions', {})
