"""Game configuration settings."""
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
SPRITES_DIR = os.path.join(ASSETS_DIR, 'sprites')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')

# Display settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
SCALE = 3  # Pixel art scaling
FPS = 60

# World/Tilemap settings (matching die-insel tutorial dimensions)
TILE_SIZE = 16  # Base tile size in pixels
WORLD_WIDTH_TILES = 25  # World width in tiles (400 / 16)
WORLD_HEIGHT_TILES = 14  # World height in tiles (224 / 16)
WORLD_WIDTH = WORLD_WIDTH_TILES * TILE_SIZE * SCALE  # 1200 pixels at 3x scale
WORLD_HEIGHT = WORLD_HEIGHT_TILES * TILE_SIZE * SCALE  # 672 pixels at 3x scale

# Camera settings
CAMERA_DRAG_MARGIN = 0.15  # 15% margin before camera follows (matching tutorial)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Player settings
PLAYER_SPEED = 100
PLAYER_MAX_HEALTH = 100
PLAYER_ATTACK_DAMAGE = 40
PLAYER_ATTACK_DURATION = 0.8  # seconds
PLAYER_HEALTH_REGEN = 5
PLAYER_REGEN_INTERVAL = 5.0  # seconds

# Enemy settings
ENEMY_CHASE_SPEED = 40
ENEMY_IDLE_SPEED = 20
ENEMY_MAX_HEALTH = 100
ENEMY_ATTACK_DAMAGE = 50
ENEMY_DETECTION_RADIUS = 51
ENEMY_ATTACK_RANGE = 12
ENEMY_DAMAGE_COOLDOWN = 0.8  # seconds
ENEMY_XP_VALUE = 10

# Animation settings
ANIMATION_FPS = 5

# Sprite sheet configurations
PLAYER_SPRITE_CONFIG = {
    'path': os.path.join(SPRITES_DIR, 'characters', 'player.png'),
    'frame_width': 48,
    'frame_height': 48,
    'animations': {
        'idle_front': {'row': 0, 'frames': 6, 'fps': 5},
        'idle_side': {'row': 1, 'frames': 6, 'fps': 5},
        'idle_back': {'row': 2, 'frames': 6, 'fps': 5},
        'walk_front': {'row': 3, 'frames': 6, 'fps': 5},
        'walk_side': {'row': 4, 'frames': 6, 'fps': 5},
        'walk_back': {'row': 5, 'frames': 6, 'fps': 5},
        'attack_front': {'row': 6, 'frames': 4, 'fps': 5},
        'attack_side': {'row': 7, 'frames': 4, 'fps': 5},
        'attack_back': {'row': 8, 'frames': 4, 'fps': 5},
        'death': {'row': 9, 'frames': 3, 'fps': 5},
    }
}

SLIME_SPRITE_CONFIG = {
    'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'),
    'frame_width': 32,
    'frame_height': 32,
    'animations': {
        'idle_front': {'row': 0, 'frames': 4, 'fps': 5},
        'idle_side': {'row': 1, 'frames': 4, 'fps': 5},
        'idle_back': {'row': 2, 'frames': 4, 'fps': 5},
        'walk_front': {'row': 3, 'frames': 6, 'fps': 5},
        'walk_side': {'row': 4, 'frames': 6, 'fps': 5},
        'walk_back': {'row': 5, 'frames': 6, 'fps': 5},
        'death': {'row': 12, 'frames': 5, 'fps': 5},
    }
}

SPIRIT_SPRITE_CONFIG = {
    'path': os.path.join(SPRITES_DIR, 'characters', 'spirit2.png'),
    'frame_width': 32,
    'frame_height': 32,
    'animations': {
        'float': {'row': 0, 'frames': 6, 'fps': 5},
    }
}

CAMPFIRE_SPRITE_CONFIG = {
    'path': os.path.join(SPRITES_DIR, 'objects', 'campfire.png'),
    'frame_width': 32,
    'frame_height': 32,
    'animations': {
        'burn': {'row': 0, 'frames': 4, 'fps': 5},
    }
}

MUSHROOM_SPRITE_CONFIG = {
    'path': os.path.join(SPRITES_DIR, 'objects', 'mushroom.png'),
    'frame_width': 32,
    'frame_height': 32,
    'animations': {
        'idle': {'row': 0, 'frames': 1, 'fps': 1},
        'harvest': {'row': 0, 'frames': 5, 'fps': 5},
    }
}
