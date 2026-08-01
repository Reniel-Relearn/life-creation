"""Life Creation.

    python main.py                play in a window
    python main.py --terminal     play in the terminal instead
    python main.py --demo         run a scripted autopilot trace
    python main.py --seed 1234    play a specific world

No dependencies. Standard library only.
"""

import argparse
import sys


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="life-creation",
        description="A survival game that asks how you will live your life.",
    )
    parser.add_argument("--seed", type=int, default=None,
                        help="world seed (same seed, same world)")
    parser.add_argument("--terminal", action="store_true",
                        help="play in the terminal instead of a window")
    parser.add_argument("--demo", action="store_true",
                        help="run a scripted autopilot trace and exit")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    if args.demo:
        from life_creation import game
        game.demo(seed=args.seed if args.seed is not None else 7)
        return 0

    if args.terminal:
        from life_creation import game
        game.play(seed=args.seed)
        return 0

    try:
        from life_creation import window
    except ImportError:
        print("tkinter is not available in this Python.")
        print("Falling back to the terminal. Use --terminal to skip this.")
        from life_creation import game
        game.play(seed=args.seed)
        return 0

    window.play(seed=args.seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
