"""
Sound effects manager using Python's standard library `winsound`.
Runs asynchronously in a background thread to prevent UI freezing.
"""

import threading
import queue
import time
import sys

class SoundManager:
    def __init__(self):
        self.enabled = True
        self.queue = queue.Queue(maxsize=10)
        self.worker_thread = None
        self.running = False
        self.has_winsound = False
        
        if sys.platform == "win32":
            try:
                import winsound
                self._winsound = winsound
                self.has_winsound = True
            except ImportError:
                self.has_winsound = False

        if self.has_winsound:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()

    def toggle_sound(self) -> bool:
        """Toggles sound on or off. Returns current enabled state."""
        self.enabled = not self.enabled
        return self.enabled

    def _play_pattern(self, pattern):
        """Worker function to execute a pattern of (frequency, duration_ms) tuples."""
        if not self.has_winsound:
            return
        try:
            for freq, dur in pattern:
                if not self.enabled:
                    break
                if freq > 0:
                    self._winsound.Beep(freq, dur)
                else:
                    time.sleep(dur / 1000.0)
        except Exception:
            pass

    def _worker(self):
        while self.running:
            try:
                pattern = self.queue.get(timeout=0.5)
                if pattern is None:
                    break
                if self.enabled:
                    self._play_pattern(pattern)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                pass

    def _enqueue(self, pattern):
        if not self.enabled or not self.has_winsound:
            return
        try:
            # Drop older sounds if queue is congested so we stay responsive
            if self.queue.full():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    pass
            self.queue.put_nowait(pattern)
        except queue.Full:
            pass

    # Sound presets
    def play_start(self):
        # Uplifting 3-step arpeggio
        self._enqueue([(523, 80), (659, 80), (784, 120)])

    def play_pickup(self):
        # Crisp high chime
        self._enqueue([(880, 60), (1318, 90)])

    def play_dash(self):
        # Fast ascending woosh
        self._enqueue([(400, 40), (700, 60), (1100, 80)])

    def play_emp(self):
        # Electric discharge pulse
        self._enqueue([(1400, 50), (900, 70), (450, 120)])

    def play_heartbeat(self):
        # Double thud (low frequency)
        self._enqueue([(130, 70), (0, 50), (120, 90)])

    def play_near_miss(self):
        # Exciting high staccato
        self._enqueue([(1046, 50), (1318, 50), (1568, 70)])

    def play_game_over(self):
        # Descending death theme
        self._enqueue([(493, 140), (440, 160), (392, 180), (349, 320)])

    def play_shield_break(self):
        # Glass break vibe
        self._enqueue([(1200, 40), (600, 80), (300, 120)])

    def shutdown(self):
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            try:
                self.queue.put_nowait(None)
            except Exception:
                pass


# Global singleton sound manager
sound_fx = SoundManager()
