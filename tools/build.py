"""Build redistributable PAK, portable Windows EXE and a clean source archive."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from runtime import VERSION


def archive(path, entries):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for name, content in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (2026, 11, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, content)


def build(skip_exe=False):
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    mod = dist / "KCDDSX"
    (mod / "Data").mkdir(parents=True, exist_ok=True)
    manifest = f'''<?xml version="1.0" encoding="utf-8"?>
<kcd_mod><info>
<name>KCDDSX Adaptive Triggers</name>
<description>DualSense bow and stamina adaptive triggers via DSX. KCD1.</description>
<author>KCDDSX contributors</author><version>{VERSION}</version>
<created_on>2026-11-01</created_on>
</info></kcd_mod>
'''
    (mod / "mod.manifest").write_text(manifest, encoding="utf-8")
    archive(mod / "Data" / "kcd_dsx.pak", {
        "Scripts/Startup/KCDDSX_startup.lua": (ROOT / "src/startup.lua").read_bytes(),
        "Scripts/KCDDSX/combat.lua": (ROOT / "src/kcd_dsx.lua").read_bytes(),
    })
    if not skip_exe:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile",
                        "--windowed", "--noupx", "--name", "KCDDSXBridge",
                        "--paths", str(ROOT / "src"),
                        "--distpath", str(ROOT / "build/exe"),
                        "--workpath", str(ROOT / "build/pyinstaller"),
                        "--specpath", str(ROOT / "build"),
                        str(ROOT / "src/app.py")], check=True, cwd=ROOT)
        shutil.copyfile(ROOT / "build/exe/KCDDSXBridge.exe", mod / "KCDDSXBridge.exe")
    for name in ("README.md", "README.zh-CN.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md", "CREDITS.md"):
        shutil.copyfile(ROOT / name, mod / name)
    (mod / "runtime-licenses").mkdir(exist_ok=True)
    for path in (ROOT / "runtime-licenses").glob("*.txt"):
        shutil.copyfile(path, mod / "runtime-licenses" / path.name)
    executable = mod / "KCDDSXBridge.exe"
    if not executable.is_file():
        raise FileNotFoundError("Build the Windows EXE before creating a release.")
    entries = {p.relative_to(dist).as_posix(): p.read_bytes() for p in mod.rglob("*") if p.is_file()}
    # File allowlist prevents machine-local state or test files leaking into releases.
    expected = {"KCDDSX/mod.manifest", "KCDDSX/Data/kcd_dsx.pak", "KCDDSX/KCDDSXBridge.exe",
                *{f"KCDDSX/{n}" for n in ("README.md", "README.zh-CN.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md", "CREDITS.md")},
                *{f"KCDDSX/runtime-licenses/{n}.txt" for n in ("Python", "PyInstaller", "Tcl", "Tk")}}
    if set(entries) != expected:
        raise RuntimeError("Unexpected release files: " + str(set(entries) ^ expected))
    release = dist / f"KCDDSX-{VERSION}-Windows.zip"
    archive(release, entries)
    sources = {}
    for folder in ("src", "tests", "tools", "docs", ".github", "runtime-licenses"):
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                sources["KCDDSX/" + path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for name in ("README.md", "README.zh-CN.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md", "CREDITS.md", ".gitignore", "requirements-dev.txt"):
        sources["KCDDSX/" + name] = (ROOT / name).read_bytes()
    archive(dist / f"KCDDSX-{VERSION}-Source.zip", sources)
    products = [release, dist / f"KCDDSX-{VERSION}-Source.zip"]
    checksums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in products)
    (dist / "SHA256SUMS.txt").write_text(checksums, encoding="ascii")
    print(json.dumps({"version": VERSION, "release": str(release), "files": len(entries)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-exe", action="store_true", help="Reuse an already-built executable")
    build(parser.parse_args().skip_exe)
