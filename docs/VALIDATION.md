# Validation record

## Hardware-tested effect logic

The private 0.4.1 prototype was tested by a player using Steam KCD1 1.9.7, DSX 3.1.7, and a USB DualSense. The player confirmed normal operation after the empty-hand detection and lighter opening-swing fixes:

- Equipped bow has R2 resistance before drawing.
- Drawing to ReadyToFire increases R2 resistance; cancel and FireArrow return to equipped-bow baseline.
- Empty-hand and drawn-melee L2/R2 resistance increases with fatigue and eases with recovery.
- Opening swings are lighter: extra fatigue resistance starts below 80% stamina.
- Disabling this game's Steam Input resolved duplicate input.
- 32 pre-existing graphics/config/Mod files were hash-checked unchanged.

On 2026-11-01, standalone **0.5.0** was installed from the release staging folder after backing up and disabling the private Cheat prototype and stopping its Python bridge. The packaged EXE automatically detected the game directory and connected to DSX. The game logged `[KCDDSX] Independent loader 0.5.0 ready` and fresh telemetry. The player tested equipped bow/draw/cancel/fire, empty-hand and sword fatigue/recovery, and pause/resume and reported that everything worked normally. No Cheat files remained enabled in Mods. The 32 protected pre-existing files were unchanged.

## Automated validation

17 tests cover real Lua 5.1 telemetry passed into the Python controller, classification, empty hands with drawn=false, both fatigue outputs, bow event/cancel handling, missing-context protection, pause/dialogue, stale/duplicate data, callback argument/return preservation, old/partial logs, independent startup callbacks, portable path detection and local settings.

A worker integration test uses a temporary fake game tree and a localhost fake DSX server. It verifies fresh log ingestion, expected dual-trigger UDP packets, release on stop and the restore-profile instruction. No game/DSX hardware is contacted by these tests.

The packaged Windows executable provides `--self-test --report <file>` for a hardware-free packaging check. This verifies its bundled controller logic, not actual controller behavior.

## Regression checklist

The initial standalone acceptance test is complete. For subsequent releases, repeat these checks with the prototype disabled:

1. Drag KCDDSX into Mods; start DSX and double-click the EXE.
2. Confirm automatic game-folder detection and the independent-loader log line.
3. Load a save; check equipped bow, draw/cancel, draw/fire, sword and empty-hand fatigue/recovery.
4. Pause/resume, load a second save and verify feedback still works.
5. Stop the bridge and confirm DSX profile restoration. Close the game and verify only the new Mod folder was added.

Loading a second save during the same session was covered by the automated startup lifecycle test, but was not separately confirmed by the player in this acceptance round. Stop/release/profile-restore packets were verified by the worker integration test; the live acceptance request covered pause/resume.

USB DualSense is the tested connection. Bluetooth, DualSense Edge, other game stores/versions and Vortex deployment remain unverified. No end-to-end latency benchmark has been performed.
