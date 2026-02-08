"""Game configuration settings."""
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
SPRITES_DIR = os.path.join(ASSETS_DIR, 'sprites')
TILESETS_DIR = os.path.join(SPRITES_DIR, 'tilesets')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')

# Display settings
SCREEN_WIDTH = 896
SCREEN_HEIGHT = 600
SCALE = 4  # Pixel art scaling
FPS = 60

# World/Tilemap settings (matching die-insel tutorial dimensions)
TILE_SIZE = 16  # Base tile size in pixels
WORLD_WIDTH_TILES = 14  # World width in tiles (X: 0-13 from Godot map)
WORLD_HEIGHT_TILES = 25  # World height in tiles (Y: 0-24 from Godot map)
WORLD_WIDTH = WORLD_WIDTH_TILES * TILE_SIZE * SCALE  # 672 pixels at 3x scale
WORLD_HEIGHT = WORLD_HEIGHT_TILES * TILE_SIZE * SCALE  # 1200 pixels at 3x scale

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

# Enemy letter display settings
ENEMY_LETTER_FONT_SIZE = 16
ENEMY_LETTER_OFFSET_Y = 35  # pixels above enemy center
ENEMY_LETTER_BACKDROP_PATH = os.path.join(SPRITES_DIR, 'ui', 'Rahmen - klein.png')

# Animation settings
ANIMATION_FPS = 5

# Sprite sheet configurations
PLAYER_SPRITE_CONFIG = {
    'path': os.path.join(SPRITES_DIR, 'characters', 'player.png'),
    'frame_width': 48,
    'frame_height': 48,
    'animations': {
        'idle_down': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_down.png'),
            'frame_width': 270,
            'frame_height': 540,
            'row': 0, 'frames': 1, 'fps': 5,
            'scale': 0.25
        },
        'walk_down': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_down.png'),
            'frame_width': 270,
            'frame_height': 540,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25
        },
        'walk_left': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_right.png'),
            'frame_width': 270,
            'frame_height': 528,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25,
            'allow_flip': True
        },
        'walk_right': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_right.png'),
            'frame_width': 270,
            'frame_height': 528,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25,
            'allow_flip': True
        },
        'walk_up': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_up.png'),
            'frame_width': 270,
            'frame_height': 534,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25
        },
        'cast_down': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'cast_down.png'),
            'frame_width': 270,
            'frame_height': 534,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25
        },
        'cast_left': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'cast_right.png'),
            'frame_width': 280,
            'frame_height': 534,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25,
            'allow_flip': True
        },
        'cast_right': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'cast_right.png'),
            'frame_width': 280,
            'frame_height': 534,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25
        },
        'cast_up': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_up.png'),
            'frame_width': 270,
            'frame_height': 534,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25
        },
        'death': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_down.png'),
            'frame_width': 270,
            'frame_height': 540,
            'row': 0, 'frames': 1, 'fps': 5,
            'scale': 0.25,
            'loop': False
        },
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
        'attack_front': {'row': 6, 'frames': 4, 'fps': 8},
        'attack_side': {'row': 7, 'frames': 4, 'fps': 8},
        'attack_back': {'row': 8, 'frames': 4, 'fps': 8},
        'damaged_front': {'row': 9, 'frames': 3, 'fps': 8},
        'damaged_side': {'row': 10, 'frames': 3, 'fps': 8},
        'damaged_back': {'row': 11, 'frames': 3, 'fps': 8},
        'death': {'row': 12, 'frames': 5, 'fps': 5},
    }
}

# Skeleton enemy - 48x48 grid, 6 cols x 13 rows (288x624)
SKELETON_SPRITE_CONFIG = {
    'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'),
    'frame_width': 48,
    'frame_height': 48,
    'animations': {
        'idle_front': {'row': 0, 'frames': 6, 'fps': 5},
        'idle_side': {'row': 1, 'frames': 6, 'fps': 5},
        'idle_back': {'row': 2, 'frames': 6, 'fps': 5},
        'walk_front': {'row': 3, 'frames': 6, 'fps': 5},
        'walk_side': {'row': 4, 'frames': 6, 'fps': 5},
        'walk_back': {'row': 5, 'frames': 6, 'fps': 5},
        'attack_front': {'row': 6, 'frames': 4, 'fps': 8},
        'attack_side': {'row': 7, 'frames': 4, 'fps': 8},
        'attack_back': {'row': 8, 'frames': 4, 'fps': 8},
        'damaged_front': {'row': 9, 'frames': 3, 'fps': 8},
        'damaged_side': {'row': 10, 'frames': 3, 'fps': 8},
        'damaged_back': {'row': 11, 'frames': 3, 'fps': 8},
        'death': {'row': 12, 'frames': 5, 'fps': 5},
    }
}

# Spell settings
SPELL_TYPES = ['fireball', 'ice', 'earth', 'nature', 'air', 'arcane', 'lightning']
SPELL_SPEED = 200  # pixels per second
SPELL_DAMAGE = 150  # enough to one-shot enemies (ENEMY_MAX_HEALTH = 100)
SPELL_COOLDOWN = 0.5  # seconds between casts
SPELL_LIFETIME = 2.0  # seconds before despawn

SPELL_PROJECTILE_CONFIG = {
    'path': os.path.join(SPRITES_DIR, 'spell_projectiles_sprite_sheet.png'),
    'frame_width': 32,
    'frame_height': 32,
    'animations': {
        'fireball': {'row': 0, 'frames': 8, 'fps': 10},
        'ice': {'row': 1, 'frames': 8, 'fps': 10},
        'earth': {'row': 2, 'frames': 8, 'fps': 10},
        'nature': {'row': 3, 'frames': 8, 'fps': 10},
        'air': {'row': 4, 'frames': 8, 'fps': 10},
        'arcane': {'row': 5, 'frames': 8, 'fps': 10},
        'lightning': {'row': 6, 'frames': 8, 'fps': 10},
    }
}

# Camera input settings (ASL hand sign detection)
CAMERA_ENABLED = True           # Toggle camera integration on/off
CAMERA_HOLD_TIME = 0.5          # Seconds to hold a letter before it fires
CAMERA_CONFIDENCE = 0.8         # Minimum confidence for hand detection
CAMERA_DEFAULT_SPELL = 'arcane' # Spell type used for camera-triggered spells
CAMERA_SHOW_PREVIEW = True      # Show camera preview window for debugging
