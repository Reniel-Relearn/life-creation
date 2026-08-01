"""A real window, using tkinter from the standard library.

This is the second front end. It touches the screen and nothing else - the
simulation in `game.py` is untouched by it, exactly as DESIGN.md section 6
rule 1 intended. `ui.py` remains the terminal front end.
"""

import tkinter as tk

from . import actions as actions_mod
from . import config
from .game import DIRECTIONS, Game

BG = "#0e0e12"
PANEL = "#15151b"
FG = "#c9c9d1"
DIM = "#43434e"
FAINT = "#26262e"
ACCENT = "#d8d8e2"

ARROWS = {"Up": "up", "Down": "down", "Left": "left", "Right": "right"}
VI_KEYS = {"k": "up", "j": "down", "h": "left", "l": "right"}


# ---------------------------------------------------------------------------
# xterm-256 colour index -> hex, so both front ends can share one palette
# ---------------------------------------------------------------------------

_SYSTEM = [
    "#000000", "#800000", "#008000", "#808000", "#000080", "#800080",
    "#008080", "#c0c0c0", "#808080", "#ff0000", "#00ff00", "#ffff00",
    "#0000ff", "#ff00ff", "#00ffff", "#ffffff",
]


def hex_for(index: int) -> str:
    if index < 16:
        return _SYSTEM[index]
    if index < 232:
        n = index - 16
        levels = [0, 95, 135, 175, 215, 255]
        r, g, b = levels[n // 36], levels[(n // 6) % 6], levels[n % 6]
        return f"#{r:02x}{g:02x}{b:02x}"
    value = 8 + 10 * (index - 232)
    return f"#{value:02x}{value:02x}{value:02x}"


def _bar_colour(value: float) -> str:
    if value >= 60:
        return "#5f9e6e"
    if value >= 30:
        return "#c9a227"
    return "#bf5b52"


# ---------------------------------------------------------------------------

class Window:
    def __init__(self, seed: int | None = None):
        self.seed = seed
        self.game: Game | None = None

        self.root = tk.Tk()
        self.root.title("Life Creation")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.frame = tk.Frame(self.root, bg=BG)
        self.frame.pack(padx=24, pady=18)
        self._build_title()

    # -- screens ------------------------------------------------------------

    def _clear(self) -> None:
        for child in self.frame.winfo_children():
            child.destroy()

    def _build_title(self) -> None:
        self._clear()
        tk.Label(self.frame, text="How will you live your life?", bg=BG,
                 fg=ACCENT, font=("Consolas", 20, "bold")).pack(pady=(60, 30))
        tk.Label(self.frame, text="You wake with nothing.", bg=BG, fg=DIM,
                 font=config.WINDOW_FONT).pack()
        tk.Label(self.frame, text="The world is already finished, and it is waiting.",
                 bg=BG, fg=DIM, font=config.WINDOW_FONT).pack(pady=(0, 40))

        row = tk.Frame(self.frame, bg=BG)
        row.pack(pady=(0, 60))
        tk.Label(row, text="What is your name?  ", bg=BG, fg=FG,
                 font=config.WINDOW_FONT).pack(side="left")
        entry = tk.Entry(row, bg=PANEL, fg=ACCENT, insertbackground=ACCENT,
                         font=config.WINDOW_FONT, width=18, relief="flat",
                         highlightthickness=1, highlightbackground=DIM)
        entry.pack(side="left", ipady=4)
        entry.focus_set()

        def begin(_event=None):
            self._start(entry.get().strip() or "Someone")

        entry.bind("<Return>", begin)
        # Keep the window a sensible size before the map exists.
        self.frame.configure(width=760, height=520)

    def _start(self, name: str) -> None:
        self.game = Game(name, self.seed)
        self.game.say("You wake with nothing.")
        self._build_game()
        self.root.bind("<Key>", self._on_key)
        self.redraw()

    def _build_game(self) -> None:
        self._clear()

        header = tk.Frame(self.frame, bg=BG)
        header.pack(fill="x", pady=(0, 8))
        tk.Label(header, text="LIFE CREATION", bg=BG, fg=DIM,
                 font=("Consolas", 12, "bold")).pack(side="left")
        self.when = tk.Label(header, text="", bg=BG, fg=FG,
                             font=config.WINDOW_FONT_SMALL)
        self.when.pack(side="right")

        self.map = tk.Text(
            self.frame, width=config.WINDOW_VIEW_WIDTH,
            height=config.WINDOW_VIEW_HEIGHT, bg=BG, fg=FG,
            font=config.WINDOW_FONT, relief="flat", highlightthickness=0,
            cursor="arrow", wrap="none", spacing1=0, spacing3=0,
        )
        self.map.pack()
        self.map.configure(state="disabled")

        self.status = tk.Canvas(self.frame, width=620, height=86, bg=BG,
                                highlightthickness=0)
        self.status.pack(pady=(10, 6))

        self.place = tk.Label(self.frame, text="", bg=BG, fg=FG, anchor="w",
                              font=config.WINDOW_FONT_SMALL)
        self.place.pack(fill="x")
        self.warning = tk.Label(self.frame, text="", bg=BG, fg="#bf5b52",
                                anchor="w", font=(*config.WINDOW_FONT_SMALL, "bold"))
        self.warning.pack(fill="x")
        self.soul = tk.Label(self.frame, text="", bg=BG, fg="#7a7a96", anchor="w",
                             font=config.WINDOW_FONT_SMALL)
        self.soul.pack(fill="x", pady=(0, 8))

        self.log = tk.Label(self.frame, text="", bg=BG, fg=DIM, anchor="w",
                            justify="left", font=config.WINDOW_FONT_SMALL)
        self.log.pack(fill="x")

        self.hints = tk.Label(self.frame, text="", bg=BG, fg=FAINT, anchor="w",
                              font=("Consolas", 10))
        self.hints.pack(fill="x", pady=(10, 0))

    # -- input --------------------------------------------------------------

    def _on_key(self, event) -> None:
        game = self.game
        if game is None or not game.player.alive:
            return

        if event.keysym in ARROWS:
            game.move(ARROWS[event.keysym])
        else:
            key = (event.char or "").lower()
            if key == "q":
                self.root.destroy()
                return
            if key in VI_KEYS:
                game.move(VI_KEYS[key])
            elif key in actions_mod.BY_KEY:
                game.do_action(key)
            else:
                return

        if not game.player.alive:
            self.redraw()
            self.root.after(900, self._show_ending)
            return
        self.redraw()

    # -- drawing ------------------------------------------------------------

    def _viewport(self) -> tuple[int, int]:
        game = self.game
        left = game.player.x - config.WINDOW_VIEW_WIDTH // 2
        top = game.player.y - config.WINDOW_VIEW_HEIGHT // 2
        left = max(0, min(game.world.width - config.WINDOW_VIEW_WIDTH, left))
        top = max(0, min(game.world.height - config.WINDOW_VIEW_HEIGHT, top))
        return max(0, left), max(0, top)

    def _draw_map(self) -> None:
        game = self.game
        world, player = game.world, game.player
        left, top = self._viewport()
        radius = game.sight_radius()

        self.map.configure(state="normal")
        self.map.delete("1.0", "end")

        for row in range(config.WINDOW_VIEW_HEIGHT):
            y = top + row
            chars, colours = [], []
            for col in range(config.WINDOW_VIEW_WIDTH):
                x = left + col
                if not world.in_bounds(x, y):
                    chars.append(" ")
                    colours.append(BG)
                    continue
                tile = world.at(x, y)
                distance = max(abs(x - player.x), abs(y - player.y))
                if x == player.x and y == player.y:
                    chars.append("@")
                    colours.append("#ffffff")
                elif tile.has_fire and distance <= radius + 2:
                    chars.append("*")
                    colours.append("#ff9d3c")
                elif distance <= radius:
                    chars.append(tile.terrain.char)
                    colours.append(hex_for(tile.terrain.colour))
                elif tile.seen:
                    chars.append(tile.terrain.char)
                    colours.append("#2b2b33")
                else:
                    chars.append(" ")
                    colours.append(BG)

            self.map.insert("end", "".join(chars) + "\n")
            # Tag runs of identical colour rather than one tag per character.
            start = 0
            for col in range(1, len(colours) + 1):
                if col == len(colours) or colours[col] != colours[start]:
                    name = f"c{colours[start].lstrip('#')}"
                    self.map.tag_configure(name, foreground=colours[start])
                    self.map.tag_add(name, f"{row + 1}.{start}",
                                     f"{row + 1}.{col}")
                    start = col

        self.map.configure(state="disabled")

    def _draw_status(self) -> None:
        needs = self.game.player.needs
        canvas = self.status
        canvas.delete("all")

        rows = [
            ("Water", needs.water, 0, 0), ("Food", needs.food, 1, 0),
            ("Warmth", needs.warmth, 0, 1), ("Rest", needs.rest, 1, 1),
            ("Health", needs.health, 0, 2),
        ]
        for label, value, column, line in rows:
            x = 4 + column * 310
            y = 8 + line * 26
            canvas.create_text(x, y, text=label, anchor="w", fill=DIM,
                               font=config.WINDOW_FONT_SMALL)
            bar_x = x + 72
            canvas.create_rectangle(bar_x, y - 7, bar_x + 170, y + 7,
                                    fill=PANEL, outline="")
            width = int(170 * max(0.0, min(100.0, value)) / 100.0)
            if width:
                canvas.create_rectangle(bar_x, y - 7, bar_x + width, y + 7,
                                        fill=_bar_colour(value), outline="")
            canvas.create_text(bar_x + 182, y, text=str(int(value)), anchor="w",
                               fill=FG, font=config.WINDOW_FONT_SMALL)

    def redraw(self) -> None:
        game = self.game
        needs, clock, tile = game.player.needs, game.clock, game.tile()

        self.when.configure(
            text=f"Day {clock.day}    {clock.clock_text()}    {clock.phase}"
        )
        self._draw_map()
        self._draw_status()

        place = f"You are standing in {tile.terrain.name}."
        if tile.has_fire:
            place += "   A fire is burning here."
        self.place.configure(text=place)
        self.warning.configure(text=needs.urgent_warning() or "")
        self.soul.configure(text=needs.describe_soul())

        lines = game.log[-config.WINDOW_LOG_LINES:]
        padded = [""] * (config.WINDOW_LOG_LINES - len(lines)) + \
                 ["> " + line for line in lines]
        self.log.configure(text="\n".join(padded))

        keys = "   ".join(f"[{a.key}] {a.label}"
                          for a in actions_mod.available(game))
        self.hints.configure(text=f"[arrows] move     {keys}     [q] quit")

    def _show_ending(self) -> None:
        lines = self.game.ending()
        self._clear()
        self.root.unbind("<Key>")
        tk.Label(self.frame, text="", bg=BG).pack(pady=20)
        for line in lines:
            if not line:
                tk.Label(self.frame, text=" ", bg=BG,
                         font=("Consolas", 6)).pack()
            elif line == "This is how you lived.":
                tk.Label(self.frame, text=line, bg=BG, fg=ACCENT,
                         font=("Consolas", 16, "bold")).pack(pady=(18, 0))
            else:
                tk.Label(self.frame, text=line, bg=BG, fg=FG,
                         wraplength=680, justify="center",
                         font=config.WINDOW_FONT).pack()
        tk.Button(self.frame, text="close", command=self.root.destroy,
                  bg=PANEL, fg=FG, relief="flat", font=config.WINDOW_FONT_SMALL,
                  activebackground=PANEL, activeforeground=ACCENT,
                  padx=18, pady=4).pack(pady=30)

    # -- run ----------------------------------------------------------------

    def run(self) -> None:
        self.root.mainloop()


def play(seed: int | None = None) -> None:
    Window(seed).run()
