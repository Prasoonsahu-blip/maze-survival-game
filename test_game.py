"""
Headless validation test for Maze Survival game mechanics.
"""

import sys
import time
from constants import GRID_ROWS, GRID_COLS
from maze import Maze
from entities import Player, StalkerKiller, PhantomKiller, BeastKiller
from items import Item, ItemType
from audio import sound_fx

def test_maze_and_connectivity():
    print("Testing Maze generation...")
    maze = Maze(GRID_ROWS, GRID_COLS, loop_factor=0.14)
    assert len(maze.open_cells) > 50, f"Expected >50 open cells, got {len(maze.open_cells)}"
    assert maze.is_path(1, 1), "Start cell (1, 1) should be open path"
    print("[OK] Maze generation & open cell caching passed.")

    # Test BFS
    p1 = maze.open_cells[0]
    p2 = maze.open_cells[-1]
    step = maze.bfs_next_step(p1, p2)
    assert step is not None, f"BFS path between {p1} and {p2} should exist"
    assert maze.is_path(step[0], step[1]), "Next step should be a valid path"
    print("[OK] BFS pathfinding passed.")

def test_entities_and_ai():
    print("Testing Player and Killer AIs...")
    maze = Maze(GRID_ROWS, GRID_COLS, loop_factor=0.14)
    player = Player((1, 1))
    
    # Test player movement
    player.set_desired_direction(0, 1)
    player.last_move_time = 0.0  # Force ready
    player.update(maze)
    print("[OK] Player update passed.")

    # Test Stalker (chaser)
    stalker = StalkerKiller((5, 5))
    stalker.last_move_time = 0.0
    stalker.update_movement(maze, player, elapsed_sec=10.0)
    print("[OK] Stalker AI update passed.")

    # Test Phantom (ambusher)
    phantom = PhantomKiller((7, 7))
    phantom.last_move_time = 0.0
    phantom.update_movement(maze, player, elapsed_sec=10.0)
    print("[OK] Phantom AI update passed.")

    # Test Beast (sprinter / patroller)
    beast = BeastKiller((9, 9))
    beast.last_move_time = 0.0
    beast.update_movement(maze, player, elapsed_sec=10.0)
    print("[OK] Beast AI update passed.")

def test_items_and_abilities():
    print("Testing Items and Abilities...")
    item_gem = Item(ItemType.GEM, (1, 1))
    assert not item_gem.is_expired(), "Item should not be expired on spawn"
    
    player = Player((1, 1))
    assert player.emp_charges == 2
    assert player.trigger_dash() is True, "Player should be able to trigger initial dash"
    assert player.is_dashing is True
    print("[OK] Items and abilities passed.")

def test_audio():
    print("Testing Audio Manager...")
    sound_fx.play_start()
    time.sleep(0.1)
    sound_fx.shutdown()
    print("[OK] Audio manager passed.")

if __name__ == "__main__":
    test_maze_and_connectivity()
    test_entities_and_ai()
    test_items_and_abilities()
    test_audio()
    print("\nALL TEST SUITES PASSED SUCCESSFULLY! Ready to play.")
