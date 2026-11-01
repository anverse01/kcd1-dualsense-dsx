"""Windows portable GUI entry point; Python is included in release builds."""
from __future__ import annotations

import argparse
import ctypes
import json
import locale
from pathlib import Path
import queue
import sys
import threading
import time

from runtime import VERSION, find_game, load_settings, run_bridge, save_settings, user_data


class SingleInstance:
    def __init__(self):
        self.handle = None
        if sys.platform == "win32":
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.CreateMutexW.restype = ctypes.c_void_p
            kernel.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
            self.handle = kernel.CreateMutexW(None, False, "Local\\KCDDSXAdaptiveTriggersBridge")
            if not self.handle:
                raise OSError(ctypes.get_last_error(), "Cannot create bridge mutex")
            if ctypes.get_last_error() == 183:
                self.close()
                raise RuntimeError("KCDDSX Bridge is already running. / 桥接程序已在运行。")

    def close(self):
        if self.handle:
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
            kernel.CloseHandle(self.handle)
            self.handle = None


class BridgeApp:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
        self.root, self.tk, self.ttk = root, tk, ttk
        self.filedialog, self.messagebox = filedialog, messagebox
        self.directory = user_data()
        settings = load_settings(self.directory)
        self.zh = settings.get("language", "zh" if (locale.getlocale()[0] or "").lower().startswith("zh") else "en") == "zh"
        self.events = queue.Queue()
        self.stop = threading.Event()
        self.thread = None
        self.closing = False
        self.last_telemetry = None
        self.online = False
        self.latest_effect = (0, 0)
        executable = Path(sys.executable) if getattr(sys, "frozen", False) else Path(__file__)
        auto = find_game(executable.parent)
        self.game = tk.StringVar(value=str(auto or settings.get("game_root", "")))
        self.port = tk.StringVar(value=str(settings.get("port", 6969)))
        self.controller = tk.StringVar(value=str(settings.get("controller", 0)))
        root.title("KCDDSX Adaptive Triggers · " + VERSION)
        root.geometry("660x420")
        root.minsize(600, 400)
        frame = ttk.Frame(root, padding=22)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="KCDDSX", font=("Segoe UI", 23, "bold")).grid(row=0, column=0, sticky="w")
        self.language_button = ttk.Button(frame, text="English / 中文", command=self.language)
        self.language_button.grid(row=0, column=2, sticky="e")
        self.subtitle = ttk.Label(frame)
        self.subtitle.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 20))
        self.path_label = ttk.Label(frame)
        self.path_label.grid(row=2, column=0, columnspan=3, sticky="w")
        self.path_entry = ttk.Entry(frame, textvariable=self.game)
        self.path_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 12))
        self.browse = ttk.Button(frame, command=self.choose)
        self.browse.grid(row=3, column=2, padx=(10, 0), pady=(5, 12))
        options = ttk.Frame(frame)
        options.grid(row=4, column=0, columnspan=3, sticky="w")
        ttk.Label(options, text="DSX UDP  127.0.0.1 :").pack(side="left")
        self.port_entry = ttk.Entry(options, textvariable=self.port, width=7)
        self.port_entry.pack(side="left", padx=(5, 20))
        ttk.Label(options, text="Controller index:").pack(side="left")
        self.controller_entry = ttk.Entry(options, textvariable=self.controller, width=4)
        self.controller_entry.pack(side="left", padx=5)
        self.status = ttk.Label(frame, wraplength=605, foreground="#175c87")
        self.status.grid(row=5, column=0, columnspan=3, sticky="w", pady=(25, 5))
        self.detail = ttk.Label(frame)
        self.detail.grid(row=6, column=0, columnspan=3, sticky="w")
        buttons = ttk.Frame(frame)
        buttons.grid(row=7, column=0, columnspan=3, sticky="w", pady=(18, 12))
        self.start_button = ttk.Button(buttons, command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(buttons, command=self.request_stop, state="disabled")
        self.stop_button.pack(side="left", padx=10)
        self.hint = ttk.Label(frame, wraplength=610)
        self.hint.grid(row=8, column=0, columnspan=3, sticky="w")
        frame.columnconfigure(1, weight=1)
        self.idle_status = True
        self.labels()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(100, self.poll)
        # Drag into Mods, launch DSX, then double-click: no extra Start click needed.
        if auto:
            root.after(350, self.start)

    def text(self, en, zh):
        return zh if self.zh else en

    def labels(self):
        self.subtitle.config(text=self.text("Kingdom Come: Deliverance · DualSense + DSX", "天国：拯救 1 · DualSense + DSX"))
        self.path_label.config(text=self.text("Game folder", "游戏根目录"))
        self.browse.config(text=self.text("Browse…", "选择…"))
        self.start_button.config(text=self.text("Start bridge", "启动桥接"))
        self.stop_button.config(text=self.text("Stop & restore DSX", "停止并还原 DSX"))
        self.hint.config(text=self.text("Keep DSX running with Incoming UDP enabled. Disable Steam Input for this game. Closing this window stops feedback.", "保持 DSX 运行并启用传入 UDP；关闭本游戏的 Steam 输入。关闭此窗口会停止反馈。"))
        if self.idle_status:
            self.status.config(text=self.text("Ready. Start DSX, then start the bridge.", "准备就绪。先开启 DSX，再启动桥接。"))

    def language(self):
        self.zh = not self.zh
        self.labels()

    def choose(self):
        path = self.filedialog.askdirectory(title=self.text("Select KingdomComeDeliverance", "选择 KingdomComeDeliverance 游戏根目录"))
        if path:
            self.game.set(path)

    def controls(self, running):
        for widget in (self.path_entry, self.browse, self.port_entry, self.controller_entry, self.start_button):
            widget.config(state="disabled" if running else "normal")
        self.stop_button.config(state="normal" if running else "disabled")

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        try:
            port, controller = int(self.port.get()), int(self.controller.get())
            if not 1 <= port <= 65535 or not 0 <= controller <= 15:
                raise ValueError("UDP port: 1–65535; controller index: 0–15")
            from runtime import valid_game
            if not valid_game(self.game.get()):
                raise ValueError(self.text("Select the game root containing Bin/Win64/KingdomCome.exe.", "请选择包含 Bin/Win64/KingdomCome.exe 的游戏根目录。"))
            save_settings(self.directory, {"game_root": self.game.get(), "port": port, "controller": controller, "language": "zh" if self.zh else "en"})
        except (ValueError, OSError) as exc:
            self.messagebox.showerror("KCDDSX", str(exc))
            return
        game = self.game.get()
        self.stop.clear()
        self.last_telemetry, self.online = None, False
        self.idle_status = False
        self.controls(True)
        self.status.config(text=self.text("Connecting to DSX…", "正在连接 DSX…"))
        def worker():
            try:
                run_bridge(game, port, controller, self.stop, lambda kind, value: self.events.put((kind, value)))
            except Exception as exc:
                self.events.put(("error", str(exc)))
            finally:
                self.events.put(("finished", None))
        self.thread = threading.Thread(target=worker, daemon=False)
        self.thread.start()

    def request_stop(self):
        self.stop.set()
        self.status.config(text=self.text("Stopping…", "正在停止…"))

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "connected":
                    self.online = True
                elif kind == "telemetry":
                    self.last_telemetry = time.monotonic()
                    self.detail.config(text=f"{value.get('mode', '?')} · stamina {value.get('stamina_ratio', 0):.0%} · L2 {self.latest_effect[0]}/8 · R2 {self.latest_effect[1]}/8")
                elif kind == "effect":
                    self.latest_effect = (value.get("left_strength", 0), value.get("strength", 0))
                elif kind == "error":
                    self.online = False
                    self.status.config(text=self.text("Connection failed. Check DSX Incoming UDP and controller.", "连接失败，请检查 DSX 传入 UDP 与手柄连接。"))
                    self.messagebox.showerror("KCDDSX", value)
                elif kind == "finished":
                    self.online = False
                    self.controls(False)
                    if self.stop.is_set():
                        self.status.config(text=self.text("Stopped. DSX profile restored.", "已停止，已发送 DSX 配置还原指令。"))
                        self.detail.config(text="")
        except queue.Empty:
            pass
        if self.online and not self.stop.is_set():
            active = self.last_telemetry and time.monotonic() - self.last_telemetry <= 2
            self.status.config(text=self.text("Live game feedback", "游戏反馈已连接") if active else self.text("DSX connected · waiting for game / load a save", "DSX 已连接 · 等待游戏状态，请进入存档"))
        if self.closing and not (self.thread and self.thread.is_alive()):
            self.root.destroy()
            return
        self.root.after(100, self.poll)

    def close(self):
        self.closing = True
        self.request_stop()


def self_test():
    from kcd_dsx_bridge import CombatController, effects_packet
    packets = []
    control = CombatController(packets.append)
    base = dict(v=1, session="self-test", state="idle", event="heartbeat", drawn=False,
                usable=True, suspended=False, mode="unarmed")
    for seq, (ratio, strength) in enumerate([(1, 0), (.79, 1), (.4, 4), (0, 6), (1, 0)], 1):
        control.accept(dict(base, seq=seq, stamina_ratio=ratio))
        assert packets[-1] == effects_packet(0, strength, strength)
    return {"version": VERSION, "self_test": "passed", "hardware_access": False}


def main():
    parser = argparse.ArgumentParser(description="KCDDSX portable bridge")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
        if args.report:
            args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
        elif sys.stdout:
            print(json.dumps(result))
        return
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    try:
        instance = SingleInstance()
    except RuntimeError as exc:
        messagebox.showinfo("KCDDSX", str(exc))
        root.destroy()
        return
    try:
        BridgeApp(root)
        root.deiconify()
        root.mainloop()
    finally:
        instance.close()


if __name__ == "__main__":
    main()
