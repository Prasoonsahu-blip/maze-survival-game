"""
Test tap vs hold timing logic.
"""

import time

class MockController:
    def __init__(self):
        self.key_down = False
        self.press_time = 0.0
        self.release_time = 0.0
        self.press_duration = 0.0

    def on_press(self):
        self.key_down = True
        self.press_time = time.time()

    def on_release(self):
        self.key_down = False
        self.release_time = time.time()
        self.press_duration = self.release_time - self.press_time

    def is_tap(self):
        return not self.key_down and self.press_duration < 0.20

    def is_holding(self):
        return self.key_down and (time.time() - self.press_time >= 0.20)

ctrl = MockController()
ctrl.on_press()
time.sleep(0.08) # 80ms tap
ctrl.on_release()
assert ctrl.is_tap() == True
assert ctrl.is_holding() == False
print("[OK] 80ms tap detected as tap!")

ctrl.on_press()
time.sleep(0.22) # 220ms hold
assert ctrl.is_holding() == True
ctrl.on_release()
assert ctrl.is_tap() == False
print("[OK] 220ms hold detected as hold!")
