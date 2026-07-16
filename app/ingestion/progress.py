"""
In-place status line for ingestion loops.

Apps with no storefront page / no achievements are a normal, uninteresting
outcome, and there are enough of them to bury the real output. Instead of one
line each, they collapse into a single line that redraws in place with a live
elapsed timer.

Anything worth keeping in the scrollback goes through StatusLine.log(), which
clears the status line first so the two don't collide. When stdout isn't a
terminal (piped to a file, CI), the live line is skipped and only a final
summary is printed.
"""

import sys
import threading
import time


def format_elapsed(seconds):
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m {secs:02d}s"


class StatusLine:
    """A single self-updating line: label, elapsed timer, and a skip counter."""

    def __init__(self, label, skip_label="skipped", stream=None, tick=0.25):
        self._label = label
        self._skip_label = skip_label
        self._stream = stream or sys.stdout
        self._tick = tick
        self._live = hasattr(self._stream, "isatty") and self._stream.isatty()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._start = time.perf_counter()
        self._skips = 0
        self._width = 0  # chars written last redraw, so we can blank them out

    def __enter__(self):
        if self._live:
            self._thread = threading.Thread(target=self._tick_loop, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._thread is not None:
            self._thread.join()
        with self._lock:
            self._clear()
            elapsed = format_elapsed(time.perf_counter() - self._start)
            print(
                f"{self._label} — {elapsed}, {self._skips} {self._skip_label}",
                file=self._stream,
            )
        return False

    def skip(self):
        """Record one skipped app; shows up as a count on the status line."""
        with self._lock:
            self._skips += 1
            self._redraw()

    def log(self, message):
        """Print a line that stays in the scrollback."""
        with self._lock:
            self._clear()
            print(message, file=self._stream)
            self._redraw()

    def _tick_loop(self):
        while not self._stop.wait(self._tick):
            with self._lock:
                self._redraw()

    def _redraw(self):
        if not self._live:
            return
        elapsed = format_elapsed(time.perf_counter() - self._start)
        text = f"{self._label} — {elapsed} ({self._skips} {self._skip_label})"
        self._stream.write("\r" + text)
        self._stream.flush()
        self._width = len(text)

    def _clear(self):
        if not self._live or not self._width:
            return
        self._stream.write("\r" + " " * self._width + "\r")
        self._stream.flush()
        self._width = 0
