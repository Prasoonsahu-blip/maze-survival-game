"""
Automated headless simulation of the full Tkinter Game loop.
"""

import tkinter as tk
import time
from game import MazeSurvivalGame

def test_full_game_loop():
    print("Initializing Tkinter root...")
    root = tk.Tk()
    root.withdraw()  # Hide window during test
    app = MazeSurvivalGame(root)

    print("Testing Start Game transition...")
    app.start_new_game()
    assert app.state == MazeSurvivalGame.STATE_PLAYING
    assert app.player is not None
    assert len(app.killers) == 3

    print("Simulating 60 frames of gameplay...")
    for frame in range(60):
        # Steer player right
        if frame == 10:
            app.player.set_desired_direction(0, 1)
        # Dash
        if frame == 20:
            app.player.trigger_dash()
        # Trigger EMP
        if frame == 30:
            app.trigger_emp()

        # Execute internal updates and renders
        app._update_playing(0.016)
        app._render()
        root.update_idletasks()
        root.update()

    print(f"Survival Score after 60 frames: {int(app.score)}")
    print(f"Elapsed Time: {app.elapsed_time:.2f}s")
    assert app.score > 0, "Score should have increased"

    print("Testing Game Over transition...")
    app._trigger_game_over(app.killers[0])
    assert app.state == MazeSurvivalGame.STATE_GAMEOVER
    app._render()
    root.update_idletasks()
    root.update()

    app._on_closing()
    print("[OK] Full simulation completed with 0 errors!")

if __name__ == "__main__":
    test_full_game_loop()
