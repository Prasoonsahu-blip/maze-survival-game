# 🕹️ Maze Survival: 3 Killers

An adrenaline-pumping survival arcade game built in Python using standard libraries (`tkinter` & `winsound`). 
You control the **GREEN sphere (YOU)** inside a procedurally generated maze. Evade the 3 relentless killers for as long as possible — the longer you survive, the higher your score climbs!

---

## 🖥️ Modernized, Minimalist Presentation

- **Decluttered Opening Screen**: Features a sleek cyberpunk title, glowing player spotlight ("YOU ARE GREEN"), and interactive hover buttons.
- **Dedicated Rules & Controls Screen**: Click the `[ 📜 HOW TO PLAY & RULES ]` button (or press `H`) to review objectives, scoring, controls, and power-up info.
- **Top-Right High Score**: Your all-time record and best survival time are anchored in the top-right corner of both the Menu and the In-Game HUD.
- **Simplified In-Game Labeling**: The player is clearly labeled as **"YOU"**, with all killer name tags removed for a clean, immersive screen.

---

## 🎮 Objective & Scoring Mechanics

- **Time-Based Score**: You gain points every millisecond you stay alive.
- **Dynamic Multiplier (up to 3.0x)**: Continuous movement and traversing new areas amplifies your points multiplier.
- **Anti-Camping System**: Staying in the same corridor or dead-end drops your multiplier to `0.5x` with an **IDLE PENALTY** warning.
- **Narrow Escapes (+400 PTS)**: Close-call dodges within 2 tiles of a killer without getting caught award bonus points and sound alerts.
- **Collectibles**: Pick up crystals for instant points, EMP charges, shields, and speed boosts!
- **Persistent High Score**: Best scores and longest survival times are automatically saved to `maze_survival_highscore.json`.

---

## ⌨️ Controls & Steering

| Input | Action |
| :--- | :--- |
| **W, A, S, D** or **Arrow Keys** | **Fluid Steer / Move** (Supports continuous key holding, pre-turn corner buffering, and instant 180° reversal) |
| **SPACEBAR** | **Sprint Dash** (Temporary burst of speed, has cooldown) |
| **F** or **E** | **EMP Flashbang** (Stuns all killers for 3.5 seconds) |
| **P** | Pause / Resume |
| **M** | Toggle Retro Sound FX (Windows `winsound`) |
| **Mouse Click** | Interact with buttons on Menu, Rules, and Game Over screens |
| **R** | Restart game upon Game Over |
| **ESC** | Return to Main Menu / Back from Rules |

### 🔄 Responsive Steering & Corner Sliding
- **Pre-Turn Buffering**: Tapping or holding a turn key before you reach an opening remembers your intent and rounds the corner the exact moment the turn opens up.
- **Corridor Centering**: Moving through passages automatically nudges the player to the centerline, preventing wall-snagging.
- **Instant Reversal**: Pressing the opposite direction flips your movement immediately without delay.
- **Multi-Key Holding**: Holding one direction while tapping or holding another smoothly transitions between routes.

---

## ⚡ Power-Ups & Collectibles

Periodic power-ups spawn throughout the maze:
- **`◆` Pink Gem**: Awards `+500` bonus points (multiplied by your current combo multiplier).
- **`⚡` Cyan EMP Battery**: Adds `+1` EMP charge (up to max 3 charges).
- **`»` Gold Speed Bolt**: Increases player movement speed for 6 seconds.
- **`🛡` Blue Shield**: Grants a temporary barrier that absorbs 1 lethal attack!

---

## 🚀 How to Run the Game

### Method 1: Double-Click
Double-click `run_game.bat` inside the folder.

### Method 2: Command Line
Open a terminal in this directory and execute:
```bash
python main.py
```

*Requirements: Python 3.8+ (No external pip packages required! Runs 100% on standard library).*

---

## 📂 File Architecture

- [main.py](file:///C:/Users/praso/.gemini/antigravity/scratch/maze_survival/main.py): High-DPI initialization and entry point.
- [game.py](file:///C:/Users/praso/.gemini/antigravity/scratch/maze_survival/game.py): Core game loop, double-buffered Tkinter canvas rendering, HUD, particle effects, and game state management.
- [maze.py](file:///C:/Users/praso/.gemini/antigravity/scratch/maze_survival/maze.py): Procedural maze generator using recursive backtracker with added cycle loops and BFS pathfinding.
- [entities.py](file:///C:/Users/praso/.gemini/antigravity/scratch/maze_survival/entities.py): Player controls, sprint mechanics, and the 3 distinct Killer AI classes (Stalker, Phantom, Beast).
- [items.py](file:///C:/Users/praso/.gemini/antigravity/scratch/maze_survival/items.py): Collectibles (Gems, EMP batteries, Speed boots, Shields).
- [audio.py](file:///C:/Users/praso/.gemini/antigravity/scratch/maze_survival/audio.py): Multi-threaded, non-blocking retro sound manager using Windows `winsound`.
- [constants.py](file:///C:/Users/praso/.gemini/antigravity/scratch/maze_survival/constants.py): Colors, timing, grid sizes, and game balance constants.
