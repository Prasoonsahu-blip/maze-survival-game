"""
Test all powerup pickups to ensure no NameError or runtime exceptions occur.
"""

import tkinter as tk
from game import MazeSurvivalGame
from items import ItemType

def test_all_item_pickups():
    root = tk.Tk()
    root.withdraw()
    app = MazeSurvivalGame(root)
    app.start_new_game()

    # Place player at (1, 1)
    app.player.r, app.player.c = 1, 1
    app.player.px = 1 * 28 + 14
    app.player.py = 1 * 28 + 14

    for itype in [ItemType.GEM, ItemType.EMP, ItemType.SPEED, ItemType.SHIELD]:
        print(f"Testing pickup for {itype}...")
        app.items = []
        app._spawn_random_item(forced_type=itype)
        app.items[0].pos = (1, 1)
        
        # Trigger frame update
        app._update_playing(0.016)
        print(f"[OK] {itype} picked up successfully with zero errors!")

    app._on_closing()
    print("ALL POWERUP PICKUPS PASSED CLEANLY!")

if __name__ == "__main__":
    test_all_item_pickups()
