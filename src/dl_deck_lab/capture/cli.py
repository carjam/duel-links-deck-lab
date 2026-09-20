from __future__ import annotations

import argparse
import datetime
import os
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Capture Duel Links collection screenshots on keypress. "
            "Windows-only -- run this from a native Windows Python install, not WSL."
        )
    )
    parser.add_argument(
        "--window-title",
        default="Duel Links",
        help="Substring to match the game window's title (default: 'Duel Links')",
    )
    parser.add_argument(
        "--capture-key", default="f9", help="Hotkey that captures the current screen (default: f9)"
    )
    parser.add_argument(
        "--stop-key", default="f10", help="Hotkey that ends the capture session (default: f10)"
    )
    parser.add_argument(
        "--out-dir", default="captures", help="Where to save screenshots (default: ./captures)"
    )
    return parser


def main() -> None:
    if sys.platform != "win32":
        print(
            "dl-capture only works on Windows (it needs to read another app's window). "
            "Run it from a native Windows Python install, not WSL.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Imported lazily so `dl-ocr`/`dl-recommend` (cross-platform) never fail to
    # import just because these Windows-only packages aren't installed.
    from dl_deck_lab.capture.hotkey_listener import wait_for_session
    from dl_deck_lab.capture.screenshot import capture_region
    from dl_deck_lab.capture.window import find_window

    args = build_parser().parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    region = find_window(args.window_title)
    count = 0

    def on_capture() -> None:
        nonlocal count
        count += 1
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        out_path = os.path.join(args.out_dir, f"{timestamp}.png")
        capture_region(region, out_path)
        print(f"[{count}] captured {out_path}")

    print(
        f"Watching for '{args.capture_key}' (capture) and '{args.stop_key}' (stop). "
        "Page through your collection in-game and press the capture key on each screen."
    )
    wait_for_session(args.capture_key, args.stop_key, on_capture)
    print(f"Done -- captured {count} screenshot(s) to {args.out_dir}")


if __name__ == "__main__":
    main()
