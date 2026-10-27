"""
Validation for hold-to-move steering: a tap moves exactly one cell, releasing stops,
holding runs, and turns work at every junction.
"""

from maze import Maze
from entities import Player
from constants import CELL_SIZE

DT = 0.016


def run(player, maze, frames):
    for _ in range(frames):
        player.update(maze, dt=DT)


def settle(player, maze, max_frames=200):
    """Run until the player is standing still on a cell."""
    for _ in range(max_frames):
        player.update(maze, dt=DT)
        if not player.is_moving():
            return
    raise AssertionError("player never stopped")


def make_corridor_maze():
    """Open 5x9 box so tests are deterministic: row 1..3, col 1..7 open, ring of walls."""
    m = Maze(5, 9, loop_factor=0.0)
    for r in range(m.rows):
        for c in range(m.cols):
            m.grid[r][c] = Maze.PATH if (1 <= r <= 3 and 1 <= c <= 7) else Maze.WALL
    m.open_cells = [(r, c) for r in range(m.rows) for c in range(m.cols) if m.grid[r][c] == Maze.PATH]
    return m


def test_tap_moves_exactly_one_cell():
    m = make_corridor_maze()
    p = Player((2, 2))
    p.set_desired_direction(0, 1)      # tap, never held
    settle(p, m)
    assert (p.r, p.c) == (2, 3), f"tap should move exactly 1 cell, ended at {(p.r, p.c)}"
    run(p, m, 30)
    assert (p.r, p.c) == (2, 3), "player must stay put after the tap"
    print("[OK] A tap moves exactly one cell and stops.")


def test_hold_runs_and_release_stops():
    m = make_corridor_maze()
    p = Player((2, 1))
    p.set_held_directions([(0, 1)])
    p.set_desired_direction(0, 1)
    run(p, m, 20)
    assert p.c >= 3, "holding should keep the player running"
    p.set_held_directions([])          # key released mid-run
    start = (p.r, p.c, p.target_c)
    settle(p, m)
    # may finish the cell it is crossing, but never more than one extra cell
    assert p.c - start[1] <= 1 and not p.is_moving()
    c_stop = p.c
    run(p, m, 30)
    assert p.c == c_stop, "must not drift after release"
    print("[OK] Holding runs; releasing stops within the current cell.")


def test_release_stops_before_wall_corridor_end():
    """The old bug: one tap ran all the way to the wall."""
    m = make_corridor_maze()
    p = Player((2, 1))
    p.set_desired_direction(0, 1)
    settle(p, m)
    assert p.c == 2, "tap must not auto-run to the far wall (col 7)"
    print("[OK] No auto-run to the wall after a tap.")


def test_instant_reversal():
    m = make_corridor_maze()
    p = Player((2, 2))
    p.set_held_directions([(0, 1)])
    p.set_desired_direction(0, 1)
    run(p, m, 3)                       # partway into the cell to the right
    assert p.is_moving() and p.dir_c == 1
    p.set_held_directions([(0, -1), (0, 1)])
    p.set_desired_direction(0, -1)
    p.update(m, dt=DT)
    assert p.dir_c == -1, "opposite key should reverse immediately mid-cell"
    print("[OK] Instant 180-degree reversal works.")


def test_turn_at_junction_and_release_turn_key_resumes():
    m = make_corridor_maze()
    p = Player((2, 1))
    p.set_held_directions([(0, 1)])
    p.set_desired_direction(0, 1)
    run(p, m, 3)
    # tap down while still holding right; down is open here so we turn at the next cell
    p.set_held_directions([(1, 0), (0, 1)])
    p.set_desired_direction(1, 0)
    for _ in range(20):
        p.update(m, dt=DT)
        if p.dir_r == 1:
            break
    assert p.dir_r == 1, "should turn down at the next cell"
    # release down, right still held -> goes back to right
    p.set_held_directions([(0, 1)])
    for _ in range(40):
        p.update(m, dt=DT)
        if p.dir_c == 1:
            break
    assert p.dir_c == 1, "after releasing the turn key the held key takes over again"
    print("[OK] Turns at junctions and falls back to the still-held key.")


def test_blocked_turn_key_does_not_stop_player():
    """Holding right + pressing up into a wall must keep running right (corner assist)."""
    m = make_corridor_maze()
    p = Player((1, 1))                 # row 1 has a wall above
    p.set_held_directions([(-1, 0), (0, 1)])
    p.set_desired_direction(-1, 0)
    run(p, m, 20)
    assert p.c > 1 and p.r == 1, "wall-blocked newest key should fall through to the held key"
    print("[OK] Blocked newest key falls through to the older held key.")


def test_quick_direction_switching_on_random_maze():
    """Tap-tap-tap through a real maze: every tap = one cell, no overshoot."""
    import random
    random.seed(7)
    maze = Maze(23, 31, loop_factor=0.18)
    p = Player((1, 1))
    for _ in range(300):
        dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        open_dirs = [d for d in dirs if maze.is_path(p.r + d[0], p.c + d[1])]
        d = random.choice(open_dirs)
        before = (p.r, p.c)
        p.set_desired_direction(*d)
        settle(p, maze)
        assert (p.r - before[0], p.c - before[1]) == d, f"tap {d} from {before} ended at {(p.r, p.c)}"
    print("[OK] 300 random taps in a real maze: each moved exactly one cell.")


if __name__ == "__main__":
    test_tap_moves_exactly_one_cell()
    test_hold_runs_and_release_stops()
    test_release_stops_before_wall_corridor_end()
    test_instant_reversal()
    test_turn_at_junction_and_release_turn_key_resumes()
    test_blocked_turn_key_does_not_stop_player()
    test_quick_direction_switching_on_random_maze()
    print("\nALL MOVEMENT TESTS PASSED!")
