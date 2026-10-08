"""Echoic, iconic, dual or triple window."""
from __future__ import annotations
import time
from collections import deque

class Memory:
    def __init__(self, mode: str = "triple"):
        self.mode = mode if mode in ("dual", "triple") else "triple"
        self.echoic = deque(maxlen=12)
        self.iconic = None
        self.working = deque(maxlen=8)
        self.episodic = []
        self.identity = {"name": "G2P-SDA", "parents": ["serana", "danny", "bel"], "rule": "traits only increase"}

    def observe(self, role: str, text: str, salient: bool = False) -> None:
        item = {"role": role, "text": text[:500], "t": time.time()}
        self.echoic.append(item)
        self.working.append(item)
        if salient or len(text) > 240:
            self.iconic = {"label": text[:120], "t": item["t"], "role": role}
            self.episodic.append(item)
            self.episodic = self.episodic[-200:]

    def dump(self) -> dict:
        windows = {"working": list(self.working), "episodic": self.episodic[-20:]}
        if self.mode == "triple":
            windows["identity"] = self.identity
        return {"mode": self.mode, "echoic": list(self.echoic), "iconic": self.iconic, "windows": windows}
