"""PyInstaller's entry point for the dl-capture .exe.

PyInstaller builds from a script file, not a package's console-script entry
point, so this just calls straight through to the real CLI.
"""

from dl_deck_lab.capture.cli import main

if __name__ == "__main__":
    main()
