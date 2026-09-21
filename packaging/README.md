# Packaging dl-capture as a standalone .exe

For someone who wants to run `dl-capture` without installing Python. Not
needed for normal use -- if you're comfortable with `pip install -e ".[capture]"`,
skip this entirely.

## Build

From a native Windows PowerShell (not WSL), at the repo root:

```powershell
.\packaging\build_windows_exe.ps1
```

Produces `dist\dl-capture.exe`. Run it from a terminal, not by
double-clicking -- console output (including the "watching for F9/F10"
message and any crash traceback) only shows up that way.

## Verification status

Built and run on a real Windows machine: `dl-capture.exe --list-windows`
printed real window titles correctly, confirming `pygetwindow`'s hidden
imports are sufficient and the build itself works. A full capture session
(F9/F10 hotkey + screenshot saving, which also exercise `mss` and `keyboard`)
hasn't been separately confirmed from the packaged binary yet.

If the built `.exe` crashes:

1. Run it from a terminal to see the traceback (a double-clicked console app
   closes its window before you can read a crash message).
2. The traceback will usually be a `ModuleNotFoundError` naming the exact
   missing submodule -- add that name to `hidden_imports` in
   `dl_capture.spec` and rebuild.
3. If it builds and runs but behaves differently than running `dl-capture`
   via plain Python, that's a real bug in this packaging (not in
   `dl-capture` itself, which is separately verified) -- worth filing as an
   issue with the exact error.

## Distributing it

The built `.exe` is large (PyInstaller bundles a full Python runtime) and
only useful to someone on Windows. Don't commit `dist/` or `build/` to the
repo (already gitignored) -- attach the `.exe` to a GitHub Release instead
if you want to share it.
