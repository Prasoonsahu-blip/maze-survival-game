"""
Power-ups and bonus collectible items scattered in the maze.
"""

import time
import random
from typing import Tuple, Optional
from constants import (
    COLOR_ITEM_EMP, COLOR_ITEM_SPEED, COLOR_ITEM_GEM, COLOR_ITEM_SHIELD
)

class ItemType:
    GEM = "GEM"
    EMP = "EMP"
    SPEED = "SPEED"
    SHIELD = "SHIELD"

class Item:
    def __init__(self, item_type: str, pos: Tuple[int, int]):
        self.item_type = item_type
        self.pos = pos  # (row, col)
        self.spawn_time = time.time()
        self.lifetime = 18.0  # items disappear after 18 seconds if not picked up
        
        if item_type == ItemType.GEM:
            self.color = COLOR_ITEM_GEM
            self.symbol = "◆"
            self.name = "+500 PTS"
        elif item_type == ItemType.EMP:
            self.color = COLOR_ITEM_EMP
            self.symbol = "⚡"
            self.name = "+1 EMP"
        elif item_type == ItemType.SPEED:
            self.color = COLOR_ITEM_SPEED
            self.symbol = "»"
            self.name = "SPEED BOOST"
        elif item_type == ItemType.SHIELD:
            self.color = COLOR_ITEM_SHIELD
            self.symbol = "🛡"
            self.name = "SHIELD"

    def is_expired(self) -> bool:
        return (time.time() - self.spawn_time) > self.lifetime
