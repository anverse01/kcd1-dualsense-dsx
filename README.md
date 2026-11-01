# KCDDSX Adaptive Triggers

Adaptive triggers for **Kingdom Come: Deliverance 1**, using a Sony DualSense controller and **DSX**. [中文说明](README.zh-CN.md)

## Downloads and Nexus review

The Windows **0.5.0** main file has **completed Nexus Mods manual review** and is available from the [Nexus Files page](https://www.nexusmods.com/kingdomcomedeliverance/mods/2448?tab=files). You can also download it from [GitHub Releases](https://github.com/anverse01/kcd1-dualsense-dsx/releases/tag/v0.5.0). Both locations provide the same Windows ZIP; the package and published checksums are unchanged.

Use **Releases** for the Windows package. GitHub's automatic **Source code** downloads contain source, not a ready-to-install game mod. The source and build instructions are public for inspection and independent builds. Published checksums identify the original uploaded artifacts; local rebuilds need not be byte-identical.

Most of this project's original code and documentation were generated with **OpenAI Codex**, then iterated through automated checks and player hardware tests. The Nexus cover was AI-generated. AI assistance does not replace upstream license compliance or validation; see [credits](CREDITS.md), [third-party notices](THIRD_PARTY_NOTICES.md), and [test scope](docs/VALIDATION.md).

| Situation | Feedback |
| --- | --- |
| Bow equipped, before pulling R2 | R2 baseline resistance: 3/8 |
| Bow reaches ReadyToFire | R2 increases to 4/8 |
| Cancel draw or fire an arrow | R2 returns to the equipped-bow baseline |
| Melee weapon drawn or empty hands | Both L2 and R2 tighten as stamina falls below 80%, reaching 6/8 at zero |
| Stamina recovers | Both triggers ease off; no extra fatigue resistance at 80%–100% |
| Pause, dialogue, or telemetry missing for 2 seconds | Trigger effects released |

## Requirements

- Windows x64; Kingdom Come: Deliverance **1**. Standalone **0.5.0** was tested on Steam game version **1.9.7**, **DSX 3.1.7**, and a USB-connected DualSense: automatic loading, equipped bow/draw/cancel/fire, sword and empty-hand fatigue/recovery, and pause/resume were confirmed working by the player.
- [DSX](https://store.steampowered.com/app/1812620/DSX/) running, with **Incoming UDP** enabled. Default: `127.0.0.1:6969`, controller index `0`. This protocol targets DSX v3.1+; other versions/connections are unverified.
- Disable **Steam Input for this game** when DSX is handling controller emulation, to avoid duplicate inputs.
- No Cheat mod, Python installation, `-devmode`, administrator access or graphics injector is required by KCDDSX.

## Drag-and-drop install

1. Close the game. Extract `KCDDSX-0.5.0-Windows.zip`.
2. Drag its **KCDDSX** folder into `KingdomComeDeliverance/Mods/`.
3. Confirm the layout is `Mods/KCDDSX/mod.manifest`, `Mods/KCDDSX/Data/kcd_dsx.pak`, and `Mods/KCDDSX/KCDDSXBridge.exe`.
4. If you use an explicit `Mods/mod_order.txt`, add `KCDDSX` to it; otherwise an explicit order file is unnecessary. Do not replace your other entries.
5. Start DSX with Incoming UDP enabled, then double-click **KCDDSXBridge.exe**. It detects the game folder and starts automatically. Keep its window open while playing.
6. Start the game and load a save. The bridge should show live feedback. You can start the bridge during a session; it will wait for new telemetry.

The EXE has a Chinese/English switch. If it is moved outside the Mod folder, select the game root manually. Vortex deployment has not been tested; manual installation is the verified package layout.

## Stop / update / uninstall

Close the bridge window or click **Stop & restore DSX** to release both triggers and send DSX's restore-profile instruction. Wait for the bridge to exit before updating files.

To update, close the game and bridge, then replace only `Mods/KCDDSX` with the new version. To uninstall, close both and remove only `Mods/KCDDSX`; remove its line from `mod_order.txt` if you added one. Optional local bridge preferences are in `%LOCALAPPDATA%/KCDDSX/settings.json`.

**Private prototype users:** disable/remove the prototype's custom Cheat loader and stop its Python bridge before switching. Do not run both loaders/bridges together. Do not delete an independently installed Cheat mod that you use for other features. The public release never edits Cheat.

## Limits and troubleshooting

- Bow feedback uses observed drawing/ReadyToFire/FireArrow/cancel events, **not a continuous draw percentage**. Cancel/fire return to 3/8 while the bow remains equipped.
- Empty-hand fatigue also applies when walking or sprinting with empty hands. KCD1 does not provide a reliable persistent raised-fists flag for solo shadowboxing in our tests.
- Native UI stamina fraction is preferred. If unavailable, a session's observed peak stamina is used; loading at low stamina may understate fatigue until full recovery.
- Melee fatigue updates roughly every **500 ms**. Bow events update when observed; end-to-end latency has not been formally benchmarked.
- “DSX connected · waiting for game”: load a save, check that the Mod is enabled and that `kcd.log` is being updated in the game root. Check for `[KCDDSX] Independent loader` and `[KCDDSX]` telemetry lines. No extra logging configuration is normally needed.
- DSX connection failure: confirm Incoming UDP, port, USB controller connection and controller index. Use DSX's own settings if its firewall setup is required; KCDDSX does not change firewall rules.
- Double inputs: disable this game's Steam Input and avoid other virtual-controller emulation layers.
- Effects conflict: stop other adaptive-trigger writers for this controller. The bridge allows one KCDDSX EXE instance per Windows session; it cannot prevent unrelated apps or prototype bridges from sending DSX commands.
- The package contains an unsigned community EXE. It can be built from the included source. There are no auto-updates, remote endpoints or telemetry uploads; network traffic is only localhost DSX UDP.
- No graphics DLLs/configs, frame-generation files, key bindings, saves, stamina, inventory or combat balance are edited. Mods replacing player callbacks or disabling game logs may conflict. KCD2, Bluetooth, DualSense Edge and non-Steam editions are untested.

## Source and build

Use Python **3.12 x64** on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m unittest discover -s tests -v
.\.venv\Scripts\python tools/build.py
```

Outputs: `dist/KCDDSX-0.5.0-Windows.zip`, `dist/KCDDSX-0.5.0-Source.zip`, and `dist/SHA256SUMS.txt`. Building uses only this repository's files; no installed game or proprietary game scripts are needed. The EXE bundles Python/Tk with PyInstaller. Runtime source: `src/app.py`, `src/runtime.py`, `src/kcd_dsx_bridge.py`; game scripts: `src/startup.lua`, `src/kcd_dsx.lua`.

Original source: [MIT](LICENSE). See [third-party notices](THIRD_PARTY_NOTICES.md) and [validation](docs/VALIDATION.md). Nexus upload text and release checklist are in `docs/`. This project is unofficial and is not affiliated with Warhorse Studios, Sony or Paliverse.

## Credits

Thanks to [Paliverse / DSX](https://github.com/Paliverse/DSX), [pryans / KCD Cheat](https://github.com/pryans/kcd-cheat) ([Nexus](https://www.nexusmods.com/kingdomcomedeliverance/mods/106)), and [dataframe / benjaminfoo's How-to Lua](https://www.nexusmods.com/kingdomcomedeliverance/mods/1344) and [KCD Coding Guide](https://github.com/benjaminfoo/KCD-Coding-Guide). Full original-author links, historical credits and the exact role of each reference are preserved in [CREDITS.md](CREDITS.md), including runtime/build/test projects.
