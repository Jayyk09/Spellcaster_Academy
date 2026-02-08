"""Game configuration settings."""
import os

# Debug settings
DEBUG_SHOW_HITBOXES = False# Draw hitboxes for debugging

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
SPRITES_DIR = os.path.join(ASSETS_DIR, 'sprites')
TILESETS_DIR = os.path.join(SPRITES_DIR, 'tilesets')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')
SOUNDS_DIR = os.path.join(ASSETS_DIR, 'sounds')

# Display settings
SCREEN_WIDTH = 1125
SCREEN_HEIGHT = 750
SCALE = 3  # Pixel art scaling
FPS = 60

# World/Tilemap settings (matching world_map.json dimensions)
TILE_SIZE = 16  # Base tile size in pixels
WORLD_WIDTH_TILES = 46  # World width in tiles (matches world_map.json width)
WORLD_HEIGHT_TILES = 28  # World height in tiles (matches world_map.json height)
WORLD_WIDTH = WORLD_WIDTH_TILES * TILE_SIZE * SCALE  # 2944 pixels at 4x scale
WORLD_HEIGHT = WORLD_HEIGHT_TILES * TILE_SIZE * SCALE  # 1792 pixels at 4x scale

# Camera settings
CAMERA_DRAG_MARGIN = 0.0  # Camera always centered on player (no drag margin)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Player settings
PLAYER_SPEED = 120
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

# Enemy letter display settings
ENEMY_LETTER_FONT_SIZE = 16
ENEMY_LETTER_OFFSET_Y = 35  # pixels above enemy center
ENEMY_LETTER_BACKDROP_PATH = os.path.join(SPRITES_DIR, 'ui', 'Rahmen - klein.png')

SCALE_MULTIPLIER = 1.25  # Multiplier for scaling up sprites (e.g. 1.25 = 125% size)

# Animation settings
ANIMATION_FPS = 5

# Sprite sheet configurations
PLAYER_SPRITE_CONFIG = {
    'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_down.png'),
    'frame_width': 48,
    'frame_height': 48,
    'animations': {
        'idle_down': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_down.png'),
            'frame_width': 270,
            'frame_height': 540,
            'row': 0, 'frames': 1, 'fps': 5,
            'scale': 0.25 * SCALE_MULTIPLIER
        },
        'walk_down': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_down.png'),
            'frame_width': 270,
            'frame_height': 540,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25 * SCALE_MULTIPLIER
        },
        'walk_left': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_right.png'),
            'frame_width': 270,
            'frame_height': 528,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25 * SCALE_MULTIPLIER,
            'allow_flip': True
        },
        'walk_right': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_right.png'),
            'frame_width': 270,
            'frame_height': 528,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25 * SCALE_MULTIPLIER,
            'allow_flip': True
        },
        'walk_up': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_up.png'),
            'frame_width': 270,
            'frame_height': 534,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25 * SCALE_MULTIPLIER
        },
        'cast_down': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'cast_down.png'),
            'frame_width': 270,
            'frame_height': 534,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25 * SCALE_MULTIPLIER
        },
        'cast_left': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'cast_right.png'),
            'frame_width': 280,
            'frame_height': 534,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25 * SCALE_MULTIPLIER,
            'allow_flip': True
        },
        'cast_right': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'cast_right.png'),
            'frame_width': 280,
            'frame_height': 534,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25 * SCALE_MULTIPLIER
        },
        'cast_up': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_up.png'),
            'frame_width': 270,
            'frame_height': 534,
            'row': 0, 'frames': 4, 'fps': 5,
            'scale': 0.25 * SCALE_MULTIPLIER
        },
        'death': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'walking_down.png'),
            'frame_width': 270,
            'frame_height': 540,
            'row': 0, 'frames': 1, 'fps': 5,
            'scale': 0.25 * SCALE_MULTIPLIER,
            'loop': False
        },
        'block': {
            'path': os.path.join(SPRITES_DIR, 'characters', 'player', 'block.png'),
            'frame_width': 270,
            'frame_height': 258,
            'row': 0, 'frames': 4, 'fps': 10,
            'rows': 2,  # 2 rows of 4 frames = 8 frames total
            'scale': 0.39 * SCALE_MULTIPLIER,
            'loop': False,
            'frame_durations': [0.075, 0.075, 0.5, 0.5, 0.075, 0.075, 0.075, 0.075],
        },
    }
}

SLIME_SPRITE_CONFIG = {
    'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'),
    'frame_width': 32,
    'frame_height': 32,
    'animations': {
        'idle_front': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 0, 'frames': 4, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
        'idle_side': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 1, 'frames': 4, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
        'idle_back': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 2, 'frames': 4, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
        'walk_front': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 3, 'frames': 6, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
        'walk_side': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 4, 'frames': 6, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
        'walk_back': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 5, 'frames': 6, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
        'attack_front': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 6, 'frames': 4, 'fps': 8, 'scale': 2.0 * SCALE_MULTIPLIER},
        'attack_side': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 7, 'frames': 4, 'fps': 8, 'scale': 2.0 * SCALE_MULTIPLIER},
        'attack_back': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 8, 'frames': 4, 'fps': 8, 'scale': 2.0 * SCALE_MULTIPLIER},
        'damaged_front': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 9, 'frames': 3, 'fps': 8, 'scale': 2.0 * SCALE_MULTIPLIER},
        'damaged_side': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 10, 'frames': 3, 'fps': 8, 'scale': 2.0 * SCALE_MULTIPLIER},
        'damaged_back': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 11, 'frames': 3, 'fps': 8, 'scale': 2.0 * SCALE_MULTIPLIER},
        'death': {'path': os.path.join(SPRITES_DIR, 'characters', 'slime.png'), 'frame_width': 32, 'frame_height': 32, 'row': 12, 'frames': 5, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
    }
}

# Skeleton enemy - 48x48 grid, 6 cols x 13 rows (288x624)
SKELETON_SPRITE_CONFIG = {
    'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'),
    'frame_width': 48,
    'frame_height': 48,
    'animations': {
        'idle_front': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 0, 'frames': 6, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
        'idle_side': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 1, 'frames': 6, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
        'idle_back': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 2, 'frames': 6, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
        'walk_front': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 3, 'frames': 6, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
        'walk_side': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 4, 'frames': 6, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
        'walk_back': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 5, 'frames': 6, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
        'attack_front': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 6, 'frames': 4, 'fps': 8, 'scale': 2.0 * SCALE_MULTIPLIER},
        'attack_side': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 7, 'frames': 4, 'fps': 8, 'scale': 2.0 * SCALE_MULTIPLIER},
        'attack_back': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 8, 'frames': 4, 'fps': 8, 'scale': 2.0 * SCALE_MULTIPLIER},
        'damaged_front': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 9, 'frames': 3, 'fps': 8, 'scale': 2.0 * SCALE_MULTIPLIER},
        'damaged_side': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 10, 'frames': 3, 'fps': 8, 'scale': 2.0 * SCALE_MULTIPLIER},
        'damaged_back': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 11, 'frames': 3, 'fps': 8, 'scale': 2.0 * SCALE_MULTIPLIER},
        'death': {'path': os.path.join(SPRITES_DIR, 'characters', 'skeleton.png'), 'row': 12, 'frames': 5, 'fps': 5, 'scale': 2.0 * SCALE_MULTIPLIER},
    }
}

# Lich boss settings
LICH_MAX_HEALTH = 5  # Takes 5 hits to kill
LICH_X_OFFSET = 312  # Stay ~312 pixels to the left of the player (25% further than before)
LICH_SPEED_FACTOR = 0.6  # 60% of player speed
LICH_ATTACK_COOLDOWN_MIN = 3.0  # Min seconds between attacks
LICH_ATTACK_COOLDOWN_MAX = 5.0  # Max seconds between attacks
LICH_LIGHTNING_DAMAGE = 75  # Lightning bolt damage

# Lich sprite directory
_LICH_DIR = os.path.join(SPRITES_DIR, 'monsters', 'Lich', 'Magenta')
_LICH_LIGHTNING_DIR = os.path.join(SPRITES_DIR, 'monsters', 'Lich', 'Lightning')

# All lich frames are 176x128, scaled to 1.5x (264x192)
LICH_SPRITE_CONFIG = {
    'path': os.path.join(_LICH_DIR, 'Lich_magenta_idle.png'),
    'frame_width': 176,
    'frame_height': 128,
    'animations': {
        # Idle: 2 rows x 8 cols = 16 frames
        'idle': {
            'path': os.path.join(_LICH_DIR, 'Lich_magenta_idle.png'),
            'frame_width': 176, 'frame_height': 128,
            'row': 0, 'frames': 8, 'rows': 2, 'fps': 8,
            'scale': 1.5 * SCALE_MULTIPLIER,
        },
        # Casting (summon skeletons): 4 rows; rows 0-2 have 7 valid frames, row 3 has 8
        # We load all 8 per row (32 total) and skip blank frames in code
        'casting': {
            'path': os.path.join(_LICH_DIR, 'Lich_magenta_casting.png'),
            'frame_width': 176, 'frame_height': 128,
            'row': 0, 'frames': 8, 'rows': 4, 'fps': 12,
            'scale': 1.5 * SCALE_MULTIPLIER, 'loop': False,
        },
        # Third attack (lightning): 2 rows x 8 cols = 16 frames
        'third_attack': {
            'path': os.path.join(_LICH_DIR, 'Lich_magenta_third_attack.png'),
            'frame_width': 176, 'frame_height': 128,
            'row': 0, 'frames': 8, 'rows': 2, 'fps': 12,
            'scale': 1.5 * SCALE_MULTIPLIER, 'loop': False,
        },
        # Long spin attack (block/defense): 4 rows x 8 cols = 32 frames
        'long_spin_attack': {
            'path': os.path.join(_LICH_DIR, 'Lich_magenta_long_spin_attack.png'),
            'frame_width': 176, 'frame_height': 128,
            'row': 0, 'frames': 8, 'rows': 4, 'fps': 12,
            'scale': 1.5 * SCALE_MULTIPLIER, 'loop': False,
        },
        'long_spin_ghosts': {
            'path': os.path.join(_LICH_DIR, 'Lich_magenta_long_spin_with_ghosts_attack.png'),
            'frame_width': 176, 'frame_height': 128,
            'row': 0, 'frames': 8, 'rows': 4, 'fps': 12,
            'scale': 1.5 * SCALE_MULTIPLIER, 'loop': False,
        },
        'long_spin_symbols': {
            'path': os.path.join(_LICH_DIR, 'Lich_magenta_long_spin_with_symbols_attack.png'),
            'frame_width': 176, 'frame_height': 128,
            'row': 0, 'frames': 8, 'rows': 4, 'fps': 12,
            'scale': 1.5 * SCALE_MULTIPLIER, 'loop': False,
        },
        # Hurt: 1 row x 2 cols = 2 frames
        'hurt': {
            'path': os.path.join(_LICH_DIR, 'Lich_magenta_hurt.png'),
            'frame_width': 176, 'frame_height': 128,
            'row': 0, 'frames': 2, 'fps': 6,
            'scale': 1.5 * SCALE_MULTIPLIER, 'loop': False,
        },
        # Death: 2 rows x 6 cols = 12 frames
        'death': {
            'path': os.path.join(_LICH_DIR, 'Lich_magenta_death.png'),
            'frame_width': 176, 'frame_height': 128,
            'row': 0, 'frames': 6, 'rows': 2, 'fps': 8,
            'scale': 1.5 * SCALE_MULTIPLIER, 'loop': False,
        },
    }
}

# Lightning projectile: 8 cols at 32x32, use rows 0-4 (5 rows of content, skip blank row 5+)
LICH_LIGHTNING_CONFIG = {
    'path': os.path.join(_LICH_LIGHTNING_DIR, 'Lightning_magenta-Sheet.png'),
    'frame_width': 32,
    'frame_height': 32,
    'animations': {
        'lightning': {
            'path': os.path.join(_LICH_LIGHTNING_DIR, 'Lightning_magenta-Sheet.png'),
            'frame_width': 32, 'frame_height': 32,
            'row': 0, 'frames': 8, 'rows': 5, 'fps': 14,
            'scale': 2.0 * SCALE_MULTIPLIER,
        },
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

# NPC settings
NPC_INTERACTION_RADIUS = 80     # pixels - auto-show panel when player is within this distance
NPC_SPRITE_CONFIG = {
    'path': os.path.join(SPRITES_DIR, 'characters', 'mage_guardian.png'),
    'frame_width': 64,
    'frame_height': 64,
    'scale': 2.0 * SCALE_MULTIPLIER,
    'animations': {
        'idle': {
            'row': 0, 'frames': 14, 'fps': 8,
            'path': os.path.join(SPRITES_DIR, 'characters', 'mage_guardian.png'),
            'frame_width': 64,
            'frame_height': 64,
            'scale': 2.0 * SCALE_MULTIPLIER,
        },
    }
}
