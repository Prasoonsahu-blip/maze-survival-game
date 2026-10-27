"""
Simulate player movement with 0.2s tap vs hold logic.
"""

from maze import Maze
from constants import CELL_SIZE

class PlayerSim:
    def __init__(self, start_pos):
        self.r, self.c = start_pos
        self.target_r, self.target_c = start_pos
        self.progress = 0.0
        self.dir_r, self.dir_c = 0, 0
        self.desired_dir = (0, 0)
        
        self.key_pressed = False
        self.key_press_time = 0.0
        self.last_press_duration = 0.0
        self.single_step_mode = False
        self.speed_tiles = 9.2

    def is_moving(self):
        return (self.dir_r != 0 or self.dir_c != 0) and (self.r != self.target_r or self.c != self.target_c)

    def on_press(self, dr, dc, now):
        self.key_pressed = True
        self.key_press_time = now
        self.single_step_mode = False
        self.desired_dir = (dr, dc)

    def on_release(self, duration, now):
        self.key_pressed = False
        self.last_press_duration = duration
        if duration < 0.20:
            self.single_step_mode = True

    def update(self, maze, dt, now):
        step = self.speed_tiles * dt

        # 1. Instant reversal
        if self.is_moving() and (self.desired_dir != (0, 0)):
            qdr, qdc = self.desired_dir
            if qdr == -self.dir_r and qdc == -self.dir_c:
                self.r, self.target_r = self.target_r, self.r
                self.c, self.target_c = self.target_c, self.c
                self.dir_r, self.dir_c = qdr, qdc
                self.progress = max(0.0, 1.0 - self.progress)

        # 2. Advance movement
        if self.is_moving():
            self.progress += step
            while self.progress >= 1.0 and self.is_moving():
                excess = self.progress - 1.0
                self.r, self.c = self.target_r, self.target_c

                # Check if this was a tap (< 0.2s)
                is_tap = False
                if self.single_step_mode:
                    is_tap = True
                elif not self.key_pressed and (self.last_press_duration < 0.20):
                    is_tap = True
                elif self.key_pressed and (now - self.key_press_time < 0.20):
                    # Key is still held, but under 0.20s: pause at tile until 0.2s
                    self.target_r, self.target_c = self.r, self.c
                    self.progress = 0.0
                    break

                if is_tap:
                    # Move ONLY one block! Stop here and clear tap intent.
                    self.target_r, self.target_c = self.r, self.c
                    self.dir_r, self.dir_c = 0, 0
                    self.progress = 0.0
                    self.single_step_mode = False
                    self.desired_dir = (0, 0)
                    break

                # Continuous hold mode: continue moving while key is held
                qdr, qdc = self.desired_dir
                if self.key_pressed:
                    if (qdr != 0 or qdc != 0) and maze.is_path(self.r + qdr, self.c + qdc):
                        self.dir_r, self.dir_c = qdr, qdc
                        self.target_r, self.target_c = self.r + qdr, self.c + qdc
                        self.progress = excess
                    elif maze.is_path(self.r + self.dir_r, self.c + self.dir_c):
                        self.target_r, self.target_c = self.r + self.dir_r, self.c + self.dir_c
                        self.progress = excess
                    else:
                        self.target_r, self.target_c = self.r, self.c
                        self.dir_r, self.dir_c = 0, 0
                        self.progress = 0.0
                else:
                    self.target_r, self.target_c = self.r, self.c
                    self.dir_r, self.dir_c = 0, 0
                    self.progress = 0.0

        # 3. If stationary at a cell, start moving if a key is held or fresh step requested
        if not self.is_moving() and (self.desired_dir != (0, 0)):
            qdr, qdc = self.desired_dir
            # Can start if key is currently down, or if held duration >= 0.2s
            can_start = False
            if self.key_pressed:
                can_start = True
            elif self.single_step_mode:
                can_start = True

            if can_start and maze.is_path(self.r + qdr, self.c + qdc):
                self.dir_r, self.dir_c = qdr, qdc
                self.target_r, self.target_c = self.r + qdr, self.c + qdc
                self.progress = min(0.99, step)
                self.single_step_mode = False


def run_tests():
    maze = Maze(15, 15, loop_factor=0.2)
    # Find a long straight corridor (at least 3 blocks)
    for r in range(1, 14):
        for c in range(1, 12):
            if maze.is_path(r, c) and maze.is_path(r, c+1) and maze.is_path(r, c+2):
                start_c = c
                row = r
                break
        else:
            continue
        break

    print(f"Testing corridor at row {row}, start_col {start_c}...")
    p = PlayerSim((row, start_c))

    # TEST 1: TAP (< 0.2s) -> Should move exactly 1 block!
    t = 100.0
    p.on_press(0, 1, t)
    # Step 50ms
    t += 0.05
    p.update(maze, 0.05, t)
    # Release after 50ms (< 0.2s)
    p.on_release(0.05, t)
    
    # Run forward until player stops
    for _ in range(30):
        t += 0.016
        p.update(maze, 0.016, t)

    assert not p.is_moving(), "Player should stop moving after tap"
    assert p.c == start_c + 1, f"Player should move exactly 1 block (to col {start_c+1}), but is at {p.c}"
    print(f"[OK] Tap (< 0.2s) moved exactly 1 block (from {start_c} to {p.c}) and stopped!")

    # TEST 2: HOLD (>= 0.2s) -> Should move multiple blocks continuously!
    t += 0.5
    start_hold_c = p.c
    p.on_press(0, 1, t)
    # Hold for 0.40s
    for _ in range(25):
        t += 0.016
        p.update(maze, 0.016, t)
    p.on_release(0.40, t)

    # Allow finishing current block
    for _ in range(15):
        t += 0.016
        p.update(maze, 0.016, t)

    assert p.c > start_hold_c + 1, f"Player should move multiple blocks when held, but is at {p.c}"
    print(f"[OK] Hold (>= 0.2s) moved continuously (from {start_hold_c} to {p.c})!")

    print("\nALL TAP VS HOLD TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
