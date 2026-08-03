"""Life Creation.

    python main.py                    play
    python main.py --seed 1234        a specific world; the same seed is the same world
    python main.py --terminal         the terminal debugging interface
    python main.py --smoke-test       verify the graphical stack and exit
    python main.py --debug            developer logging
    python main.py --time-scale 20    developer time acceleration

Requires Arcade. See README.md for setup.
"""

from __future__ import annotations

import argparse
import logging
import sys

# Time acceleration is a development tool. It is reachable only by typing the
# flag, never by a key combination during ordinary play.
MAX_TIME_SCALE = 240.0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="life-creation",
        description="A survival game that asks how you will live your life.",
    )
    parser.add_argument("--seed", type=int, default=None,
                        help="world seed (same seed, same world)")
    parser.add_argument("--terminal", action="store_true",
                        help="use the terminal debugging interface")
    parser.add_argument("--smoke-test", action="store_true",
                        help="verify the graphical stack and exit")
    parser.add_argument("--debug", action="store_true",
                        help="developer logging")
    parser.add_argument("--time-scale", type=float, default=1.0,
                        metavar="N",
                        help="developer time acceleration (1.0 = normal)")
    parser.add_argument("--mute", action="store_true",
                        help="no sound")
    return parser.parse_args(argv)


def _configure_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )


def _time_scale(requested: float) -> float:
    if requested <= 0:
        raise SystemExit("--time-scale must be greater than 0")
    if requested > MAX_TIME_SCALE:
        raise SystemExit(f"--time-scale is capped at {MAX_TIME_SCALE:g}")
    return requested


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _configure_logging(args.debug)
    scale = _time_scale(args.time_scale)

    if args.smoke_test:
        from life_creation.presentation import smoke
        return smoke.run()

    if args.terminal:
        from life_creation import ui
        ui.play(seed=args.seed, time_scale=scale)
        return 0

    try:
        from life_creation import presentation
    except ImportError as exc:
        print("Life Creation needs Arcade, and it is not installed.")
        print(f"  ({exc})")
        print()
        print("  python -m pip install -r requirements.txt")
        print()
        print("Or use the terminal interface instead:  python main.py --terminal")
        return 1

    return presentation.run(seed=args.seed, time_scale=scale,
                            debug=args.debug, muted=args.mute)


if __name__ == "__main__":
    sys.exit(main())
