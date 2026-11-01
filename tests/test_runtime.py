import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from runtime import find_game, load_settings, run_bridge, save_settings
from kcd_dsx_bridge import effects_packet, reset_packet
from lupa.lua51 import LuaRuntime


class RuntimeTests(unittest.TestCase):
    def test_portable_detection_settings_and_no_game_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory) / "游戏 folder"
            (game / "Bin/Win64").mkdir(parents=True)
            (game / "Bin/Win64/KingdomCome.exe").touch()
            location = game / "Mods/KCDDSX"
            location.mkdir(parents=True)
            # Windows runners may spell TEMP with an 8.3 user-directory alias.
            self.assertEqual(find_game(location), game.resolve())
            state = Path(directory) / "settings"
            self.assertEqual(load_settings(state), {})
            expected = {"game_root": str(game), "port": 6969}
            save_settings(state, expected)
            self.assertEqual(load_settings(state), expected)
            (state / "settings.json").write_text("broken", encoding="utf-8")
            self.assertEqual(load_settings(state), {})
            self.assertEqual(list(location.iterdir()), [])

    def test_independent_startup_loads_each_save_without_duplicate_registration(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
        registrations=0; reloads=0; logs={}
        UIAction={RegisterActionListener=function() registrations=registrations+1 end}
        System={LogAlways=function(text) table.insert(logs,text) end}
        Script={ReloadScript=function(path)
          assert(path=='Scripts/KCDDSX/combat.lua'); reloads=reloads+1 end}
        ''')
        code = (ROOT / "src/startup.lua").read_text(encoding="utf-8")
        lua.execute(code)
        lua.execute(code)
        lua.execute("KCDDSXLoader:onScene('Game','PauseGame'); assert(reloads==0)")
        lua.execute("KCDDSXLoader:onScene('sys_loadingimagescreen','OnEnd')")
        lua.execute("KCDDSXLoader:onScene('sys_loadingimagescreen','OnEnd')")
        self.assertEqual(lua.globals().registrations, 1)
        self.assertEqual(lua.globals().reloads, 2)

    def test_worker_with_fake_dsx_fresh_telemetry_and_profile_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "Bin/Win64").mkdir(parents=True)
            (game / "Bin/Win64/KingdomCome.exe").touch()
            log = game / "kcd.log"
            log.write_text("old contents\n", encoding="utf-8")
            server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server.bind(("127.0.0.1", 0))
            server.settimeout(.1)
            server_stop = threading.Event()
            packets, errors = [], []
            def dsx():
                while not server_stop.is_set():
                    try:
                        raw, address = server.recvfrom(65535)
                    except socket.timeout:
                        continue
                    packet = json.loads(raw)
                    packets.append(packet)
                    reply = {"Status":"ok", "isControllerConnected":True,
                             "Devices":[{"Index":0,"IsSupportAT":True}]}
                    server.sendto(json.dumps(reply).encode(), address)
            server_thread = threading.Thread(target=dsx)
            server_thread.start()
            stop, ready, effect = threading.Event(), threading.Event(), threading.Event()
            def notify(kind, value):
                if kind == "waiting": ready.set()
                if kind == "effect" and value.get("strength") == 4: effect.set()
            def bridge():
                try:
                    run_bridge(game, server.getsockname()[1], 0, stop, notify)
                except Exception as exc:
                    errors.append(exc)
            worker = threading.Thread(target=bridge)
            worker.start()
            try:
                self.assertTrue(ready.wait(3), "bridge never connected")
                msg = dict(v=1, session="fake-game", seq=1, state="idle", event="heartbeat",
                           mode="unarmed", drawn=False, usable=True, suspended=False, stamina_ratio=.4)
                with log.open("a", encoding="utf-8") as output:
                    output.write("[KCDDSX] " + json.dumps(msg) + "\n")
                self.assertTrue(effect.wait(3), "no fatigue packet")
            finally:
                stop.set()
                worker.join(4)
                deadline = time.monotonic() + 1
                while reset_packet(0) not in packets and time.monotonic() < deadline:
                    time.sleep(.01)
                server_stop.set()
                server_thread.join(2)
                server.close()
            self.assertFalse(worker.is_alive())
            self.assertEqual(errors, [])
            self.assertIn(effects_packet(0, 4, 4), packets)
            self.assertIn(effects_packet(0, 0, 0), packets)
            self.assertEqual(packets[-1], reset_packet(0))


if __name__ == "__main__":
    unittest.main()
