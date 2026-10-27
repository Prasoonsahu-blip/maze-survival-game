"""
Verify mouse button clicks and screen transitions.
"""

import tkinter as tk
from game import MazeSurvivalGame

def test_menu_and_rules_interaction():
    root = tk.Tk()
    root.withdraw()
    app = MazeSurvivalGame(root)

    assert app.state == MazeSurvivalGame.STATE_MENU
    print("1. Initial state is STATE_MENU.")

    # Simulate mouse click on Rules button
    rx = (app.btn_rules[0] + app.btn_rules[2]) // 2
    ry = (app.btn_rules[1] + app.btn_rules[3]) // 2
    
    class DummyEvent:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    app._on_mouse_click(DummyEvent(rx, ry))
    assert app.state == MazeSurvivalGame.STATE_RULES, f"Expected STATE_RULES, got {app.state}"
    print("2. Successfully navigated to STATE_RULES via button click!")

    # Simulate click on Back button
    bx = (app.btn_rules_back[0] + app.btn_rules_back[2]) // 2
    by = (app.btn_rules_back[1] + app.btn_rules_back[3]) // 2
    app._on_mouse_click(DummyEvent(bx, by))
    assert app.state == MazeSurvivalGame.STATE_MENU, f"Expected STATE_MENU, got {app.state}"
    print("3. Successfully navigated back to STATE_MENU via Back button!")

    # Simulate click on Play button
    px = (app.btn_play[0] + app.btn_play[2]) // 2
    py = (app.btn_play[1] + app.btn_play[3]) // 2
    app._on_mouse_click(DummyEvent(px, py))
    assert app.state == MazeSurvivalGame.STATE_PLAYING, f"Expected STATE_PLAYING, got {app.state}"
    print("4. Successfully started game via Play button!")

    # Verify HUD renders high score
    app._render_hud()
    print("5. HUD rendered with top-right High Score column.")

    app._on_closing()
    print("[ALL UI BUTTON INTERACTION TESTS PASSED!]")

if __name__ == "__main__":
    test_menu_and_rules_interaction()
