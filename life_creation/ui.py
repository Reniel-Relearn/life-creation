"""The terminal front end - an optional debugging interface.

The graphical game is the game (`life_creation.presentation`). This exists so
the simulation can be driven by hand over SSH, or on a machine with no working
OpenGL, without any graphics framework being importable at all.

Like the graphical layer, it touches the screen and nothing else. It owns its
own loop; the simulation knows nothing about it.
"""

from __future__ import annotations

import os
import sys

from . import actions as actions_mod
from . import config
from .application import Session
from .clock import Phase
from .commands import Command, Direction

# ---------------------------------------------------------------------------
# Terminal setup - stdlib only
# ---------------------------------------------------------------------------

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
CLEAR = "\x1b[2J\x1b[H"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"


def fg(colour: int) -> str:
    return f"\x1b[38;5;{colour}m"


def paint(text: str, colour: int, bold: bool = False) -> str:
    return f"{BOLD if bold else ''}{fg(colour)}{text}{RESET}"


def setup_terminal() -> None:
    """Enable ANSI escapes on Windows and force UTF-8 output."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            enable_vt_processing = 0x0004
            kernel32.SetConsoleMode(handle, mode.value | enable_vt_processing)
    except (ImportError, AttributeError, OSError):
        # No console to configure. Colour will look wrong; nothing will break.
        pass


def clear() -> None:
    sys.stdout.write(CLEAR)


def hide_cursor() -> None:
    sys.stdout.write(HIDE_CURSOR)


def show_cursor() -> None:
    sys.stdout.write(SHOW_CURSOR)


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

_WIN_ARROWS = {b"H": "up", b"P": "down", b"K": "left", b"M": "right"}
_POSIX_ARROWS = {"[A": "up", "[B": "down", "[C": "right", "[D": "left"}

VI_KEYS = {"k": "up", "j": "down", "h": "left", "l": "right"}


def read_key() -> str:
    """One keypress, no Enter. Arrow keys come back as 'up'/'down'/..."""
    if os.name == "nt":
        import msvcrt

        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):
            return _WIN_ARROWS.get(msvcrt.getch(), "")
        if ch == b"\x03":
            raise KeyboardInterrupt
        return ch.decode("utf-8", "ignore").lower()

    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            return _POSIX_ARROWS.get(sys.stdin.read(2), "")
        if ch == "\x03":
            raise KeyboardInterrupt
        return ch.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ---------------------------------------------------------------------------
# Bars
# ---------------------------------------------------------------------------

FULL, EMPTY = "█", "░"


def _bar_colour(value: float) -> int:
    if value >= 60:
        return 71
    if value >= 30:
        return 179
    return 167


def bar(label: str, value: float, width: int = 10) -> str:
    filled = int(round(value / 100.0 * width))
    filled = max(0, min(width, filled))
    body = FULL * filled + EMPTY * (width - filled)
    return f"{label:<7}{paint(body, _bar_colour(value))} {int(value):>3}"


# ---------------------------------------------------------------------------
# The map
# ---------------------------------------------------------------------------

def _viewport(player, world) -> tuple[int, int]:
    left = player.x - config.VIEW_WIDTH // 2
    top = player.y - config.VIEW_HEIGHT // 2
    left = max(0, min(world.width - config.VIEW_WIDTH, left))
    top = max(0, min(world.height - config.VIEW_HEIGHT, top))
    return max(0, left), max(0, top)


def render_map(game) -> list[str]:
    world, player = game.world, game.player
    left, top = _viewport(player, world)
    visible = game.visible()
    rows = []

    for row in range(config.VIEW_HEIGHT):
        y = top + row
        if y >= world.height:
            rows.append("")
            continue
        cells = []
        for col in range(config.VIEW_WIDTH):
            x = left + col
            if x >= world.width:
                cells.append(" ")
                continue
            tile = world.at(x, y)

            if x == player.x and y == player.y:
                cells.append(paint("@", 231, bold=True))
            elif game.fires.at(x, y) and (x, y) in visible:
                cells.append(paint("*", 208, bold=True))
            elif (x, y) in visible:
                cells.append(paint(tile.terrain.char, tile.terrain.colour))
            elif tile.seen:
                cells.append(paint(tile.terrain.char, 236))
            else:
                cells.append(" ")
        rows.append("".join(cells))
    return rows


# ---------------------------------------------------------------------------
# The frame
# ---------------------------------------------------------------------------

def _phase_colour(phase: Phase) -> int:
    return {Phase.DAY: 222, Phase.DAWN: 216,
            Phase.DUSK: 174, Phase.NIGHT: 61}.get(phase, 250)


def render(game) -> None:
    needs, clock = game.player.needs, game.clock
    out = [CLEAR]

    header = paint("LIFE CREATION", 250, bold=True)
    when = (
        f"{paint('Day ' + str(clock.day), 253)}   "
        f"{paint(clock.clock_text(), 253)}   "
        f"{paint(clock.phase.value, _phase_colour(clock.phase))}"
    )
    out.append(f" {header}{' ' * 18}{when}")
    out.append("")

    for row in render_map(game):
        out.append(" " + row)
    out.append("")

    out.append(f"  {bar('Water', needs.water)}    {bar('Food', needs.food)}")
    out.append(f"  {bar('Warmth', needs.warmth)}    {bar('Rest', needs.rest)}")
    out.append(f"  {bar('Health', needs.health)}")
    out.append("")

    tile = game.tile()
    place = f"You are standing in {tile.terrain.name}."
    if game.fires.at(game.player.x, game.player.y):
        place += paint("  A fire is burning here.", 208)
    out.append("  " + paint(place, 250))

    warning = needs.urgent_warning()
    if warning:
        out.append("  " + paint(warning, 167, bold=True))

    soul_line = needs.describe_soul()
    if soul_line:
        out.append("  " + paint(soul_line, 103))
    out.append("")

    recent = game.log[-config.LOG_LINES:]
    for line in recent:
        out.append("  " + paint("> " + line, 245))
    for _ in range(config.LOG_LINES - len(recent)):
        out.append("")
    out.append("")

    keys = "  ".join(
        f"[{a.key}]{a.label}" for a in actions_mod.available(game)
    )
    out.append("  " + paint("[arrows/hjkl] move   " + keys + "   [q]uit", 240))

    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------

def title_screen() -> str:
    clear()
    print("\n\n" + paint("        How will you live your life?", 253, bold=True))
    print("\n")
    print(paint("        You wake with nothing.", 245))
    print(paint("        The world is already finished, and it is waiting.", 245))
    print("\n")
    try:
        name = input(paint("        What is your name?  ", 250)).strip()
    except EOFError:
        name = ""
    return name or "Someone"


def ending_screen(lines: list[str]) -> None:
    clear()
    print("\n")
    for line in lines:
        if line == "This is how you lived.":
            print()
            print(paint("        " + line, 253, bold=True))
        elif line:
            print(paint("        " + line, 249))
        else:
            print()
    print("\n")


# ---------------------------------------------------------------------------
# The terminal loop. The front end owns it; the simulation does not.
# ---------------------------------------------------------------------------

def _command_for(key: str) -> Command | None:
    if key in ("up", "down", "left", "right"):
        return Command.move(Direction(key))
    if key in VI_KEYS:
        return Command.move(Direction(VI_KEYS[key]))
    if key in actions_mod.BY_KEY:
        return Command.action(key)
    return None


def play(seed: int | None = None, time_scale: float = 1.0) -> None:
    setup_terminal()
    name = title_screen()
    session = Session(name, seed, time_scale=time_scale)
    session.game.say("You wake with nothing.")

    hide_cursor()
    try:
        while session.game.alive:
            render(session.game)
            key = read_key()
            if key == "q":
                break
            command = _command_for(key)
            if command is None:
                continue
            session.submit(command)
            # The terminal has no animation to wait on, so the lock opens again
            # the moment the frame is drawn.
            session.animation_finished()
    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()

    if not session.game.alive:
        render(session.game)
    ending_screen(session.ending())
