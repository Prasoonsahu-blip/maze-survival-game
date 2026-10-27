"""
Core Game Engine and UI for Maze Survival: 3 Killers.
Built with Python's standard Tkinter GUI.
"""

import tkinter as tk
import time
import math
import json
import os
import random
from typing import List, Tuple, Optional

from constants import (
    GRID_ROWS, GRID_COLS, CELL_SIZE, CANVAS_WIDTH, CANVAS_HEIGHT, HUD_HEIGHT,
    TOTAL_WIDTH, TOTAL_HEIGHT, FPS, FRAME_DELAY_MS,
    COLOR_BG, COLOR_CANVAS_BG, COLOR_WALL, COLOR_WALL_BORDER, COLOR_WALL_ACCENT,
    COLOR_PATH, COLOR_PATH_DOT, COLOR_PLAYER, COLOR_PLAYER_GLOW,
    COLOR_KILLER_STALKER, COLOR_KILLER_PHANTOM, COLOR_KILLER_BEAST, COLOR_KILLER_BEAST_ENRAGED,
    COLOR_HUD_BG, COLOR_HUD_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT_CYAN, COLOR_ACCENT_GOLD, COLOR_ACCENT_RED,
    COLOR_ITEM_EMP, COLOR_ITEM_SPEED, COLOR_ITEM_GEM, COLOR_ITEM_SHIELD,
    BASE_POINTS_PER_SEC, MAX_MULTIPLIER, MIN_MULTIPLIER,
    MULTIPLIER_INC_RATE, MULTIPLIER_DEC_RATE, IDLE_THRESHOLD_SEC,
    EMP_STUN_DURATION_SEC, HIGHSCORE_FILE
)
from maze import Maze
from entities import Player, Killer, StalkerKiller, PhantomKiller, BeastKiller
from items import Item, ItemType
from audio import sound_fx


DIR_MAP = {
    "w": (-1, 0), "up": (-1, 0),
    "s": (1, 0),  "down": (1, 0),
    "a": (0, -1), "left": (0, -1),
    "d": (0, 1),  "right": (0, 1),
}


class FloatingText:
    def __init__(self, x: float, y: float, text: str, color: str, duration: float = 1.0):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.duration = duration
        self.born = time.time()

    def is_alive(self) -> bool:
        return (time.time() - self.born) < self.duration

    def get_progress(self) -> float:
        return (time.time() - self.born) / self.duration


class Shockwave:
    def __init__(self, cx: float, cy: float, max_radius: float = 400.0, duration: float = 0.5):
        self.cx = cx
        self.cy = cy
        self.max_radius = max_radius
        self.duration = duration
        self.born = time.time()

    def is_alive(self) -> bool:
        return (time.time() - self.born) < self.duration

    def get_radius(self) -> float:
        p = (time.time() - self.born) / self.duration
        return p * self.max_radius


class MazeSurvivalGame:
    STATE_MENU = "MENU"
    STATE_RULES = "RULES"
    STATE_PLAYING = "PLAYING"
    STATE_PAUSED = "PAUSED"
    STATE_GAMEOVER = "GAMEOVER"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Maze Survival: 3 Killers")
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_BG)

        # Center window on screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = max(10, (screen_w - TOTAL_WIDTH) // 2)
        pos_y = max(10, (screen_h - TOTAL_HEIGHT) // 2 - 20)
        self.root.geometry(f"{TOTAL_WIDTH}x{TOTAL_HEIGHT}+{pos_x}+{pos_y}")

        # High Scores
        self.high_score = 0
        self.best_time = 0.0
        self.load_high_score()

        # Button Rectangles for interactive mouse clicks (x1, y1, x2, y2)
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2
        self.btn_play = (cx - 150, cy + 40, cx + 150, cy + 95)
        self.btn_rules = (cx - 150, cy + 110, cx + 150, cy + 155)
        self.btn_sound = (cx - 100, cy + 175, cx + 100, cy + 210)
        self.btn_rules_back = (cx - 130, cy + 210, cx + 130, cy + 255)
        self.btn_gameover_replay = (cx - 150, cy + 140, cx + 150, cy + 185)
        self.btn_gameover_menu = (cx - 130, cy + 195, cx + 130, cy + 235)

        # Build UI layout
        self._build_ui()

        # Keyboard & Mouse bindings
        self.keys_pressed = set()
        self.dir_key_history: List[str] = []
        self._bind_events()

        # Game State
        self.state = self.STATE_MENU
        self.maze: Optional[Maze] = None
        self.player: Optional[Player] = None
        self.killers: List[Killer] = []
        self.items: List[Item] = []
        self.floating_texts: List[FloatingText] = []
        self.shockwaves: List[Shockwave] = []

        # Gameplay metrics
        self.game_start_time = 0.0
        self.elapsed_time = 0.0
        self.score = 0.0
        self.multiplier = 1.0
        self.last_update_time = time.time()
        self.last_near_miss_time = 0.0
        self.last_item_spawn_time = 0.0
        self.last_heartbeat_time = 0.0
        self.near_misses_count = 0

        # Animation loop
        self.root.after(FRAME_DELAY_MS, self._game_loop)

    def _build_ui(self):
        # Top HUD Canvas
        self.hud_canvas = tk.Canvas(
            self.root,
            width=TOTAL_WIDTH,
            height=HUD_HEIGHT,
            bg=COLOR_HUD_BG,
            highlightthickness=0
        )
        self.hud_canvas.pack(side=tk.TOP, fill=tk.X)

        # Main Maze Game Canvas
        self.canvas = tk.Canvas(
            self.root,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=COLOR_CANVAS_BG,
            highlightthickness=0
        )
        self.canvas.pack(side=tk.TOP)

    def _bind_events(self):
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.root.bind("<FocusOut>", self._on_focus_out)
        self.canvas.bind("<Button-1>", self._on_mouse_click)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_key_press(self, event):
        key = event.keysym.lower()
        is_repeat = key in self.keys_pressed  # OS auto-repeat of a key that is already down
        self.keys_pressed.add(key)

        # Menu controls
        if self.state == self.STATE_MENU:
            if key in ("space", "return"):
                self.start_new_game()
            elif key in ("r", "h"):
                self.state = self.STATE_RULES
            elif key == "m":
                sound_fx.toggle_sound()
            return

        # Rules screen controls
        if self.state == self.STATE_RULES:
            if key in ("escape", "space", "return", "r", "h", "b"):
                self.state = self.STATE_MENU
            return

        # Game Over controls
        if self.state == self.STATE_GAMEOVER:
            if key in ("r", "space", "return"):
                self.start_new_game()
            elif key == "escape":
                self.state = self.STATE_MENU
            return

        # Playing controls
        if key in ("p", "pause"):
            if self.state == self.STATE_PLAYING:
                self.state = self.STATE_PAUSED
            elif self.state == self.STATE_PAUSED:
                self.state = self.STATE_PLAYING
                self.last_update_time = time.time()
            return

        if self.state == self.STATE_PLAYING and self.player:
            # Handle direction keys with priority stack (most recent press = last)
            if key in DIR_MAP:
                if not is_repeat:
                    # Fresh press: becomes top priority and is buffered as a one-shot tap
                    if key in self.dir_key_history:
                        self.dir_key_history.remove(key)
                    self.dir_key_history.append(key)
                    self.player.set_desired_direction(*DIR_MAP[key])
                elif key not in self.dir_key_history:
                    # Key was already down when play began (e.g. held through restart)
                    self.dir_key_history.append(key)
            elif key == "space":
                if self.player.trigger_dash():
                    sound_fx.play_dash()
                    self.add_floating_text(self.player.px, self.player.py - 20, "DASH!", COLOR_ACCENT_GOLD)
            elif key in ("f", "e"):
                self.trigger_emp()
            elif key == "m":
                sound_fx.toggle_sound()

    def _on_key_release(self, event):
        key = event.keysym.lower()
        self.keys_pressed.discard(key)

        # Releasing a direction key stops steering with it. The player finishes the
        # cell it is already crossing and then stops (unless another key is held).
        if key in self.dir_key_history:
            self.dir_key_history.remove(key)

    def _on_focus_out(self, event=None):
        """Window lost focus: key-release events are lost, so drop all held keys."""
        self.keys_pressed.clear()
        self.dir_key_history = []

    def _on_mouse_click(self, event):
        x, y = event.x, event.y

        if self.state == self.STATE_MENU:
            if self._point_in_rect(x, y, self.btn_play):
                self.start_new_game()
            elif self._point_in_rect(x, y, self.btn_rules):
                self.state = self.STATE_RULES
            elif self._point_in_rect(x, y, self.btn_sound):
                sound_fx.toggle_sound()

        elif self.state == self.STATE_RULES:
            if self._point_in_rect(x, y, self.btn_rules_back):
                self.state = self.STATE_MENU

        elif self.state == self.STATE_GAMEOVER:
            if self._point_in_rect(x, y, self.btn_gameover_replay):
                self.start_new_game()
            elif self._point_in_rect(x, y, self.btn_gameover_menu):
                self.state = self.STATE_MENU

    def _on_mouse_move(self, event):
        x, y = event.x, event.y
        hovered = False

        if self.state == self.STATE_MENU:
            hovered = (
                self._point_in_rect(x, y, self.btn_play)
                or self._point_in_rect(x, y, self.btn_rules)
                or self._point_in_rect(x, y, self.btn_sound)
            )
        elif self.state == self.STATE_RULES:
            hovered = self._point_in_rect(x, y, self.btn_rules_back)
        elif self.state == self.STATE_GAMEOVER:
            hovered = (
                self._point_in_rect(x, y, self.btn_gameover_replay)
                or self._point_in_rect(x, y, self.btn_gameover_menu)
            )

        self.canvas.config(cursor="hand2" if hovered else "")

    @staticmethod
    def _point_in_rect(x: int, y: int, rect: Tuple[int, int, int, int]) -> bool:
        x1, y1, x2, y2 = rect
        return x1 <= x <= x2 and y1 <= y <= y2

    def _on_closing(self):
        sound_fx.shutdown()
        self.root.destroy()

    def start_new_game(self):
        """Initializes a new procedural game session."""
        self.maze = Maze(GRID_ROWS, GRID_COLS, loop_factor=0.18)
        self.dir_key_history = []
        
        # Player starts in top-left open area
        player_start = (1, 1)
        self.player = Player(player_start)

        # Spawn 3 killers at distant corners
        killer1_pos = self.maze.get_random_open_cell(min_dist_from=player_start, min_dist=14)
        killer2_pos = self.maze.get_random_open_cell(min_dist_from=player_start, min_dist=16)
        killer3_pos = self.maze.get_random_open_cell(min_dist_from=player_start, min_dist=18)

        self.killers = [
            StalkerKiller(killer1_pos),
            PhantomKiller(killer2_pos),
            BeastKiller(killer3_pos)
        ]

        self.items = []
        self.floating_texts = []
        self.shockwaves = []
        
        # Spawn initial power-ups
        self._spawn_random_item(ItemType.GEM)
        self._spawn_random_item(ItemType.SPEED)

        self.game_start_time = time.time()
        self.elapsed_time = 0.0
        self.score = 0.0
        self.multiplier = 1.0
        self.near_misses_count = 0
        self.last_update_time = time.time()
        self.last_item_spawn_time = time.time()
        self.last_heartbeat_time = time.time()

        self.state = self.STATE_PLAYING
        sound_fx.play_start()

    def _spawn_random_item(self, forced_type: Optional[str] = None):
        if not self.maze or not self.player:
            return
        
        # Don't overcrowd items
        if len(self.items) >= 4:
            return

        pos = self.maze.get_random_open_cell(min_dist_from=(self.player.r, self.player.c), min_dist=5)
        # Avoid placing on top of existing item
        if any(item.pos == pos for item in self.items):
            return

        if forced_type:
            itype = forced_type
        else:
            weights = [
                (ItemType.GEM, 0.40),
                (ItemType.SPEED, 0.25),
                (ItemType.EMP, 0.20),
                (ItemType.SHIELD, 0.15)
            ]
            r = random.random()
            acc = 0.0
            itype = ItemType.GEM
            for t, w in weights:
                acc += w
                if r <= acc:
                    itype = t
                    break

        self.items.append(Item(itype, pos))

    def trigger_emp(self):
        """Activates EMP pulse, stunning all 3 killers."""
        if not self.player or self.player.emp_charges <= 0:
            return

        self.player.emp_charges -= 1
        sound_fx.play_emp()

        # Add visual shockwave
        self.shockwaves.append(Shockwave(self.player.px, self.player.py, max_radius=600))
        self.add_floating_text(self.player.px, self.player.py - 24, "⚡ EMP BLAST! KILLERS STUNNED!", COLOR_ACCENT_CYAN, 1.5)

        for killer in self.killers:
            killer.stun(EMP_STUN_DURATION_SEC)

    def add_floating_text(self, x: float, y: float, text: str, color: str, duration: float = 1.0):
        self.floating_texts.append(FloatingText(x, y, text, color, duration))

    def load_high_score(self):
        if os.path.exists(HIGHSCORE_FILE):
            try:
                with open(HIGHSCORE_FILE, "r") as f:
                    data = json.load(f)
                    self.high_score = data.get("score", 0)
                    self.best_time = data.get("time", 0.0)
            except Exception:
                self.high_score = 0
                self.best_time = 0.0

    def save_high_score(self):
        try:
            with open(HIGHSCORE_FILE, "w") as f:
                json.dump({
                    "score": int(self.high_score),
                    "time": round(self.best_time, 1)
                }, f)
        except Exception:
            pass

    def _game_loop(self):
        now = time.time()
        dt = min(0.1, now - self.last_update_time)
        self.last_update_time = now

        if self.state == self.STATE_PLAYING:
            self._update_playing(dt)

        self._render()

        # Queue next frame
        self.root.after(FRAME_DELAY_MS, self._game_loop)

    def _update_playing(self, dt: float):
        now = time.time()
        self.elapsed_time = now - self.game_start_time

        # Tell the player which direction keys are physically held (most recent first).
        # The player only keeps moving while one of them is down.
        self.player.set_held_directions([DIR_MAP[k] for k in reversed(self.dir_key_history)])

        # Update player with frame delta
        self.player.update(self.maze, dt)

        # Multiplier & Survival Score Accumulation
        time_since_move = now - self.player.last_position_change_time
        if time_since_move > IDLE_THRESHOLD_SEC:
            # Idle penalty: standing in one spot reduces multiplier
            self.multiplier = max(MIN_MULTIPLIER, self.multiplier - MULTIPLIER_DEC_RATE * dt)
        else:
            # Active movement rewards higher multiplier
            self.multiplier = min(MAX_MULTIPLIER, self.multiplier + MULTIPLIER_INC_RATE * dt)

        # Points accumulate continuously based on time survived
        points_this_frame = (BASE_POINTS_PER_SEC * self.multiplier) * dt
        self.score += points_this_frame

        # Update killers with frame delta
        for killer in self.killers:
            killer.update_movement(self.maze, self.player, self.elapsed_time, dt)

        # Item Spawner
        if now - self.last_item_spawn_time > 10.0:
            self._spawn_random_item()
            self.last_item_spawn_time = now

        # Remove expired items
        self.items = [item for item in self.items if not item.is_expired()]

        # Check item pickup with cell & pixel proximity
        player_cell = (self.player.r, self.player.c)
        remaining_items = []
        for item in self.items:
            item_px = item.pos[1] * CELL_SIZE + CELL_SIZE // 2
            item_py = item.pos[0] * CELL_SIZE + CELL_SIZE // 2
            item_dist = math.hypot(item_px - self.player.px, item_py - self.player.py)
            if item.pos == player_cell or item_dist < (CELL_SIZE * 0.70):
                sound_fx.play_pickup()
                if item.item_type == ItemType.GEM:
                    bonus = int(500 * self.multiplier)
                    self.score += bonus
                    self.add_floating_text(self.player.px, self.player.py - 15, f"+{bonus} PTS!", COLOR_ITEM_GEM)
                elif item.item_type == ItemType.EMP:
                    self.player.emp_charges = min(3, self.player.emp_charges + 1)
                    self.add_floating_text(self.player.px, self.player.py - 15, "+1 EMP CHARGE!", COLOR_ITEM_EMP)
                elif item.item_type == ItemType.SPEED:
                    self.player.speed_boost_until = now + 6.0
                    self.add_floating_text(self.player.px, self.player.py - 15, "SPEED BOOST!", COLOR_ITEM_SPEED)
                elif item.item_type == ItemType.SHIELD:
                    self.player.shield_active = True
                    self.add_floating_text(self.player.px, self.player.py - 15, "SHIELD ACTIVE!", COLOR_ITEM_SHIELD)
            else:
                remaining_items.append(item)
        self.items = remaining_items

        # Killer Proximity, Near-Miss Detection, and Heartbeat Audio
        min_killer_dist = 999
        for killer in self.killers:
            dist = Maze.manhattan((killer.r, killer.c), player_cell)
            if dist < min_killer_dist:
                min_killer_dist = dist

        # Heartbeat pulse when a killer is dangerously near (<= 4 tiles)
        if min_killer_dist <= 4 and (now - self.last_heartbeat_time > 0.8):
            sound_fx.play_heartbeat()
            self.last_heartbeat_time = now

        # Near-miss bonus: close dodge without getting caught
        if min_killer_dist <= 2 and (now - self.last_near_miss_time > 4.0):
            self.last_near_miss_time = now
            self.near_misses_count += 1
            near_miss_bonus = 400
            self.score += near_miss_bonus
            sound_fx.play_near_miss()
            self.add_floating_text(self.player.px, self.player.py - 25, "NEAR MISS! +400", COLOR_ACCENT_GOLD, 1.2)

        # Fair pixel-distance collision check with killers
        hit_radius = CELL_SIZE * 0.68
        for killer in self.killers:
            dist = math.hypot(killer.px - self.player.px, killer.py - self.player.py)
            if dist < hit_radius:
                if not killer.is_stunned():
                    if self.player.shield_active:
                        # Shield absorbs hit!
                        self.player.shield_active = False
                        killer.stun(2.5)
                        sound_fx.play_shield_break()
                        self.add_floating_text(self.player.px, self.player.py - 20, "SHIELD BROKEN!", COLOR_ACCENT_RED, 1.5)
                    else:
                        # Lethal hit: Game Over
                        self._trigger_game_over(killer)
                        break

    def _trigger_game_over(self, killer: Killer):
        self.state = self.STATE_GAMEOVER
        sound_fx.play_game_over()
        
        # Check high scores
        is_new_score = self.score > self.high_score
        is_new_time = self.elapsed_time > self.best_time
        
        if is_new_score:
            self.high_score = self.score
        if is_new_time:
            self.best_time = self.elapsed_time

        if is_new_score or is_new_time:
            self.save_high_score()

    def _render(self):
        # Render Top HUD
        self._render_hud()

        # Render Main Canvas based on state
        self.canvas.delete("all")
        if self.state == self.STATE_MENU:
            self._render_menu()
        elif self.state == self.STATE_RULES:
            self._render_rules()
        elif self.state == self.STATE_PLAYING:
            self._render_maze()
            self._render_items()
            self._render_killers()
            self._render_player()
            self._render_effects()
        elif self.state == self.STATE_PAUSED:
            self._render_maze()
            self._render_items()
            self._render_killers()
            self._render_player()
            self._render_paused_overlay()
        elif self.state == self.STATE_GAMEOVER:
            self._render_maze()
            self._render_killers()
            self._render_player()
            self._render_gameover_overlay()

    def _render_hud(self):
        self.hud_canvas.delete("all")

        # Background gradient line
        self.hud_canvas.create_line(0, HUD_HEIGHT - 1, TOTAL_WIDTH, HUD_HEIGHT - 1, fill=COLOR_HUD_BORDER, width=2)

        # 1. Survival Time (Left)
        minutes = int(self.elapsed_time // 60)
        seconds = self.elapsed_time % 60
        time_str = f"{minutes:02d}:{seconds:04.1f}"
        self.hud_canvas.create_text(24, 25, text="⏱ TIME", fill=COLOR_TEXT_SECONDARY, font=("Consolas", 10, "bold"), anchor="w")
        self.hud_canvas.create_text(24, 55, text=time_str, fill=COLOR_ACCENT_CYAN, font=("Consolas", 22, "bold"), anchor="w")

        # 2. Score (Left-Center)
        self.hud_canvas.create_text(180, 25, text="⭐ SCORE", fill=COLOR_TEXT_SECONDARY, font=("Consolas", 10, "bold"), anchor="w")
        self.hud_canvas.create_text(180, 55, text=f"{int(self.score):,}", fill=COLOR_ACCENT_GOLD, font=("Consolas", 22, "bold"), anchor="w")

        # 3. Multiplier (Center)
        mult_color = COLOR_ACCENT_RED if self.multiplier <= 0.8 else (COLOR_ACCENT_GOLD if self.multiplier >= 2.0 else COLOR_ACCENT_CYAN)
        mult_subtext = "IDLE PENALTY!" if (self.player and (time.time() - self.player.last_position_change_time > IDLE_THRESHOLD_SEC)) else "ACTIVE"
        self.hud_canvas.create_text(340, 25, text=f"⚡ MULTIPLIER ({mult_subtext})", fill=mult_color, font=("Consolas", 9, "bold"), anchor="w")
        self.hud_canvas.create_text(340, 55, text=f"{self.multiplier:.1f}x", fill=mult_color, font=("Consolas", 22, "bold"), anchor="w")

        # 4. Abilities - You (Center-Right)
        now = time.time()
        dash_ready = self.player and (now >= self.player.dash_ready_time)
        dash_text = "READY [SPACE]" if dash_ready else ("ACTIVE!" if (self.player and self.player.is_dashing) else "RECHARGING...")
        dash_color = COLOR_ACCENT_CYAN if dash_ready else ("#38bdf8" if (self.player and self.player.is_dashing) else "#64748b")
        self.hud_canvas.create_text(485, 25, text="DASH SPRINT", fill=COLOR_TEXT_SECONDARY, font=("Consolas", 9, "bold"), anchor="w")
        self.hud_canvas.create_text(485, 45, text=dash_text, fill=dash_color, font=("Consolas", 10, "bold"), anchor="w")

        charges = self.player.emp_charges if self.player else 0
        emp_icons = ("⚡ " * charges) + ("○ " * (3 - charges))
        self.hud_canvas.create_text(485, 66, text=f"EMP [F]: {emp_icons.strip()}", fill=COLOR_ACCENT_CYAN, font=("Segoe UI Symbol", 10, "bold"), anchor="w")

        # 5. ALL-TIME BEST / HIGH SCORE (TOP RIGHT!)
        card_rx = TOTAL_WIDTH - 24
        self.hud_canvas.create_text(card_rx, 25, text="🏆 ALL-TIME BEST", fill=COLOR_ACCENT_GOLD, font=("Consolas", 10, "bold"), anchor="e")
        self.hud_canvas.create_text(card_rx, 50, text=f"{int(self.high_score):,} PTS", fill="#ffffff", font=("Consolas", 18, "bold"), anchor="e")
        best_min = int(self.best_time // 60)
        best_sec = self.best_time % 60
        self.hud_canvas.create_text(card_rx, 70, text=f"RECORD TIME: {best_min:02d}:{best_sec:04.1f}", fill=COLOR_TEXT_SECONDARY, font=("Consolas", 8), anchor="e")

    def _render_maze(self):
        if not self.maze:
            return

        for r in range(self.maze.rows):
            for c in range(self.maze.cols):
                x1 = c * CELL_SIZE
                y1 = r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE

                if self.maze.grid[r][c] == Maze.WALL:
                    # Wall block
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill=COLOR_WALL,
                        outline=COLOR_WALL_BORDER,
                        width=1
                    )
                else:
                    # Open corridor with subtle center dot
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    self.canvas.create_oval(
                        cx - 1, cy - 1, cx + 1, cy + 1,
                        fill=COLOR_PATH_DOT,
                        outline=""
                    )

    def _render_items(self):
        for item in self.items:
            r, c = item.pos
            cx = c * CELL_SIZE + CELL_SIZE // 2
            cy = r * CELL_SIZE + CELL_SIZE // 2

            # Pulsing size effect
            pulse = math.sin(time.time() * 6.0) * 2.0
            rad = (CELL_SIZE * 0.32) + pulse

            self.canvas.create_oval(
                cx - rad, cy - rad, cx + rad, cy + rad,
                fill="",
                outline=item.color,
                width=2
            )
            self.canvas.create_text(
                cx, cy,
                text=item.symbol,
                fill=item.color,
                font=("Segoe UI Symbol", 12, "bold")
            )

    def _render_player(self):
        if not self.player:
            return

        px, py = self.player.px, self.player.py
        radius = CELL_SIZE * 0.40

        # Shield Bubble if active
        if self.player.shield_active:
            shield_r = radius + 6 + math.sin(time.time() * 8) * 2
            self.canvas.create_oval(
                px - shield_r, py - shield_r, px + shield_r, py + shield_r,
                fill="",
                outline="#38bdf8",
                width=2
            )

        # Outer glow
        glow_rad = radius + (4 if self.player.is_dashing else 2)
        glow_col = COLOR_ACCENT_GOLD if self.player.is_dashing else COLOR_PLAYER_GLOW
        self.canvas.create_oval(
            px - glow_rad, py - glow_rad, px + glow_rad, py + glow_rad,
            fill="",
            outline=glow_col,
            width=2
        )

        # Player Body
        fill_col = COLOR_ACCENT_GOLD if self.player.is_dashing else COLOR_PLAYER
        self.canvas.create_oval(
            px - radius, py - radius, px + radius, py + radius,
            fill=fill_col,
            outline="#ffffff",
            width=1
        )

        # Facing Direction Pointer (Eyes/Arrow)
        eye_dist = radius * 0.45
        facing_c = self.player.dir_c if (self.player.dir_r != 0 or self.player.dir_c != 0) else getattr(self.player, "last_facing_c", 1)
        facing_r = self.player.dir_r if (self.player.dir_r != 0 or self.player.dir_c != 0) else getattr(self.player, "last_facing_r", 0)
        eye_x = px + facing_c * eye_dist
        eye_y = py + facing_r * eye_dist
        self.canvas.create_oval(
            eye_x - 3, eye_y - 3, eye_x + 3, eye_y + 3,
            fill="#090d13",
            outline=""
        )

        # Player Identification (YOU)
        self.canvas.create_text(
            px, py - radius - 8,
            text="YOU",
            fill=COLOR_PLAYER,
            font=("Consolas", 8, "bold")
        )

    def _render_killers(self):
        for killer in self.killers:
            kx, ky = killer.px, killer.py
            radius = CELL_SIZE * 0.42

            # Stunned Ice Ring
            if killer.is_stunned():
                self.canvas.create_oval(
                    kx - radius - 5, ky - radius - 5, kx + radius + 5, ky + radius + 5,
                    fill="",
                    outline=COLOR_ACCENT_CYAN,
                    width=2,
                    dash=(3, 3)
                )
                self.canvas.create_text(
                    kx, ky - radius - 8,
                    text="STUNNED",
                    fill=COLOR_ACCENT_CYAN,
                    font=("Consolas", 8, "bold")
                )

            # Outer aura
            aura_col = COLOR_KILLER_BEAST_ENRAGED if (isinstance(killer, BeastKiller) and killer.is_enraged) else killer.glow_color
            aura_rad = radius + 3 + (3 if (isinstance(killer, BeastKiller) and killer.is_enraged) else 0)
            self.canvas.create_oval(
                kx - aura_rad, ky - aura_rad, kx + aura_rad, ky + aura_rad,
                fill="",
                outline=aura_col,
                width=2
            )

            # Killer Body
            body_col = COLOR_KILLER_BEAST_ENRAGED if (isinstance(killer, BeastKiller) and killer.is_enraged) else killer.color
            self.canvas.create_oval(
                kx - radius, ky - radius, kx + radius, ky + radius,
                fill=body_col,
                outline="#000000",
                width=1
            )

            # Menacing Eyes
            eye_col = "#ffffff" if not killer.is_stunned() else "#67e8f9"
            self.canvas.create_oval(kx - 5, ky - 3, kx - 1, ky + 1, fill=eye_col, outline="")
            self.canvas.create_oval(kx + 1, ky - 3, kx + 5, ky + 1, fill=eye_col, outline="")
            self.canvas.create_oval(kx - 4, ky - 2, kx - 2, ky, fill="#000000", outline="")
            self.canvas.create_oval(kx + 2, ky - 2, kx + 4, ky, fill="#000000", outline="")

    def _render_effects(self):
        # Shockwaves (EMP Blast)
        alive_waves = []
        for wave in self.shockwaves:
            if wave.is_alive():
                r = wave.get_radius()
                self.canvas.create_oval(
                    wave.cx - r, wave.cy - r, wave.cx + r, wave.cy + r,
                    fill="",
                    outline=COLOR_ACCENT_CYAN,
                    width=3
                )
                alive_waves.append(wave)
        self.shockwaves = alive_waves

        # Floating Texts
        alive_texts = []
        for ft in self.floating_texts:
            if ft.is_alive():
                prog = ft.get_progress()
                y = ft.y - (prog * 30)  # Float upwards
                self.canvas.create_text(
                    ft.x, y,
                    text=ft.text,
                    fill=ft.color,
                    font=("Consolas", 10, "bold")
                )
                alive_texts.append(ft)
        self.floating_texts = alive_texts

        # Danger Edge Pulse if killer is very close
        if self.player:
            min_dist = min(Maze.manhattan((k.r, k.c), (self.player.r, self.player.c)) for k in self.killers)
            if min_dist <= 2:
                # Pulsing red danger border
                self.canvas.create_rectangle(
                    0, 0, CANVAS_WIDTH, CANVAS_HEIGHT,
                    fill="",
                    outline=COLOR_ACCENT_RED,
                    width=6
                )

    def _render_menu(self):
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2

        # 1. TOP-RIGHT ALL-TIME BEST / HIGH SCORE CARD
        hx1, hy1, hx2, hy2 = CANVAS_WIDTH - 240, 20, CANVAS_WIDTH - 24, 76
        self.canvas.create_rectangle(hx1, hy1, hx2, hy2, fill="#111827", outline="#374151", width=1)
        self.canvas.create_text(hx1 + 14, hy1 + 18, text="🏆 ALL-TIME BEST", fill=COLOR_ACCENT_GOLD, font=("Consolas", 9, "bold"), anchor="w")
        best_min = int(self.best_time // 60)
        best_sec = self.best_time % 60
        self.canvas.create_text(hx1 + 14, hy1 + 42, text=f"{int(self.high_score):,} PTS", fill="#ffffff", font=("Consolas", 15, "bold"), anchor="w")
        self.canvas.create_text(hx2 - 14, hy1 + 42, text=f"{best_min:02d}:{best_sec:04.1f}", fill=COLOR_TEXT_SECONDARY, font=("Consolas", 11), anchor="e")

        # 2. TITLE
        self.canvas.create_text(cx, cy - 140, text="MAZE SURVIVAL", fill="#ffffff", font=("Impact", 44))
        self.canvas.create_text(cx, cy - 96, text="OUTRUN THE 3 KILLERS", fill=COLOR_ACCENT_RED, font=("Consolas", 12, "bold"))

        # 3. PLAYER SPOTLIGHT (TELL THE USER THEY ARE GREEN)
        spot_y = cy - 36
        # Glowing rings
        self.canvas.create_oval(cx - 25, spot_y - 25, cx + 25, spot_y + 25, fill="", outline=COLOR_PLAYER_GLOW, width=3)
        self.canvas.create_oval(cx - 18, spot_y - 18, cx + 18, spot_y + 18, fill=COLOR_PLAYER, outline="#ffffff", width=2)
        # Eye pointer
        self.canvas.create_oval(cx + 2, spot_y - 3, cx + 8, spot_y + 3, fill="#090d13", outline="")

        self.canvas.create_text(cx, spot_y + 35, text="YOU ARE THE GREEN SPHERE", fill=COLOR_PLAYER, font=("Consolas", 14, "bold"))
        self.canvas.create_text(cx, spot_y + 58, text="Navigate the maze. The longer you stay alive, the more points you earn!", fill=COLOR_TEXT_SECONDARY, font=("Consolas", 11))

        # 4. ACTION BUTTONS (CLICKABLE & KEYBOARD ACCESSIBLE)
        # Play Game Button
        bx1, by1, bx2, by2 = self.btn_play
        self.canvas.create_rectangle(bx1, by1, bx2, by2, fill=COLOR_PLAYER, outline="#ffffff", width=2)
        self.canvas.create_text(cx, by1 + 18, text="▶  PLAY GAME", fill="#090d13", font=("Consolas", 15, "bold"))
        self.canvas.create_text(cx, by1 + 38, text="[ CLICK OR PRESS SPACE ]", fill="#064e3b", font=("Consolas", 9, "bold"))

        # How to Play & Rules Button
        rx1, ry1, rx2, ry2 = self.btn_rules
        self.canvas.create_rectangle(rx1, ry1, rx2, ry2, fill="#1e293b", outline=COLOR_ACCENT_CYAN, width=1)
        self.canvas.create_text(cx, ry1 + 22, text="📜  HOW TO PLAY & RULES  (H)", fill=COLOR_ACCENT_CYAN, font=("Consolas", 12, "bold"))

        # Sound Toggle Pill
        sx1, sy1, sx2, sy2 = self.btn_sound
        snd_txt = "🔊 SOUND: ON" if sound_fx.enabled else "🔇 SOUND: MUTED"
        snd_col = COLOR_TEXT_SECONDARY if sound_fx.enabled else COLOR_ACCENT_RED
        self.canvas.create_rectangle(sx1, sy1, sx2, sy2, fill="#0f172a", outline="#334155", width=1)
        self.canvas.create_text(cx, sy1 + 17, text=f"{snd_txt} (M)", fill=snd_col, font=("Consolas", 9, "bold"))

    def _render_rules(self):
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2

        # Header
        self.canvas.create_text(cx, 55, text="GAME RULES & CONTROLS", fill="#ffffff", font=("Impact", 34))
        self.canvas.create_text(cx, 90, text="Everything you need to outlast the 3 killers", fill=COLOR_ACCENT_CYAN, font=("Consolas", 11, "bold"))

        # Card 1: Objective & Multiplier
        c1_x1, c1_y1, c1_x2, c1_y2 = cx - 340, 115, cx + 340, 235
        self.canvas.create_rectangle(c1_x1, c1_y1, c1_x2, c1_y2, fill="#111827", outline="#374151", width=1)
        self.canvas.create_text(c1_x1 + 20, c1_y1 + 18, text="🎯 OBJECTIVE & SCORING", fill=COLOR_ACCENT_GOLD, font=("Consolas", 12, "bold"), anchor="w")
        rules = [
            "• You are GREEN. Move through corridors and evade the 3 hunting killers.",
            "• SURVIVAL TIME = POINTS: Every millisecond you survive increases your score.",
            "• ACTIVE COMBOS: Continuously moving ramps your point multiplier up to 3.0x!",
            "• IDLE PENALTY: Stopping or camping in dead-ends drops your multiplier to 0.5x.",
            "• NARROW ESCAPE (+400 PTS): Slashing past killers at close range awards bonus score."
        ]
        ty = c1_y1 + 38
        for line in rules:
            self.canvas.create_text(c1_x1 + 20, ty, text=line, fill=COLOR_TEXT_PRIMARY, font=("Consolas", 9), anchor="w")
            ty += 18

        # Card 2: Controls
        c2_x1, c2_y1, c2_x2, c2_y2 = cx - 340, 248, cx + 340, 395
        self.canvas.create_rectangle(c2_x1, c2_y1, c2_x2, c2_y2, fill="#111827", outline="#374151", width=1)
        self.canvas.create_text(c2_x1 + 20, c2_y1 + 18, text="⌨️ CONTROLS & SURVIVAL ABILITIES", fill=COLOR_ACCENT_CYAN, font=("Consolas", 12, "bold"), anchor="w")
        ctrls = [
            "• [W, A, S, D] or [ARROWS]  : Move / Steer with instant 180° reversal & corner buffering.",
            "• [SPACEBAR]                : SPRINT DASH — burst of speed to escape tight pinches.",
            "• [F] or [E]                : EMP FLASHBANG — electric shockwave stuns all killers for 3.5s.",
            "• [P]                       : Pause / Resume game.",
            "• [M]                       : Toggle audio sound effects."
        ]
        ty = c2_y1 + 40
        for line in ctrls:
            self.canvas.create_text(c2_x1 + 20, ty, text=line, fill=COLOR_TEXT_PRIMARY, font=("Consolas", 9), anchor="w")
            ty += 20

        # Card 3: Power-Ups
        c3_x1, c3_y1, c3_x2, c3_y2 = cx - 340, 408, cx + 340, 492
        self.canvas.create_rectangle(c3_x1, c3_y1, c3_x2, c3_y2, fill="#111827", outline="#374151", width=1)
        self.canvas.create_text(c3_x1 + 20, c3_y1 + 16, text="⚡ POWER-UPS (SCATTERED IN MAZE)", fill="#ec4899", font=("Consolas", 11, "bold"), anchor="w")
        self.canvas.create_text(c3_x1 + 20, c3_y1 + 40, text="◆ Gem (+500 PTS)        |  ⚡ EMP (+1 Stun Charge, Max 3)", fill=COLOR_TEXT_PRIMARY, font=("Consolas", 9), anchor="w")
        self.canvas.create_text(c3_x1 + 20, c3_y1 + 62, text="» Speed (Faster Speed)   |  🛡 Shield (Absorbs 1 Lethal Catch)", fill=COLOR_TEXT_PRIMARY, font=("Consolas", 9), anchor="w")

        # Back Button
        bx1, by1, bx2, by2 = self.btn_rules_back
        self.canvas.create_rectangle(bx1, by1, bx2, by2, fill="#1e293b", outline=COLOR_PLAYER, width=2)
        self.canvas.create_text(cx, by1 + 22, text="⬅  BACK TO MENU  [ESC]", fill="#ffffff", font=("Consolas", 12, "bold"))

    def _render_paused_overlay(self):
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2
        # Dimming rectangle
        self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill="#000000", stipple="gray50")
        self.canvas.create_text(cx, cy - 20, text="PAUSED", fill="#ffffff", font=("Impact", 36))
        self.canvas.create_text(cx, cy + 30, text="Press [P] to Resume", fill=COLOR_ACCENT_CYAN, font=("Consolas", 14, "bold"))

    def _render_gameover_overlay(self):
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2

        # Dim background
        self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill="#05080d", stipple="gray75")

        self.canvas.create_text(cx, cy - 130, text="YOU WERE CAUGHT!", fill=COLOR_ACCENT_RED, font=("Impact", 44))
        self.canvas.create_text(cx, cy - 80, text="You were cornered in the maze.", fill=COLOR_TEXT_SECONDARY, font=("Consolas", 12))

        # Stats Card
        minutes = int(self.elapsed_time // 60)
        seconds = self.elapsed_time % 60
        time_str = f"{minutes:02d}:{seconds:04.1f}"

        stats = [
            f"Survival Time : {time_str}",
            f"Final Score   : {int(self.score):,} Points",
            f"Max Multiplier: {self.multiplier:.1f}x",
            f"Near Misses   : {self.near_misses_count} Narrow Escapes"
        ]

        card_y = cy - 35
        for s in stats:
            self.canvas.create_text(cx, card_y, text=s, fill=COLOR_TEXT_PRIMARY, font=("Consolas", 13, "bold"))
            card_y += 26

        if int(self.score) >= int(self.high_score) and self.score > 0:
            self.canvas.create_text(cx, card_y + 8, text="★ NEW ALL-TIME RECORD! ★", fill=COLOR_ACCENT_GOLD, font=("Consolas", 13, "bold"))

        # Replay & Menu buttons
        rx1, ry1, rx2, ry2 = self.btn_gameover_replay
        self.canvas.create_rectangle(rx1, ry1, rx2, ry2, fill=COLOR_PLAYER, outline="#ffffff", width=2)
        self.canvas.create_text(cx, ry1 + 22, text="🔄  PLAY AGAIN  [R / SPACE]", fill="#090d13", font=("Consolas", 12, "bold"))

        mx1, my1, mx2, my2 = self.btn_gameover_menu
        self.canvas.create_rectangle(mx1, my1, mx2, my2, fill="#1e293b", outline="#64748b", width=1)
        self.canvas.create_text(cx, my1 + 20, text="🏠  MAIN MENU  [ESC]", fill="#f8fafc", font=("Consolas", 11, "bold"))
