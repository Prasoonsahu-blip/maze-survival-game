"""
Entities: Player and the 3 unique Killer AIs (Stalker, Phantom, Beast).
"""

import time
import random
from typing import Tuple, Optional, List
from constants import (
    COLOR_PLAYER, COLOR_PLAYER_GLOW,
    COLOR_KILLER_STALKER, COLOR_KILLER_STALKER_GLOW,
    COLOR_KILLER_PHANTOM, COLOR_KILLER_PHANTOM_GLOW,
    COLOR_KILLER_BEAST, COLOR_KILLER_BEAST_GLOW, COLOR_KILLER_BEAST_ENRAGED,
    KILLER_SPEED_NORMAL, KILLER_SPEED_PHANTOM, KILLER_SPEED_BEAST_PATROL,
    KILLER_SPEED_BEAST_SPRINT, KILLER_SPEED_MIN_CAP,
    PLAYER_BASE_SPEED_MS, PLAYER_DASH_SPEED_MS,
    DASH_DURATION_SEC, DASH_COOLDOWN_SEC, CELL_SIZE, TURN_BUFFER_SEC
)
from maze import Maze

class Player:
    def __init__(self, start_pos: Tuple[int, int]):
        self.r, self.c = start_pos
        self.target_r, self.target_c = start_pos
        self.prev_r, self.prev_c = start_pos
        self.progress = 0.0  # Transition progress between (r, c) and (target_r, target_c)
        
        self.dir_r, self.dir_c = 0, 0          # Current active moving direction
        self.desired_dir = (0, 0)              # One-shot buffered tap (consumed when used)
        self.desired_dir_time = 0.0            # When the tap was registered
        self.held_dirs: List[Tuple[int, int]] = []  # Currently held keys, most recent first
        self.last_facing_r, self.last_facing_c = 0, 1 # Visual facing direction for eyes

        # Floating-point pixel coordinates
        self.px = float(self.c * CELL_SIZE + CELL_SIZE // 2)
        self.py = float(self.r * CELL_SIZE + CELL_SIZE // 2)

        # Abilities & Stats
        self.emp_charges = 2
        self.shield_active = False
        self.speed_boost_until = 0.0
        
        # Dash state
        self.is_dashing = False
        self.dash_until = 0.0
        self.dash_ready_time = 0.0

        # Movement tracking
        self.last_position_change_time = time.time()
        self.visited_cells = {start_pos}

    def set_desired_direction(self, dr: int, dc: int):
        self.desired_dir = (dr, dc)
        self.desired_dir_time = time.time()
        if dr != 0 or dc != 0:
            self.last_facing_r, self.last_facing_c = dr, dc

    def set_held_directions(self, dirs: List[Tuple[int, int]]):
        """Directions whose keys are physically held right now, most recently pressed first.
        The player only keeps moving while at least one of these is held."""
        self.held_dirs = list(dirs)
        if self.held_dirs:
            self.last_facing_r, self.last_facing_c = self.held_dirs[0]

    def _candidates(self, now: float) -> List[Tuple[int, int]]:
        """Directions the player wants to go, best first: a fresh tap, then held keys."""
        cands: List[Tuple[int, int]] = []
        if self.desired_dir != (0, 0) and (now - self.desired_dir_time) < TURN_BUFFER_SEC:
            cands.append(self.desired_dir)
        for d in self.held_dirs:
            if d not in cands:
                cands.append(d)
        return cands

    def _pick_open(self, maze: Maze, cands: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """First wanted direction that is actually walkable from the current cell."""
        for dr, dc in cands:
            if maze.is_path(self.r + dr, self.c + dc):
                return (dr, dc)
        return None

    def _consume_tap(self, d: Tuple[int, int]):
        if self.desired_dir == d:
            self.desired_dir = (0, 0)

    def trigger_dash(self) -> bool:
        now = time.time()
        if now >= self.dash_ready_time and not self.is_dashing:
            self.is_dashing = True
            self.dash_until = now + DASH_DURATION_SEC
            self.dash_ready_time = now + DASH_DURATION_SEC + DASH_COOLDOWN_SEC
            return True
        return False

    def get_tiles_per_sec(self) -> float:
        now = time.time()
        if self.is_dashing and now < self.dash_until:
            return 14.5  # Dash sprint: ~406 px/sec - explosive burst
        elif now < self.speed_boost_until:
            return 12.0  # Speed boost: ~336 px/sec
        return 9.2       # Base speed: ~258 px/sec - snappy, fast, highly responsive

    def is_moving(self) -> bool:
        return (self.dir_r != 0 or self.dir_c != 0) and (self.r != self.target_r or self.c != self.target_c)

    def update(self, maze: Maze, dt: float = 0.016):
        now = time.time()
        if self.is_dashing and now >= self.dash_until:
            self.is_dashing = False

        step = self.get_tiles_per_sec() * dt
        cands = self._candidates(now)

        # 1. Instant 180° reversal while traveling between cells
        if self.is_moving() and cands and cands[0] == (-self.dir_r, -self.dir_c):
            qdr, qdc = cands[0]
            self.r, self.target_r = self.target_r, self.r
            self.c, self.target_c = self.target_c, self.c
            self.dir_r, self.dir_c = qdr, qdc
            self.progress = max(0.0, 1.0 - self.progress)
            self.last_position_change_time = now
            self._consume_tap((qdr, qdc))

        # 2. Advance toward the next cell. On arrival, keep going ONLY if a key
        #    is still held (or a fresh tap is buffered); otherwise stop dead on the cell.
        if self.is_moving():
            self.progress += step
            while self.progress >= 1.0 and self.is_moving():
                excess = self.progress - 1.0
                self.prev_r, self.prev_c = self.r, self.c
                self.r, self.c = self.target_r, self.target_c
                self.visited_cells.add((self.r, self.c))
                self.last_position_change_time = now

                choice = self._pick_open(maze, self._candidates(now))
                if choice:
                    self.dir_r, self.dir_c = choice
                    self.target_r, self.target_c = self.r + choice[0], self.c + choice[1]
                    self.progress = excess
                    self._consume_tap(choice)
                else:
                    # No key held / path blocked: stop cleanly at the tile center
                    self.target_r, self.target_c = self.r, self.c
                    self.dir_r, self.dir_c = 0, 0
                    self.progress = 0.0

        # 3. Standing on a cell: start moving immediately toward any wanted open direction
        if not self.is_moving():
            choice = self._pick_open(maze, cands)
            if choice:
                self.dir_r, self.dir_c = choice
                self.target_r, self.target_c = self.r + choice[0], self.c + choice[1]
                self.progress = min(0.99, step)
                self.last_position_change_time = now
                self._consume_tap(choice)

        # 4. Smooth continuous sub-pixel coordinates for rendering
        start_x = self.c * CELL_SIZE + CELL_SIZE // 2
        start_y = self.r * CELL_SIZE + CELL_SIZE // 2
        target_x = self.target_c * CELL_SIZE + CELL_SIZE // 2
        target_y = self.target_r * CELL_SIZE + CELL_SIZE // 2

        self.px = start_x + (target_x - start_x) * self.progress
        self.py = start_y + (target_y - start_y) * self.progress


class Killer:
    def __init__(self, name: str, start_pos: Tuple[int, int], color: str, glow_color: str, base_interval_ms: int):
        self.name = name
        self.r, self.c = start_pos
        self.color = color
        self.glow_color = glow_color
        self.base_interval_ms = base_interval_ms
        self.current_interval_ms = base_interval_ms
        
        # Pixel coordinates for smooth movement
        self.px = self.c * CELL_SIZE + CELL_SIZE // 2
        self.py = self.r * CELL_SIZE + CELL_SIZE // 2

        self.last_move_time = 0.0
        self.stunned_until = 0.0
        self.target_cell = start_pos
        self.is_enraged = False

    def stun(self, duration_sec: float):
        self.stunned_until = max(self.stunned_until, time.time() + duration_sec)

    def is_stunned(self) -> bool:
        return time.time() < self.stunned_until

    def update_difficulty(self, elapsed_sec: float):
        """Gradually speeds up killers over time (dynamic scaling)."""
        # Accelerate slightly every 15 seconds
        speed_boost = int((elapsed_sec / 15.0) * 12)
        self.current_interval_ms = max(KILLER_SPEED_MIN_CAP, self.base_interval_ms - speed_boost)

    def step_towards(self, target: Tuple[int, int], maze: Maze):
        next_cell = maze.bfs_next_step((self.r, self.c), target)
        if next_cell:
            self.r, self.c = next_cell

    def update_movement(self, maze: Maze, player: Player, elapsed_sec: float, dt: float = 0.016):
        now = time.time()
        self.update_difficulty(elapsed_sec)

        # Smooth pixel interpolation towards target
        target_px = self.c * CELL_SIZE + CELL_SIZE // 2
        target_py = self.r * CELL_SIZE + CELL_SIZE // 2
        lerp = min(1.0, 16.0 * dt)
        self.px += (target_px - self.px) * lerp
        self.py += (target_py - self.py) * lerp

        if self.is_stunned():
            return

        interval_sec = self.current_interval_ms / 1000.0
        if now - self.last_move_time >= interval_sec:
            self.decide_and_move(maze, player)
            self.last_move_time = now

    def decide_and_move(self, maze: Maze, player: Player):
        """Override in subclasses."""
        pass


class StalkerKiller(Killer):
    """
    Killer 1: The Stalker (Crimson Red).
    Relentlessly chases player along the shortest BFS path.
    """
    def __init__(self, start_pos: Tuple[int, int]):
        super().__init__(
            name="Stalker",
            start_pos=start_pos,
            color=COLOR_KILLER_STALKER,
            glow_color=COLOR_KILLER_STALKER_GLOW,
            base_interval_ms=KILLER_SPEED_NORMAL
        )

    def decide_and_move(self, maze: Maze, player: Player):
        # Always target the player's exact coordinates
        self.step_towards((player.r, player.c), maze)


class PhantomKiller(Killer):
    """
    Killer 2: The Phantom (Violet).
    Ambusher/Flanker that predicts player direction and intercepts ahead of them.
    """
    def __init__(self, start_pos: Tuple[int, int]):
        super().__init__(
            name="Phantom",
            start_pos=start_pos,
            color=COLOR_KILLER_PHANTOM,
            glow_color=COLOR_KILLER_PHANTOM_GLOW,
            base_interval_ms=KILLER_SPEED_PHANTOM
        )

    def decide_and_move(self, maze: Maze, player: Player):
        # Predict 3 steps ahead of player
        lead_r = player.r + player.dir_r * 3
        lead_c = player.c + player.dir_c * 3

        # Clamp and check if valid open path
        if maze.is_path(lead_r, lead_c):
            target = (lead_r, lead_c)
        else:
            # If wall ahead, find nearest open neighbor to that spot or fallback to player
            neighbors = maze.get_neighbors(player.r, player.c)
            target = random.choice(neighbors) if neighbors else (player.r, player.c)

        self.step_towards(target, maze)


class BeastKiller(Killer):
    """
    Killer 3: The Beast (Blaze Orange).
    Patrols maze areas, but if in straight line-of-sight with player or within 5 tiles,
    enters ENRAGED sprint mode!
    """
    def __init__(self, start_pos: Tuple[int, int]):
        super().__init__(
            name="Beast",
            start_pos=start_pos,
            color=COLOR_KILLER_BEAST,
            glow_color=COLOR_KILLER_BEAST_GLOW,
            base_interval_ms=KILLER_SPEED_BEAST_PATROL
        )
        self.patrol_target: Optional[Tuple[int, int]] = None
        self.enraged_duration = 0.0

    def decide_and_move(self, maze: Maze, player: Player):
        dist = Maze.manhattan((self.r, self.c), (player.r, player.c))
        has_los = maze.has_line_of_sight((self.r, self.c), (player.r, player.c))

        if has_los or dist <= 5:
            # Scent caught! Enrage and charge!
            self.is_enraged = True
            self.current_interval_ms = KILLER_SPEED_BEAST_SPRINT
            self.step_towards((player.r, player.c), maze)
        else:
            self.is_enraged = False
            self.current_interval_ms = self.base_interval_ms

            # Continue patrolling towards target
            if not self.patrol_target or (self.r, self.c) == self.patrol_target:
                self.patrol_target = maze.get_random_open_cell()

            self.step_towards(self.patrol_target, maze)
