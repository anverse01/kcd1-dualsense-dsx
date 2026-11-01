"""Portable bridge worker. Local game log -> localhost DSX UDP only."""
from __future__ import annotations

import json
import os
from pathlib import Path
import threading
import time

from kcd_dsx_bridge import CombatController, DSX, FreshLog, parse_line, reset_packet

VERSION = "0.5.0"


def valid_game(path):
    return (Path(path) / "Bin" / "Win64" / "KingdomCome.exe").is_file()


def find_game(start):
    path = Path(start).resolve()
    for parent in (path, *path.parents):
        if valid_game(parent):
            return parent
    return None


def user_data():
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / "KCDDSX"


def run_bridge(game, port, controller, stop: threading.Event, notify):
    """notify(kind, value) is called from the worker; UI must queue it."""
    if not valid_game(game):
        raise ValueError("Select the KingdomComeDeliverance folder containing Bin/Win64/KingdomCome.exe.")
    client = DSX(port)
    follower = None
    control = CombatController(client.send, controller)
    connected = False
    try:
        status = client.status()
        if not any(d["index"] == controller and d["adaptive_triggers"] for d in status["devices"]):
            raise RuntimeError("DSX did not report an adaptive-trigger controller at this index.")
        connected = True
        notify("connected", status)
        follower = FreshLog(Path(game) / "kcd.log")
        # Establish EOF before announcing readiness, including an already-running game.
        follower.read_lines()
        notify("waiting", None)
        while not stop.is_set():
            for line in follower.read_lines():
                message = parse_line(line)
                if message and control.accept(message):
                    notify("telemetry", message)
            control.watchdog()
            client.drain()
            for transition in control.transitions:
                notify("effect", transition)
            control.transitions.clear()
            stop.wait(0.02)
    finally:
        try:
            if connected:
                try:
                    control.neutral("bridge_exit")
                finally:
                    client.send(reset_packet(controller))
        finally:
            if follower and follower.file:
                follower.file.close()
            client.sock.close()
            notify("stopped", None)


def load_settings(directory):
    try:
        value = json.loads((Path(directory) / "settings.json").read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(directory, settings):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / "settings.tmp"
    temporary.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(directory / "settings.json")
