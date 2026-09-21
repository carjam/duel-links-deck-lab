# PyInstaller spec for a standalone dl-capture.exe.
#
# Run from anywhere on a native Windows Python (not WSL):
#   pyinstaller packaging/dl_capture.spec
#
# UNTESTED: written without a Windows machine to build/run it on. The
# hidden-imports list below is a defensive best guess at what pygetwindow,
# mss, and keyboard's Windows backends need (they load some submodules
# dynamically, which PyInstaller's static analysis can miss). If the built
# .exe crashes immediately on launch, run it from a terminal (not by
# double-clicking) to see the traceback -- it's almost always a missing
# hidden import, which PyInstaller's error message names directly; add it
# to the list below and rebuild.

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
