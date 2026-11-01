"""Combat rules, incremental log reader and DSX localhost protocol."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import socket
import time

PREFIX = "[KCDDSX] "


def trigger_packet(index: int, strength: int, trigger: int = 2) -> dict:
    # Official DSX v3.1+: TriggerUpdate=1, Left=1, Right=2, OFF=20, FEEDBACK=21.
    parameters = [index, trigger, 21, 1, strength] if strength else [index, trigger, 20]
    return {"instructions": [{"type": 1, "parameters": parameters}]}


def effects_packet(index: int, left: int, right: int) -> dict:
    return {"instructions": (trigger_packet(index, left, 1)["instructions"]
                             + trigger_packet(index, right, 2)["instructions"])}


def reset_packet(index: int) -> dict:
    return {"instructions": [{"type": 7, "parameters": [index]}]}


class DSX:
    def __init__(self, port=6969):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.connect(("127.0.0.1", port))
        self.sock.settimeout(2)
        self.last_send = 0.0
        self.acks = 0

    def send(self, packet):
        self.last_send = time.perf_counter()
        self.sock.send(json.dumps(packet, separators=(",", ":")).encode("ascii"))

    def status(self):
        self.send({"instructions": [{"type": 0, "parameters": []}]})
        result = json.loads(self.sock.recv(65535))
        return {
            "roundtrip_ms": round((time.perf_counter() - self.last_send) * 1000, 2),
            "connected": result.get("isControllerConnected", False),
            "status": result.get("Status"),
            "devices": [
                {"index": d.get("Index"), "adaptive_triggers": d.get("IsSupportAT")}
                for d in result.get("Devices", [])
            ],
        }

    def drain(self):
        self.sock.setblocking(False)
        while True:
            try:
                response = json.loads(self.sock.recv(65535))
                if response.get("Status"):
                    self.acks += 1
            except (BlockingIOError, ConnectionResetError, json.JSONDecodeError):
                break


class CombatController:
    def __init__(self, send, index=0, clock=time.monotonic, stale_seconds=2.0):
        self.send = send
        self.index = index
        self.clock = clock
        self.stale_seconds = stale_seconds
        self.session = None
        self.sequence = -1
        self.last_telemetry = None
        self.last_effect = None
        self.last_refresh = 0.0
        self.owned = False
        self.samples = 0
        self.transitions = []

    def neutral(self, reason):
        if self.owned:
            self.send(effects_packet(self.index, 0, 0))
            self.transitions.append({"event": reason, "strength": 0, "left_strength": 0})
        self.last_effect = None
        self.owned = False

    def accept(self, message):
        if message.get("v") != 1 or not isinstance(message.get("session"), str):
            return False
        seq = message.get("seq")
        if not isinstance(seq, int) or seq < 1:
            return False
        if message.get("state") not in ("idle", "drawing", "ready"):
            return False
        if message["session"] != self.session:
            self.neutral("session_change")
            self.session, self.sequence = message["session"], -1
        if seq <= self.sequence:
            return False
        self.sequence = seq
        self.samples += 1
        now = self.clock()
        self.last_telemetry = now
        event = str(message.get("event", ""))
        if event.startswith("stop_"):
            self.neutral(event)
            return True
        mode = message.get("mode", "bow" if message.get("bow") is True else "none")
        active = ((message.get("drawn") is True or mode == "unarmed")
                  and message.get("suspended") is False and message.get("usable") is True)
        left, right = 0, 0
        if active and mode == "bow":
            # Preserve preloaded bow resistance; melee fatigue must never override it.
            right = {"idle": 3, "drawing": 3, "ready": 4}[message["state"]]
        elif active and mode in ("melee", "unarmed"):
            ratio = message.get("stamina_ratio")
            if isinstance(ratio, (int, float)) and not isinstance(ratio, bool) and math.isfinite(ratio):
                ratio = min(1.0, max(0.0, ratio))
                # Keep the opening swings light; fatigue starts below 80% stamina.
                left = right = 0 if ratio >= 0.8 else 1 + int(((0.8 - ratio) / 0.8) * 5 + 0.5)
        effect = (left, right)
        # Update immediately on transitions and refresh the active effect twice a second.
        if effect != self.last_effect or (any(effect) and now - self.last_refresh >= 0.45):
            self.send(effects_packet(self.index, left, right))
            if effect != self.last_effect:
                self.transitions.append({"seq": seq, "event": event, "state": message["state"],
                                         "mode": mode, "strength": right, "left_strength": left,
                                         "stamina_ratio": message.get("stamina_ratio")})
            self.last_effect, self.last_refresh, self.owned = effect, now, True
        return True

    def watchdog(self):
        if self.last_telemetry is not None and self.clock() - self.last_telemetry > self.stale_seconds:
            self.neutral("telemetry_timeout")
            self.last_telemetry = None


class FreshLog:
    """Ignore existing log contents; reopen when the game rotates/truncates its log."""
    def __init__(self, path):
        self.path = Path(path)
        self.file = None
        self.identity = None
        self.pending = b""
        self.initial = True

    def read_lines(self):
        try:
            stat = self.path.stat()
        except FileNotFoundError:
            return []
        identity = (stat.st_dev, stat.st_ino)
        if self.file is None or identity != self.identity or stat.st_size < self.file.tell():
            if self.file:
                self.file.close()
            self.file = self.path.open("rb")
            self.identity, self.pending = identity, b""
            if self.initial:
                self.file.seek(0, os.SEEK_END)
                self.initial = False
        self.pending += self.file.read(65536)
        parts = self.pending.split(b"\n")
        self.pending = parts.pop()
        if len(self.pending) > 65536:
            self.pending = b""
        return [line.decode("utf-8", errors="replace") for line in parts]


def parse_line(line):
    offset = line.find(PREFIX)
    if offset < 0:
        return None
    try:
        value = json.loads(line[offset + len(PREFIX):])
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None

