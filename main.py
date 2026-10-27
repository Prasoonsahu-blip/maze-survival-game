"""
Main entry point for Maze Survival: 3 Killers.
Run this file to launch the game:
    python main.py
"""

import sys
import os
import tkinter as tk

# Enable High DPI scaling on Windows if available
if sys.platform == "win32":
    try:
        import ctypes
        # SetProcessDpiAwareness: 1 = System DPI aware, 2 = Per-monitor DPI aware
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from game import MazeSurvivalGame

def main():
    root = tk.Tk()
    app = MazeSurvivalGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
