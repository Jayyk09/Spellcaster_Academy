#!/usr/bin/env python3
"""
Decode Godot 4 TileMapLayer PackedByteArray data - Corrected version.

Format is 12 bytes per tile:
- 2 bytes: x coordinate (int16)
- 2 bytes: y coordinate (int16)  
- 2 bytes: padding/layer info
- 2 bytes: source_id (matches tileset sources in world.tres)
- 2 bytes: atlas_x coordinate in tileset
- 2 bytes: atlas_y coordinate in tileset
"""

import base64
import struct
import re
import json
from pathlib import Path


def decode_layer(base64_data: str, debug: bool = False) -> list[tuple]:
    """Decode a single layer's tile data."""
    raw_bytes = base64.b64decode(base64_data)
    num_entries = len(raw_bytes) // 12
    
    if debug:
        print(f"Raw bytes ({len(raw_bytes)} total):")
        for i in range(min(5, num_entries)):
            offset = i * 12
            chunk = raw_bytes[offset:offset + 12]
            hex_str = ' '.join(f'{b:02x}' for b in chunk)
            print(f"  {i}: {hex_str}")
    
    entries = []
    for i in range(num_entries):
        offset = i * 12
        entry = raw_bytes[offset:offset + 12]
        # Let's try: x, y, ?, source, atlas_x, atlas_y
        # Or maybe it's stored column-first? Let me try y, x order
        raw = struct.unpack('<hhhhhh', entry)
        # raw[0] = first 2 bytes
        # raw[1] = second 2 bytes  
        # raw[2] = third 2 bytes
        # raw[3] = fourth 2 bytes (source_id)
        # raw[4] = fifth 2 bytes (atlas_x)
        # raw[5] = sixth 2 bytes (atlas_y)
        
        # Based on analysis, pad seems to be x, and first two bytes might be y split or something
        # Let me try: pad (bytes 4-5) as x, and bytes 0-3 combined somehow
        x = raw[0]
        y = raw[1]
        extra = raw[2]
        source = raw[3]
        ax = raw[4]
        ay = raw[5]
        
        # Actually, looking at the output - maybe the format encodes tiles
        # in a sparse way where multiple tiles at same y have incrementing "extra" field as x?
        # That would explain: all tiles have x=0 but extra goes 0-13 (14 columns?)
        
        # Let me just store all 6 fields and we'll figure it out
        entries.append((raw[0], raw[1], raw[2], raw[3], raw[4], raw[5]))
    
    return entries


def analyze_all_layers():
    """Analyze all layers and print statistics."""
    tscn_path = Path("die-insel_tutorial_v2/scenes/world.tscn")
    content = tscn_path.read_text()
    
    layer_pattern = r'\[node name="(\w+)" type="TileMapLayer"[^\]]*\]\n(?:[^\[]*\n)*?tile_map_data = PackedByteArray\("([^"]+)"\)'
    
    matches = re.findall(layer_pattern, content)
    
    all_layers = {}
    
    for layer_name, base64_data in matches:
        entries = decode_layer(base64_data, debug=(layer_name == 'ground'))
        all_layers[layer_name] = entries
        
        print(f"\n{'='*60}")
        print(f"Layer: {layer_name} ({len(entries)} tiles)")
        print('='*60)
        
        # Print unique values for each field
        field_names = ['field0', 'field1', 'field2', 'source', 'atlas_x', 'atlas_y']
        for i, name in enumerate(field_names):
            values = sorted(set(e[i] for e in entries))
            print(f"  {name}: {values[:20]}{'...' if len(values) > 20 else ''}")
        
        # Source mapping from world.tres:
        # 0 = objects.png
        # 1 = grass.png
        # 2 = plains.png
        # 3 = decor_8x8.png
        source_names = {0: 'objects', 1: 'grass', 2: 'plains', 3: 'decor8'}
        sources = set(e[3] for e in entries)
        for src in sorted(sources):
            count = sum(1 for e in entries if e[3] == src)
            name = source_names.get(src, f'unknown_{src}')
            print(f"    Source {src} ({name}): {count} tiles")
        
        # Hypothesis: field0=?, field1=row_in_column, field2=column
        # So real coords are (field2, field1)?
        print(f"\nIf (x=field2, y=field1):")
        coords = set((e[2], e[1]) for e in entries)
        if coords:
            print(f"  X range: {min(c[0] for c in coords)} to {max(c[0] for c in coords)}")
            print(f"  Y range: {min(c[1] for c in coords)} to {max(c[1] for c in coords)}")
            print(f"  Unique positions: {len(coords)}")
        
        # Show sample entries
        print(f"\nFirst 10 entries as (x=f2, y=f1):")
        for e in entries[:10]:
            src_name = source_names.get(e[3], f'src{e[3]}')
            print(f"  ({e[2]:3}, {e[1]:3}) {src_name} atlas=({e[4]},{e[5]}) f0={e[0]}")
    
    return all_layers


def convert_to_map_json(all_layers: dict) -> dict:
    """Convert decoded layers to our JSON map format."""
    
    source_names = {0: 'objects', 1: 'grass', 2: 'plains', 3: 'decor8'}
    
    # Use ground layer for map bounds (the actual playable area)
    # Other layers like ysort may have objects extending beyond the map
    ground_coords = []
    for e in all_layers.get('ground', []):
        x = e[2]  # field2 is x
        y = e[1]  # field1 is y
        ground_coords.append((x, y))
    
    if ground_coords:
        min_x = min(c[0] for c in ground_coords)
        max_x = max(c[0] for c in ground_coords)
        min_y = min(c[1] for c in ground_coords)
        max_y = max(c[1] for c in ground_coords)
    else:
        min_x, max_x, min_y, max_y = 0, 0, 0, 0
    
    print(f"\nMap bounds (from ground layer):")
    print(f"  X: {min_x} to {max_x} ({max_x - min_x + 1} tiles)")
    print(f"  Y: {min_y} to {max_y} ({max_y - min_y + 1} tiles)")
    
    # Build JSON structure
    json_layers = {}
    
    for layer_name, entries in all_layers.items():
        tiles = []
        for e in entries:
            # Format: (field0, field1=y, field2=x, source, atlas_x, atlas_y)
            x = e[2]
            y = e[1]
            source = e[3]
            ax = e[4]
            ay = e[5]
            
            tile = {
                "x": x,
                "y": y,
                "tileset": source_names.get(source, f"source_{source}"),
                "col": ax,
                "row": ay
            }
            tiles.append(tile)
        
        json_layers[layer_name] = {"tiles": tiles}
    
    return {
        "name": "world",
        "width": max_x - min_x + 1,
        "height": max_y - min_y + 1,
        "tile_size": 16,
        "layers": json_layers,
        "spawn_points": {
            "player_start": {"x": 207 // 16, "y": 158 // 16},  # pixel coords from tscn
            "enemy": {"x": 119 // 16, "y": 109 // 16},
            "shroom": {"x": 126 // 16, "y": 61 // 16}
        }
    }


def main():
    print("Analyzing Godot TileMapLayer data...\n")
    
    all_layers = analyze_all_layers()
    
    print("\n\n" + "="*60)
    print("CONVERTING TO JSON FORMAT")
    print("="*60)
    
    map_json = convert_to_map_json(all_layers)
    
    # Save
    output_path = Path("data/world_map_godot.json")
    with open(output_path, 'w') as f:
        json.dump(map_json, f, indent=2)
    
    print(f"\nSaved to: {output_path}")
    print(f"Total layers: {len(map_json['layers'])}")
    for layer_name, layer_data in map_json['layers'].items():
        print(f"  {layer_name}: {len(layer_data['tiles'])} tiles")


if __name__ == "__main__":
    main()
