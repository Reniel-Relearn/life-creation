"""The only module in the game that touches the terminal.

Everything else returns data. If this project ever moves to `rich`, `tcod` or a
graphical window, this is the single file that changes (DESIGN.md section 6).
"""

import os
import sys

from . import actions as actions_mod
from . import config

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
    if os.name == "nt":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                kernel32.SetConsoleMode(
                    handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
                )
        except Exception:
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
    radius = game.sight_radius()
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
            distance = max(abs(x - player.x), abs(y - player.y))

            if x == player.x and y == player.y:
                cells.append(paint("@", 231, bold=True))
            elif tile.has_fire and distance <= radius + 2:
                cells.append(paint("*", 208, bold=True))
            elif distance <= radius:
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

def _phase_colour(phase: str) -> int:
    return {"day": 222, "dawn": 216, "dusk": 174, "night": 61}.get(phase, 250)


def render(game) -> None:
    player, needs, clock = game.player, game.player.needs, game.clock
    out = [CLEAR]

    header = paint("LIFE CREATION", 250, bold=True)
    when = (
        f"{paint('Day ' + str(clock.day), 253)}   "
        f"{paint(clock.clock_text(), 253)}   "
        f"{paint(clock.phase, _phase_colour(clock.phase))}"
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
    if tile.has_fire:
        place += paint("  A fire is burning here.", 208)
    out.append("  " + paint(place, 250))

    warning = needs.urgent_warning()
    if warning:
        out.append("  " + paint(warning, 167, bold=True))

    soul_line = needs.describe_soul()
    if soul_line:
        out.append("  " + paint(soul_line, 103))
    out.append("")

    for line in game.log[-config.LOG_LINES:]:
        out.append("  " + paint("> " + line, 245))
    for _ in range(config.LOG_LINES - len(game.log[-config.LOG_LINES:])):
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
    print()
    print()
    print(paint("        How will you live your life?", 253, bold=True))
    print()
    print()
    print(paint("        You wake with nothing.", 245))
    print(paint("        The world is already finished, and it is waiting.", 245))
    print()
    print()
    try:
        name = input(paint("        What is your name?  ", 250)).strip()
    except EOFError:
        name = ""
    return name or "Someone"


def ending_screen(lines: list[str]) -> None:
    clear()
    print()
    print()
    for line in lines:
        if line == "This is how you lived.":
            print()
            print(paint("        " + line, 253, bold=True))
        elif line:
            print(paint("        " + line, 249))
        else:
            print()
    print()
    print()
