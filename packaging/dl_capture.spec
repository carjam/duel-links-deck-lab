# PyInstaller spec for a standalone dl-capture.exe.
#
# Run from anywhere on a native Windows Python (not WSL):
#   pyinstaller packaging/dl_capture.spec
#
# Verified: built and run on a real Windows machine, `dl-capture.exe
# --list-windows` printed real window titles correctly -- pygetwindow's
# hidden imports below are confirmed sufficient. mss/keyboard (the actual
# screenshot + hotkey capture, as opposed to just window enumeration)
# haven't been separately confirmed from the packaged binary yet; if a
# real capture session crashes where plain `dl-capture` doesn't, that's
# almost always a missing hidden import for one of those two -- the
# traceback (run from a terminal, not by double-clicking) will name it
# directly; add it to the list below and rebuild.

import os

# SPECPATH is injected by PyInstaller into this file's exec environment --
# using it (instead of a path relative to the current working directory)
# means this spec works the same regardless of where `pyinstaller` is run from.
here = SPECPATH
src_dir = os.path.join(here, "..", "src")
entry_script = os.path.join(here, "dl_capture_entry.py")

hidden_imports = [
    "pygetwindow",
    "pyrect",
    "win32gui",
    "win32con",
    "win32api",
    "win32process",
    "mss",
    "mss.windows",
    "keyboard",
    "keyboard._winkeyboard",
]

a = Analysis(
    [entry_script],
    pathex=[src_dir],
    hiddenimports=hidden_imports,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="dl-capture",
    console=True,
    onefile=True,
)
