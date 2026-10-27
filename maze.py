"""
Procedural maze generator with cycles, connectivity guarantees,
and pathfinding utilities (BFS, Line-of-Sight, Distance).
"""

import random
from collections import deque
from typing import List, Tuple, Optional, Set

class Maze:
    WALL = 0
    PATH = 1

    def __init__(self, rows: int, cols: int, loop_factor: float = 0.12):
        # Ensure dimensions are odd
        self.rows = rows if rows % 2 == 1 else rows + 1
        self.cols = cols if cols % 2 == 1 else cols + 1
        self.loop_factor = loop_factor
        self.grid: List[List[int]] = []
        self.open_cells: List[Tuple[int, int]] = []
        self.generate()

    def generate(self):
        """Generates a perfect maze using DFS backtracker, then carves loops."""
        # Initialize grid with all walls
        self.grid = [[self.WALL for _ in range(self.cols)] for _ in range(self.rows)]
        
        # Start carving from (1, 1)
        start_r, start_c = 1, 1
        self.grid[start_r][start_c] = self.PATH
        
        stack = [(start_r, start_c)]
        visited = {(start_r, start_c)}

        directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]

        while stack:
            curr_r, curr_c = stack[-1]
            random.shuffle(directions)
            carved = False

            for dr, dc in directions:
                nr, nc = curr_r + dr, curr_c + dc
                if 1 <= nr < self.rows - 1 and 1 <= nc < self.cols - 1:
                    if (nr, nc) not in visited:
                        # Carve passage between curr and neighbor
                        wall_r = curr_r + dr // 2
                        wall_c = curr_c + dc // 2
                        self.grid[wall_r][wall_c] = self.PATH
                        self.grid[nr][nc] = self.PATH
                        visited.add((nr, nc))
                        stack.append((nr, nc))
                        carved = True
                        break

            if not carved:
                stack.pop()

        # Add loops by removing interior walls that separate open paths
        interior_walls = []
        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):
                if self.grid[r][c] == self.WALL:
                    # Check horizontal wall between two paths
                    if self.grid[r - 1][c] == self.PATH and self.grid[r + 1][c] == self.PATH:
                        interior_walls.append((r, c))
                    # Check vertical wall between two paths
                    elif self.grid[r][c - 1] == self.PATH and self.grid[r][c + 1] == self.PATH:
                        interior_walls.append((r, c))

        num_loops_to_add = int(len(interior_walls) * self.loop_factor)
        random.shuffle(interior_walls)
        for r, c in interior_walls[:num_loops_to_add]:
            self.grid[r][c] = self.PATH

        # Cache open cells
        self.open_cells = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if self.grid[r][c] == self.PATH
        ]

    def is_path(self, r: int, c: int) -> bool:
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.grid[r][c] == self.PATH
        return False

    def get_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Returns valid adjacent walkable cells (up, down, left, right)."""
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if self.is_path(nr, nc):
                neighbors.append((nr, nc))
        return neighbors

    def get_random_open_cell(self, min_dist_from: Optional[Tuple[int, int]] = None, min_dist: int = 8) -> Tuple[int, int]:
        """Returns a random open cell, optionally far away from a specified location."""
        if not min_dist_from:
            return random.choice(self.open_cells)
        
        target_r, target_c = min_dist_from
        candidates = [
            (r, c) for (r, c) in self.open_cells
            if (abs(r - target_r) + abs(c - target_c)) >= min_dist
        ]
        if candidates:
            return random.choice(candidates)
        return random.choice(self.open_cells)

    def bfs_next_step(self, start: Tuple[int, int], target: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Calculates the first step on the shortest path from start to target using BFS.
        Returns the adjacent cell to move towards, or None if already there or no path.
        """
        if start == target:
            return None

        queue = deque([start])
        visited: Set[Tuple[int, int]] = {start}
        parent = {}

        found = False
        while queue:
            curr = queue.popleft()
            if curr == target:
                found = True
                break

            for nxt in self.get_neighbors(curr[0], curr[1]):
                if nxt not in visited:
                    visited.add(nxt)
                    parent[nxt] = curr
                    queue.append(nxt)

        if not found:
            return None

        # Reconstruct path back to start
        curr = target
        while curr in parent and parent[curr] != start:
            curr = parent[curr]

        return curr

    def has_line_of_sight(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> bool:
        """
        Checks if p1 and p2 have direct, unobstructed line of sight along a straight corridor.
        """
        r1, c1 = p1
        r2, c2 = p2

        if r1 == r2:
            step = 1 if c2 > c1 else -1
            for c in range(c1 + step, c2, step):
                if not self.is_path(r1, c):
                    return False
            return True
        elif c1 == c2:
            step = 1 if r2 > r1 else -1
            for r in range(r1 + step, r2, step):
                if not self.is_path(r, c1):
                    return False
            return True

        return False

    @staticmethod
    def manhattan(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
