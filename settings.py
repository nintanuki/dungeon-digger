# Keep shared configuration grouped in namespaced classes for predictable imports.
import os

class ColorSettings:
    """Centralized named colors used throughout UI and gameplay rendering."""

    # Base color names
    WHITE = 'white'
    BLACK = 'black'
    YELLOW = 'yellow'
    RED = 'red'
    GREEN = 'green'
    BLUE = 'blue'
    CYAN = 'cyan'
    PURPLE = 'purple'
    GOLD = 'gold'
    DODGER_BLUE = 'dodgerblue'
    TAN = 'tan'
    FIREBRICK = 'firebrick'
    LIME_GREEN = 'limegreen'
    ORCHID = 'orchid'
    MEDIUM_ORCHID = 'mediumorchid'
    PLUM = 'plum'
    DARK_GRAY = 'darkgray'
    DIM_GRAY = 'dimgray'
    SADDLE_BROWN = 'saddlebrown'
    SLATE_GRAY = 'slategray'

    SCREEN_BACKGROUND = BLACK
    GRID_OUTLINE = BLACK

    TEXT_DEFAULT = WHITE
    TEXT_ACTIVE_MESSAGE = YELLOW
    TEXT_TITLE = YELLOW
    TEXT_PROMPT = CYAN
    TEXT_GOLD = GOLD
    TEXT_WIN = GREEN
    TEXT_LOSS = RED
    TEXT_CONTINUE = CYAN
    TEXT_ERROR = RED
    TEXT_SELECTOR = YELLOW

    TREASURE_RUBY = RED
    TREASURE_SAPPHIRE = DODGER_BLUE
    TREASURE_EMERALD = GREEN
    TREASURE_DIAMOND = CYAN

    BORDER_DEFAULT = WHITE
    BORDER_KEY_ACTIVE = GOLD
    BORDER_MAP_ACTIVE = GOLD
    BORDER_MESSAGE_SUCCESS = LIME_GREEN
    BORDER_MESSAGE_FAILURE = FIREBRICK
    BORDER_REPELLED = MEDIUM_ORCHID

    MINIMAP_WALL = DARK_GRAY
    MINIMAP_DUG = SADDLE_BROWN
    MINIMAP_FLOOR = SADDLE_BROWN
    MINIMAP_DOOR = YELLOW
    MINIMAP_MONSTER = RED
    MINIMAP_PLAYER = BLUE

    OVERLAY_BACKGROUND = BLACK
    LIGHT_MASK = WHITE

    CLOAK_GLOW_MIN = ORCHID
    CLOAK_GLOW_MAX = PLUM
    REPELLED_TINT = PURPLE

    MESSAGE_CONTROL_X = DODGER_BLUE
    MESSAGE_CONTROL_Y = YELLOW
    MESSAGE_CONTROL_B = RED
    MESSAGE_CONTROL_A = GREEN
    MESSAGE_DOOR = TAN

class ScreenSettings:
    """Class to hold all the settings related to the screen."""
    WIDTH = 800
    HEIGHT = 600
    RESOLUTION = (WIDTH,HEIGHT)
    FPS = 60
    CRT_ALPHA_RANGE = (75, 90)
    CRT_SCANLINE_HEIGHT = 3
    TITLE = "Dungeon Digger"

class GridSettings:
    """Grid and tile scaling values used for map layout and sprite snapping."""

    RAW_TILE_SIZE = 16 # Source tile size in pixels.
    SCALE_FACTOR = 2 # Render scale multiplier applied to source tiles.
    TILE_SIZE = RAW_TILE_SIZE * SCALE_FACTOR # Effective in-game tile size.

class UISettings:
    """Layout coordinates and dimensions for game windows and HUD elements."""

    LEFT_MARGIN = 64
    TOP_MARGIN = 56
    GAP = GridSettings.TILE_SIZE

    BORDER_COLOR = ColorSettings.BORDER_DEFAULT
    BORDER_RADIUS = 5
    DOOR_UNLOCK_BORDER_FLASH_MS = 2500

    SIDEBAR_WIDTH = 200
    BOTTOM_LOG_HEIGHT = 150

    COLS = 14
    ROWS = 10
    ACTION_WINDOW_WIDTH = COLS * GridSettings.TILE_SIZE
    ACTION_WINDOW_HEIGHT = ROWS * GridSettings.TILE_SIZE

    ACTION_WINDOW_X = LEFT_MARGIN
    ACTION_WINDOW_Y = TOP_MARGIN

    SIDEBAR_X = ACTION_WINDOW_X + ACTION_WINDOW_WIDTH + GAP
    SIDEBAR_Y = TOP_MARGIN
    SIDEBAR_HEIGHT = ACTION_WINDOW_HEIGHT

    LOG_X = LEFT_MARGIN
    LOG_Y = ACTION_WINDOW_Y + ACTION_WINDOW_HEIGHT + GAP
    LOG_WIDTH = ACTION_WINDOW_WIDTH
    LOG_HEIGHT = BOTTOM_LOG_HEIGHT

    MAP_X = SIDEBAR_X
    MAP_Y = LOG_Y
    MAP_WIDTH = SIDEBAR_WIDTH
    MAP_HEIGHT = BOTTOM_LOG_HEIGHT
    MINIMAP_PADDING = 10

    SCORE_X = 72
    SCORE_Y = 20
    CURRENT_SCORE_X = SIDEBAR_X + 16
    CURRENT_SCORE_Y = SCORE_Y
    LEVEL_X = LEFT_MARGIN
    LEVEL_Y = ScreenSettings.HEIGHT - 34
    DUNGEON_NAME_Y = LEVEL_Y + 15

    # AUDIO MUTED indicator anchored to the top-right of the action window,
    # opposite the HIGH SCORE label. Used as a topright anchor when blitting.
    MUTE_RIGHT_X = ACTION_WINDOW_X + ACTION_WINDOW_WIDTH
    MUTE_Y = SCORE_Y

class RenderSettings:
    """Constants for title, overlay, and between-screen render timing/layout."""

    IN_GAME_TITLE = ScreenSettings.TITLE.upper()

    TITLE_CHASE_INITIAL_DELAY_MS = 60000
    TITLE_CHASE_COOLDOWN_MS = 60000
    TITLE_CHASE_DURATION_MS = 2400
    TITLE_CHASE_SPRITE_OFFSET_Y = -96
    TITLE_CHASE_SPRITE_SPACING = 42

    ENDGAME_OVERLAY_ALPHA = 180
    ENDGAME_PROMPT_OFFSET_Y = 42

    TREASURE_OVERLAY_ALPHA = 200
    TREASURE_START_X = 20
    TREASURE_START_Y = 20
    TREASURE_LINE_HEIGHT = 22
    TREASURE_TITLE_GAP = 16
    TREASURE_TOTAL_GAP = 5
    TREASURE_PROMPT_BOTTOM_PADDING = 18

    SHOP_OVERLAY_ALPHA = 210
    SHOP_START_X = 20
    SHOP_START_Y = 20
    SHOP_LINE_HEIGHT = 22
    SHOP_TITLE_GAP = 16
    SHOP_GOLD_GAP = 6
    SHOP_SELECTOR_OFFSET_X = 12

    INITIALS_TITLE_Y = 160
    INITIALS_INVITE_Y = 240
    INITIALS_SCORE_Y = 268
    INITIALS_CHARS_Y = 295
    INITIALS_HELP_Y = 430

    LEADERBOARD_TITLE_Y = 80
    LEADERBOARD_START_Y = 140
    LEADERBOARD_ROW_HEIGHT = 34
    LEADERBOARD_RANK_X_OFFSET = -145
    LEADERBOARD_SCORE_X_OFFSET = 60
    LEADERBOARD_EMPTY_Y = 260
    LEADERBOARD_PROMPT_Y_OFFSET = 60

    # Slot select layout (NEW GAME / LOAD GAME). Ten rows of slot summary
    # land between the header and the bottom prompt. The cursor X offset
    # positions the ">" indicator a few pixels left of the row text.
    SLOT_SELECT_TITLE_Y = 50
    SLOT_SELECT_START_Y = 110
    SLOT_SELECT_ROW_HEIGHT = 36
    SLOT_SELECT_ROW_X = 120
    SLOT_SELECT_CURSOR_OFFSET_X = -20
    SLOT_SELECT_PROMPT_Y_OFFSET = 35

    # Name entry, overwrite confirm, and delete confirm share a centered
    # layout pattern: a header, a contextual line, a focal element (the
    # typed name buffer or NO/YES options), and a bottom controls hint.
    SAVE_DIALOG_TITLE_Y = 150
    SAVE_DIALOG_BODY_Y = 230
    SAVE_DIALOG_FOCAL_Y = 320
    SAVE_DIALOG_PROMPT_Y_OFFSET = 50
    SAVE_DIALOG_OPTION_GAP = 100

class GameSettings:
    """Global gameplay flow constants and persistence limits."""

    LEVEL_TRANSITION_MS = 2000
    LEADERBOARD_FILE = 'leaderboard.txt'
    LEADERBOARD_LIMIT = 10

    # Save system: ten slots, JSON files under saves/. SAVE_VERSION exists so
    # SaveManager can reject or migrate older save files if the schema ever
    # changes incompatibly.
    SAVES_DIR = 'saves'
    SAVE_VERSION = 1
    MAX_SAVE_SLOTS = 10
    MAX_PLAYER_NAME_LENGTH = 8
    GAME_OVER_CONTINUE_DELAY_MS = 650
    GAME_OVER_PROMPT_FADE_MS = 750
    DOOR_UNLOCK_MESSAGE_TYPE_SPEED = 0.12

    TREASURE_CONVERSION_DISPLAY_DELAY_MS = 2000
    TREASURE_CONVERSION_LINE_REVEAL_INTERVAL_MS = 520
    TREASURE_CONVERSION_TOTAL_REVEAL_DELAY_MS = 450
    TREASURE_CONVERSION_PROMPT_FADE_MS = 650
    TREASURE_CONVERSION_POST_MESSAGE_DELAY_MS = 450

    SHOP_DISPLAY_DELAY_MS = 200
    STATUS_EFFECT_TURN_BUFFER = 1

class WindowSettings:
    """Message window behavior and text layout settings."""

    MAX_MESSAGES = 5
    LINE_HEIGHT = 22
    TEXT_PADDING = 16
    WELCOME_MESSAGE = [
        "IT'S PITCH BLACK",
        "YOU CAN'T SEE A THING",
        "MAYBE YOU SHOULD LIGHT A TORCH?",
        "(B BUTTON ON CONTROLLER / F ON KEYBOARD)"]
    TYPING_SPEED = 0.25 # Characters advanced per frame in typewriter animation.

class TutorialSettings:
    """Layout, timing, and copy values for the tutorial card overlay."""

    # Anti-mash window: same key that just dismissed a card cannot also dig
    # on the same press.
    DISMISS_DELAY_MS = 500
    # Number of full turns to wait between flow-queue cards so they don't all
    # fire on a single dig.
    FLOW_CARD_TURN_GAP = 2

    # Darken the action window behind the card so text reads cleanly.
    WORLD_DARKEN_ALPHA = 170
    # Card panel background opacity.
    PANEL_ALPHA = 220
    PANEL_BORDER_RADIUS = 8
    PANEL_PADDING_X = 24
    PANEL_PADDING_Y = 18

    TEXT_LINE_GAP = 10
    PROMPT_GAP = 14
    PROMPT_TEXT = "PRESS A OR SPACE TO CONTINUE"
    BODY_FONT_SIZE = 14
    # The dismiss prompt reuses FontSettings.MESSAGE_SIZE directly at the
    # call site so HUD text stays one source of truth.

class PlayerSettings:
    """Player-specific tuning values."""

    ANIMATION_SPEED = 1 # Pixels advanced per frame during sprite interpolation.
    FLASH_CYCLE_FRAMES = 30
    FLASH_HALF_CYCLE = FLASH_CYCLE_FRAMES // 2

    # Idle "look around" animation: after staying still this long, the player
    # cycles through the sequence below holding each frame for FRAME_MS.
    IDLE_ANIMATION_DELAY_MS = 10000
    IDLE_ANIMATION_FRAME_MS = 200
    # 'center' uses the neutral facing sprite; 'left'/'right' use the peek variants.
    IDLE_ANIMATION_SEQUENCE = (
        'center', 'left', 'center', 'right', 'center',
    )

class MonsterSettings:
    """Monster behavior and movement tuning values."""

    COUNT = 3
    # HEARING_RADIUS replaces the legacy CHASE_RADIUS. The chase trigger
    # now keys off the player's light_radius (light = danger), so this
    # value is reused for a different role: the Manhattan bubble inside
    # which a monster can sense the player even in pitch darkness and
    # emit a one-shot "you hear something" warning. Kept separate from
    # light_radius so the dark warning range can be tuned without
    # touching how far light reaches.
    HEARING_RADIUS = 3  # Manhattan distance
    IDLE_CHANCE = 0.3
    MIN_PLAYER_DISTANCE = 5  # Minimum Manhattan distance between a monster and the player at spawn.
    REPELLENT_DURATION = 5 # Number of turns the repellent effect remains active.
    ANIMATION_SPEED = 1 # Pixels advanced per frame during sprite interpolation.

class InputSettings:
    """Controller button and axis mappings used by gameplay and menus.

    Constants are named after the physical button on the controller, not the
    action it performs. The only exception is JOY_BUTTON_QUIT_COMBO, which is
    a special multi-button chord rather than a single button.
    """

    JOY_BUTTON_A = 0
    JOY_BUTTON_B = 1
    JOY_BUTTON_X = 2
    JOY_BUTTON_Y = 3
    JOY_BUTTON_L1 = 4
    JOY_BUTTON_R1 = 5
    JOY_BUTTON_BACK = 6
    JOY_BUTTON_START = 7
    JOY_BUTTON_QUIT_COMBO = (7, 6, 4, 5)

    JOY_AXIS_LEFT_X = 0
    JOY_AXIS_LEFT_Y = 1
    JOY_AXIS_L2 = 4
    JOY_AXIS_R2 = 5
    JOY_TRIGGER_THRESHOLD = 0.5

class NPCSettings:
    """NPC spawn tuning values."""

    MAX_COUNT = 2
    SPAWN_CHANCE = 0.1  # Probability for each potential NPC slot to actually spawn.
    FADE_SPEED = 1       # Alpha units subtracted per frame during fade-out (~255 frames = ~4s at 60fps).

class LightSettings:
    """Lighting radius and duration values for consumable light sources."""

    DEFAULT_RADIUS = 0    # Start each run with no active light source.
    BASE_RADIUS = 2
    BASE_DURATION = 3

    MATCH_RADIUS = BASE_RADIUS * 1
    MATCH_DURATION = BASE_DURATION * 1

    TORCH_RADIUS = BASE_RADIUS * 1.5
    TORCH_DURATION = BASE_DURATION * 1.5

    LANTERN_RADIUS = BASE_RADIUS * 3
    LANTERN_DURATION = BASE_DURATION * 3

    # Best-first order used to auto-pick a default light source after pickups.
    SOURCE_PRIORITY = ('LANTERN', 'TORCH', 'MATCH')
    # Cycle order for L1/R1 (and Q/E) so the player walks weakest-to-strongest.
    SOURCE_CYCLE_ORDER = ('MATCH', 'TORCH', 'LANTERN')
    # (radius, duration) per source. Mirrors the *_RADIUS/_DURATION pairs above
    # so Player.process_turn_action can look both up with one dict access.
    SOURCE_STATS = {
        'MATCH': (MATCH_RADIUS, MATCH_DURATION),
        'TORCH': (TORCH_RADIUS, TORCH_DURATION),
        'LANTERN': (LANTERN_RADIUS, LANTERN_DURATION),
    }

class ItemSettings:
    """Item inventory, spawn, scoring, and shop economy configuration."""

    INVISIBILITY_CLOAK_DURATION = 5
    INVISIBILITY_CLOAK_COOLDOWN = 3
    LEVEL_SCOPED_ITEMS = {"KEY", "MAP", "MAGIC MAP", "KEY DETECTOR"}

    TREASURE_SCORE_VALUES = {
        'GOLD COINS': 1,
        'RUBY': 50,
        'SAPPHIRE': 100,
        'EMERALD': 200,
        'DIAMOND': 500
    }

    SHOP_PRICES = {
        'MATCH': 100,
        'TORCH': 250,
        'LANTERN': 1000,
        'MONSTER REPELLENT': 500,
        'KEY DETECTOR': 2000,
        'MAP': 5000,
        'INVISIBILITY CLOAK': 25000,
    }

    # Only the invisibility cloak is limited stock (one per shop visit, and
    # zero if the player already owns one). Every other item is unlimited.
    SHOP_LIMITED_STOCK_TEMPLATE = {
        'INVISIBILITY CLOAK': 1,
    }

    DETECTOR_DISTANCE_FOUND = 0
    DETECTOR_DISTANCE_HOT = 1
    DETECTOR_DISTANCE_STEADY = 3
    DETECTOR_DISTANCE_SLOW = 5
    DETECTOR_DISTANCE_FAINT = 7

    # Digging probabilities (must be between 0.0 and 1.0)
    # The higher the number, the more common it is.
    SPAWN_CHANCE = {
        # Consumables
        'MATCH': 0.20,
        'TORCH': 0.10,
        'LANTERN': 0.05,
        'MONSTER REPELLENT': 0.10,
        'INVISIBILITY SCROLL': 0.01,
        
        # Treasure
        'GOLD COINS': 0.20,
        'RUBY': 0.15,
        'SAPPHIRE': 0.10,
        'EMERALD': 0.05,
        'DIAMOND': 0.01,

        # Unique
        'KEY DETECTOR': 0.05,
        'MAGIC MAP': 0.01,
    }

    SPAWN_QUANTITIES = {
        'GOLD COINS': (1, 200),
        'RUBY': (1, 7),
        'SAPPHIRE': (1, 5),
        'EMERALD': (1, 3),
        # Items not listed here default to quantity 1.
        # Note: add BOOK OF MATCHES (20) for a rare 5% drop
    }

    NORMAL_INITIAL_INVENTORY = {
        'TORCH': 1,
    }

    TEST_INITIAL_INVENTORY = {
        'INVISIBILITY CLOAK': 1,
        'KEY': 1,
        'MAGIC MAP': 1,
        'LANTERN': 99,
    }

    INITIAL_INVENTORY = NORMAL_INITIAL_INVENTORY.copy()

class FontSettings:
    """Font files, sizes, and text-color mappings for UI rendering."""

    # Absolute path so pygame.font.Font(...) works no matter what the
    # caller's working directory is. assets/ now owns every bundled media
    # folder (font, graphics, music, sound).
    FONT = os.path.join(
        os.path.dirname(__file__), 'assets', 'font', 'Pixeled.ttf'
    )
    MESSAGE_SIZE = 8
    SCORE_SIZE = 12
    HUD_SIZE = 10
    ENDGAME_SIZE = 32
    DEFAULT_COLOR = ColorSettings.TEXT_DEFAULT
    LAST_MESSAGE_COLOR = ColorSettings.TEXT_ACTIVE_MESSAGE

    WORD_COLORS = {
        "RUBY": ColorSettings.TREASURE_RUBY,
        "SAPPHIRE": ColorSettings.BLUE,
        "EMERALD": ColorSettings.TREASURE_EMERALD,
        "KEY": ColorSettings.YELLOW,
        "MONSTER": ColorSettings.PURPLE,
        "MONSTER REPELLENT": ColorSettings.PURPLE
    }

class AudioSettings:
    """Global audio toggles and mixer-level defaults."""

    MUTE = False
    MUTE_MUSIC = False  # Keep music disabled while retaining sound effects.
    MUSIC_VOLUME = 1  # Background music volume in the range [0.0, 1.0].

class AssetPaths:
    """Resolved asset paths for sprites, audio, and music content."""

    # All bundled media now lives under a single assets/ folder
    # (assets/font, assets/graphics, assets/music, assets/sound) so the
    # project root only carries code + docs + saves. BASE_DIR still resolves
    # to the project root because settings.py itself stays at the root.
    BASE_DIR = os.path.dirname(__file__)
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

    # Images
    GRAPHICS_DIR = os.path.join(ASSETS_DIR, 'graphics')
    MONSTER_VARIANTS_DIR = os.path.join(GRAPHICS_DIR, 'monsters')
    PLAYER_VARIANTS_DIR = os.path.join(GRAPHICS_DIR, 'player')
    NPC_VARIANTS_DIR = os.path.join(GRAPHICS_DIR, 'npcs')
    TILES_DIR = os.path.join(GRAPHICS_DIR, 'tiles')
    EFFECTS_DIR = os.path.join(GRAPHICS_DIR, 'effects')

    # Player sprites keyed by (helmet_state, facing, peek). helmet_state values:
    # 'up' (default), 'down' (cloak/repelled visual), 'off' (reserved for
    # future use). facing values: 'left' or 'right' based on the player's
    # last horizontal movement. peek values: 'center' (neutral), 'left',
    # or 'right' — only the helmet-up sprite has non-center peek frames,
    # which drive the idle "look around" animation.
    PLAYER_SPRITES = {
        ('up', 'right', 'center'): os.path.join(PLAYER_VARIANTS_DIR, 'player_helmet_up_right.png'),
        ('up', 'left', 'center'):  os.path.join(PLAYER_VARIANTS_DIR, 'player_helmet_up_left.png'),
        ('up', 'right', 'left'):   os.path.join(PLAYER_VARIANTS_DIR, 'player_helmet_up_right_looking_left.png'),
        ('up', 'right', 'right'):  os.path.join(PLAYER_VARIANTS_DIR, 'player_helmet_up_right_looking_right.png'),
        ('up', 'left', 'left'):    os.path.join(PLAYER_VARIANTS_DIR, 'player_helmet_up_left_looking_left.png'),
        ('up', 'left', 'right'):   os.path.join(PLAYER_VARIANTS_DIR, 'player_helmet_up_left_looking_right.png'),
        ('down', 'right', 'center'): os.path.join(PLAYER_VARIANTS_DIR, 'player_helmet_down_right.png'),
        ('down', 'left', 'center'):  os.path.join(PLAYER_VARIANTS_DIR, 'player_helmet_down_left.png'),
        ('off', 'right', 'center'):  os.path.join(PLAYER_VARIANTS_DIR, 'player_helmet_off_right.png'),
        ('off', 'left', 'center'):   os.path.join(PLAYER_VARIANTS_DIR, 'player_helmet_off_left.png'),
    }

    # Convenience aliases used by the title/intro screens, which want a
    # single canonical sprite rather than a state-based lookup.
    PLAYER = PLAYER_SPRITES[('up', 'right', 'center')]
    MONSTER = os.path.join(MONSTER_VARIANTS_DIR, 'ghost_right.png')

    # Door
    CLOSED_DOOR = os.path.join(TILES_DIR, 'closed_door.png')
    OPEN_DOOR = os.path.join(TILES_DIR, 'open_door.png')

    # Keep as a list to support future dirt-tile variety.
    DIRT_TILES = [
        os.path.join(TILES_DIR, 'dirt.png'),
    ]

    DUG_TILE = os.path.join(TILES_DIR, 'dug_dirt.png')
    WALL_TILE = os.path.join(TILES_DIR, 'wall.png')
    # Reserved for future use; not currently rendered anywhere.
    GRAVEL_TILE = os.path.join(TILES_DIR, 'gravel.png')

    # CRT Effect
    TV = os.path.join(EFFECTS_DIR, 'tv.png')

    # Audio
    SOUND_DIR = os.path.join(ASSETS_DIR, 'sound')
    MOVE_SOUND = os.path.join(SOUND_DIR, 'sfx_movement_footstepsloop4_slow.ogg')
    DIG_SOUND = os.path.join(SOUND_DIR, 'dig_sound_effect.ogg')
    BOUNDARY_SOUND = os.path.join(SOUND_DIR, 'wall_bump_sound_effect.ogg')
    KEY_SOUND = os.path.join(SOUND_DIR, 'sfx_coin_single1.ogg')
    SCREAM_SOUND = os.path.join(SOUND_DIR, 'wilhelm_scream.ogg')
    MONSTER_CHASE_SOUND = os.path.join(SOUND_DIR, 'sfx_sound_nagger1.ogg')
    COIN_SOUND = os.path.join(SOUND_DIR, 'sfx_coin_cluster3.ogg')
    LIGHT_SOUND = os.path.join(SOUND_DIR, 'Torch Whoosh Sound Effect.ogg')
    MATCH_LIGHT_SOUND = os.path.join(SOUND_DIR, 'Lighting A Match Sound Effect.ogg')
    VANISH_SOUND = os.path.join(SOUND_DIR, 'Vanish Sound Effect.ogg')
    SHORT_SPRAY_SOUND = os.path.join(SOUND_DIR, 'short_spray.ogg')
    LONG_SPRAY_SOUND = os.path.join(SOUND_DIR, 'long_spray.ogg')
    FOUND_DETECTOR_SOUND = os.path.join(SOUND_DIR, 'sfx_alarm_loop3.ogg')
    HOT_DETECTOR_SOUND = os.path.join(SOUND_DIR, 'sfx_alarm_loop7.ogg')
    WARM_DETECTOR_SOUND = os.path.join(SOUND_DIR, 'sfx_alarm_loop6.ogg')
    MENU_MOVE_SOUND = os.path.join(SOUND_DIR, 'sfx_menu_move2.ogg')
    MENU_SELECT_SOUND = os.path.join(SOUND_DIR, 'sfx_menu_select3.ogg')

    # Music
    MUSIC_DIR = os.path.join(ASSETS_DIR, 'music')
    NORMAL_MUSIC_TRACKS = [
        os.path.join(MUSIC_DIR, 'Goblins_Den_(Regular).ogg'),
    ]
    CHASE_MUSIC = os.path.join(MUSIC_DIR, 'Goblins_Dance_(Battle).ogg')
    MUSIC_TRACKS = NORMAL_MUSIC_TRACKS

class DebugSettings:
    """Settings related to debugging features."""
    GRID = True # Draw tile outlines for visual debugging.
    MUTE = False # Force mute all sound output during testing.
    NO_FOG = False # Disable fog rendering for visibility debugging.
    SPAWN_LOG = False # Print spawn/item placement summary during dungeon setup.
    USE_TEST_INITIAL_INVENTORY = False # Start runs with ItemSettings.TEST_INITIAL_INVENTORY when enabled.