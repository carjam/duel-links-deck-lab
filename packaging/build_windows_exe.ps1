# Builds dist/dl-capture.exe. Run from a native Windows PowerShell
# (not WSL) with the repo's Windows-side Python environment active.
#
#   cd C:\path\to\duel-links-deck-lab
#   .\packaging\build_windows_exe.ps1
#
# UNTESTED end-to-end -- see packaging/README.md before reporting a build
# as broken; the fix for most PyInstaller failures is adding a missing
# hidden import to dl_capture.spec, not a problem with this script.

pip install -e ".[capture]"
pip install pyinstaller
pyinstaller packaging/dl_capture.spec

Write-Host ""
Write-Host "Built dist/dl-capture.exe -- run it from a terminal first (not by"
Write-Host "double-clicking) so you can see any crash traceback."
