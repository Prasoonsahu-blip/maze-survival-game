"""
Game constants, color palettes, and configurations.
"""

# Window and Grid Dimensions
GRID_ROWS = 23
GRID_COLS = 31
CELL_SIZE = 28  # Pixels per cell

CANVAS_WIDTH = GRID_COLS * CELL_SIZE  # 868px
CANVAS_HEIGHT = GRID_ROWS * CELL_SIZE  # 644px
HUD_HEIGHT = 86  # Top HUD bar height
TOTAL_WIDTH = CANVAS_WIDTH
TOTAL_HEIGHT = CANVAS_HEIGHT + HUD_HEIGHT

# Frame rate
FPS = 60
FRAME_DELAY_MS = int(1000 / FPS)  # ~16ms

# Color Palette (Cyberpunk / Modern Dark Arcade)
COLOR_BG = "#0c1017"              # Deep dark background
COLOR_CANVAS_BG = "#090d13"       # Maze canvas background
COLOR_WALL = "#1e293b"            # Maze wall fill
COLOR_WALL_BORDER = "#334155"     # Wall outline
COLOR_WALL_ACCENT = "#38bdf8"     # Subtle wall glow accent
COLOR_PATH = "#0f172a"            # Open corridor floor
COLOR_PATH_DOT = "#1e293b"        # Subtle floor grid dot

# Entity Colors
COLOR_PLAYER = "#22c55e"          # Vibrant Neon Green
COLOR_PLAYER_GLOW = "#15803d"     # Green glow
COLOR_PLAYER_EYE = "#ffffff"

# Killer 1: The Stalker (Relentless direct chaser)
COLOR_KILLER_STALKER = "#ef4444"       # Neon Red
COLOR_KILLER_STALKER_GLOW = "#991b1b"

# Killer 2: The Phantom (Flanker / Interceptor)
COLOR_KILLER_PHANTOM = "#a855f7"       # Phantom Purple
COLOR_KILLER_PHANTOM_GLOW = "#6b21a8"

# Killer 3: The Beast (Patroller & Line-of-sight Sprinter)
COLOR_KILLER_BEAST = "#f97316"         # Blaze Orange
COLOR_KILLER_BEAST_GLOW = "#c2410c"
COLOR_KILLER_BEAST_ENRAGED = "#ff0055" # Crimson sprint

# HUD & UI Colors
COLOR_HUD_BG = "#0f172a"
COLOR_HUD_BORDER = "#1e293b"
COLOR_TEXT_PRIMARY = "#f8fafc"
COLOR_TEXT_SECONDARY = "#94a3b8"
COLOR_ACCENT_CYAN = "#06b6d4"
COLOR_ACCENT_GOLD = "#eab308"
COLOR_ACCENT_RED = "#f43f5e"

# Power-up Colors
COLOR_ITEM_EMP = "#06b6d4"        # Cyan EMP Orb
COLOR_ITEM_SPEED = "#eab308"      # Golden Speed Bolt
COLOR_ITEM_GEM = "#ec4899"        # Pink Score Gem
COLOR_ITEM_SHIELD = "#3b82f6"     # Blue Shield Barrier

# Game Balance
BASE_POINTS_PER_SEC = 100
MAX_MULTIPLIER = 3.0
MIN_MULTIPLIER = 0.5
MULTIPLIER_INC_RATE = 0.15        # Gain per sec of active moving
MULTIPLIER_DEC_RATE = 0.40        # Loss per sec of standing still
IDLE_THRESHOLD_SEC = 2.5          # Standing still warning time

# Killer Speeds (movement interval in milliseconds; lower = faster)
KILLER_SPEED_NORMAL = 280         # Base killer step interval
KILLER_SPEED_PHANTOM = 300
KILLER_SPEED_BEAST_PATROL = 340
KILLER_SPEED_BEAST_SPRINT = 170   # When chasing in line-of-sight
KILLER_SPEED_MIN_CAP = 150        # Absolute maximum speed limit

# Player Speeds
PLAYER_BASE_SPEED_MS = 110        # Player step interval (smooth snappy)
PLAYER_DASH_SPEED_MS = 60         # During sprint/dash
TURN_BUFFER_SEC = 0.15           # How long a tapped turn is remembered (one-shot)
DASH_DURATION_SEC = 2.0
DASH_COOLDOWN_SEC = 6.0
EMP_STUN_DURATION_SEC = 3.5

# High Score File
HIGHSCORE_FILE = "maze_survival_highscore.json"
