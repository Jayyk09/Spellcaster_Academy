#!/usr/bin/env python3
"""
Decode Godot 4 TileMapLayer PackedByteArray data - Debug version.

Let me analyze the raw bytes more carefully.
"""

import base64
import struct
import re
from pathlib import Path


def hex_dump(data: bytes, num_bytes: int = 96) -> None:
    """Print a hex dump of the first N bytes."""
    print(f"First {min(len(data), num_bytes)} bytes:")
    for i in range(0, min(len(data), num_bytes), 12):
        chunk = data[i:i+12]
        hex_str = ' '.join(f'{b:02x}' for b in chunk)
        print(f"  {i:4d}: {hex_str}")


def analyze_ground_layer():
    """Analyze the ground layer data specifically."""
    # Read directly from the .tscn file
    tscn_path = Path("die-insel_tutorial_v2/scenes/world.tscn")
    content = tscn_path.read_text()
    
    # Extract ground layer data
    match = re.search(r'\[node name="ground" type="TileMapLayer"[^\]]*\]\n(?:[^\[]*\n)*?tile_map_data = PackedByteArray\("([^"]+)"\)', content)
    if not match:
        print("Could not find ground layer!")
        return
    
    ground_b64 = match.group(1)
    print(f"Base64 string length: {len(ground_b64)}")
    
    raw_bytes = base64.b64decode(ground_b64)
    print(f"Ground layer: {len(raw_bytes)} bytes total")
    
    hex_dump(raw_bytes)
    
    # Try 12-byte entries
    print("\nAs 12-byte entries (x, y, source, atlas_x, atlas_y, flags):")
    for i in range(5):
        offset = i * 12
        entry = raw_bytes[offset:offset + 12]
        values = struct.unpack('<hhhhhh', entry)
        print(f"  Entry {i}: x={values[0]}, y={values[1]}, src={values[2]}, ax={values[3]}, ay={values[4]}, fl={values[5]}")
    
    # The data looks suspicious. Let me try different interpretations.
    # Looking at the hex: 00 00 00 00 00 00 01 00 00 00 00 00
    # If x=0, y=0 are first 4 bytes (int32?), then...
    
    print("\nAs 8-byte entries (x32, y32, source16, flags16):")
    for i in range(5):
        offset = i * 8
        if offset + 8 > len(raw_bytes):
            break
        entry = raw_bytes[offset:offset + 8]
        x, y, source, flags = struct.unpack('<hhHH', entry)
        print(f"  Entry {i}: x={x}, y={y}, src={source}, flags={flags}")
    
    print("\n\nLet me look for patterns by analyzing specific bytes...")
    print("Looking at bytes 0-3 (should be tile coords):")
    
    # Actually, looking at the pattern: 00 00 00 00 00 00 01 00 00 00 00 00
    # This could be:
    # 00 00 = x (0)
    # 00 00 = y (0) 
    # 00 00 = ? (0)
    # 01 00 = source_id (1 = grass)
    # 00 00 = atlas_x (0)
    # 00 00 = atlas_y (0)
    
    print("\nReinterpreting as (x16, y16, ???, source, atlas_x, atlas_y):")
    num_entries = len(raw_bytes) // 12
    print(f"Total entries: {num_entries}")
    
    # Let me try: maybe the "unk" is actually x, and the first 2 bytes are something else?
    # Or maybe Godot stores multiple tiles at the same grid position for different "layers"?
    # That would explain why we see x=0 but unk varies from 0-24 (that's the real X!)
    
    print("\nTrying (cell_unk, y16, x16, source, atlas_x, atlas_y):")
    all_entries = []
    for i in range(num_entries):
        offset = i * 12
        entry = raw_bytes[offset:offset + 12]
        cell_unk, y, x, source, ax, ay = struct.unpack('<hhhHHH', entry)
        all_entries.append((x, y, cell_unk, source, ax, ay))
    
    all_coords = set((e[0], e[1]) for e in all_entries)
    print(f"Unique coordinates: {len(all_coords)}")
    coords_sorted = sorted(all_coords)
    print(f"X range: {min(c[0] for c in coords_sorted)} to {max(c[0] for c in coords_sorted)}")
    print(f"Y range: {min(c[1] for c in coords_sorted)} to {max(c[1] for c in coords_sorted)}")
    
    # Count tiles per position to see if there are duplicates
    from collections import Counter
    coord_counts = Counter((e[0], e[1]) for e in all_entries)
    print(f"\nTiles per coordinate (showing non-1 counts):")
    for coord, count in sorted(coord_counts.items()):
        if count != 1:
            print(f"  ({coord[0]}, {coord[1]}): {count} tiles")
    
    # Show first 15 entries
    print("\nFirst 15 entries:")
    for i, e in enumerate(all_entries[:15]):
        print(f"  ({e[0]:3}, {e[1]:3}) cell_info={e[2]}, src={e[3]}, atlas=({e[4]},{e[5]})")
    
    # Show sample of entries at x > 10
    print("\nEntries at x > 10:")
    count = 0
    for e in all_entries:
        if e[0] > 10 and count < 10:
            print(f"  ({e[0]:3}, {e[1]:3}) cell_info={e[2]}, src={e[3]}, atlas=({e[4]},{e[5]})")
            count += 1


def main():
    analyze_ground_layer()


if __name__ == "__main__":
    main()
