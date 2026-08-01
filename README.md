# Life Creation

> ### *How will you live your life?*

A survival game that starts you with nothing in a world that already contains
everything you need. It asks that question on the first screen, and answers it
on the last.

Pure Python. No dependencies. `python main.py` and you are playing.

---

## 📋 Table of Contents

- [About](#-about)
- [The three needs](#-the-three-needs)
- [Installation](#-installation)
- [Playing](#-playing)
- [Surviving the first night](#-surviving-the-first-night)
- [The chronicle](#-the-chronicle)
- [Project structure](#-project-structure)
- [Status and roadmap](#-status-and-roadmap)
- [Design](#-design)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

---

## 📚 About

You wake at dawn. You have nothing — no tools, no fire, no shelter, and no
explanation of why you are here. The world is finished, indifferent, and
waiting.

There is no quest. There is no tech tree to complete, no boss, and no score.

Bare survival is genuinely achievable, and it is genuinely empty. Everything
that is worth doing — building a fire, crossing the river, walking to the far
edge of the world — costs time you will never get back. What you chose to spend
your days on **is** your answer to the question. At the end, the game reads it
back to you and stops.

---

## ✨ The three needs

This is what separates Life Creation from other survival games. Three needs,
each failing on a completely different timescale, derived from the real
survival doctrine known as the Rule of Threes:

| | Fails in | Domain | How you see it |
|---|---|---|---|
| Shelter, warmth | ~3 hours | **Body** | A number |
| Water | ~3 days | **Body** | A number |
| Food | ~3 weeks | **Body** | A number |
| Purpose, company | ~3 months | **Soul** | Prose. Never a number. |
| Meaning | ~3 years, or never | **Spirit** | Never displayed at all |

**Body** kills you. Loud, urgent, visible. Cold is the fastest killer, water is
the emergency, and hunger weakens you long before it ends you.

**Soul** does not kill you — it narrows you. As it falls, actions quietly stop
appearing in your list. Nothing is announced and nothing explains it. You simply
stop thinking of them. It is fed by curiosity: seeing somewhere you have not
been. It is drained by monotony.

**Spirit** does nothing at all when you neglect it. No warning, no penalty, no
death. Tended, it slows the soul's decay and widens what you can perceive.
It is shown to you exactly once — in the chronicle, after you are dead.

You can play an entire life feeding only the fast needs, and the game will never
once tell you that was a mistake.

---

## 🚀 Installation

**Requirements:** Python 3.10 or newer. Nothing else.

```bash
git clone https://github.com/Reniel-Relearn/life-creation.git
cd life-creation
python main.py
```

There is no `pip install` step and no `requirements.txt`. The game uses only the
Python standard library — including `tkinter` for the window, which ships with
Python.

---

## 💻 Playing

```bash
python main.py                # play in a window (default)
python main.py --terminal     # play in the terminal instead
python main.py --seed 1234    # a specific world; the same seed is the same world
python main.py --demo         # watch an autopilot play, no input needed
```

### Controls

| Key | Action |
|---|---|
| `arrow keys` or `hjkl` | Move |
| `d` | Drink — you must be on or beside water |
| `f` | Forage — searches the ground where you stand |
| `g` | Gather wood — deadwood is found in forest |
| `b` | Build a fire, or feed one that is already lit |
| `r` | Rest |
| `s` | Sleep — until dawn if it is night |
| `m` | Be still |
| `q` | Quit |

### The map

| | |
|---|---|
| `@` | You |
| `"` | Grassland — some forage |
| `T` | Forest — deadwood, forage, shelter from the cold |
| `~` | Running water — safe to drink, cold to wade across |
| `,` | Marsh — reeds, and flat brackish water that slakes less |
| `^` | Rocky hills — stone and flint, and no shelter at all |
| `*` | A lit fire |

Terrain you have seen is remembered in dark grey. At night the world closes in
to a few paces, and a fire pushes it back out again.

---

## 🔥 Surviving the first night

The first night is the game's first real gate, and it is meant to be hard.

You wake at dawn with roughly twelve hours of daylight. Find forest, gather six
to eight wood, and light a fire **before** dusk. Firemaking fails often when you
are new at it and each attempt costs twenty-five minutes, so start early. One
wood buys two hours of burn; a full night needs six.

Then sleep beside it. If the fire burns down while you are asleep, the cold will
find you — a body left unsheltered loses its warmth in about three hours, and
then has about two hours left.

Everything after that is on you.

---

## 📖 The chronicle

There is no score and no win screen. When you die, the game writes the plain
facts of your life in order and stops:

```
    Adam lived 4 days.

    You spent most of your days tending a fire.
    By the end you were clumsy at stillness.
    You saw a good deal of the world.
    You made fire on the 1st day.
    You came through 3 nights.

    You were still curious at the end.
    You made time to be still. It cost you days you could not spare,
    and nothing came of it that anyone could see.

    This is how you lived.
```

---

## 📁 Project structure

```
life-creation/
├── main.py                 entry point
├── DESIGN.md               the full design document
└── life_creation/
    ├── config.py           every tunable number in the game
    ├── clock.py            game time, day/night, temperature curve
    ├── world.py            grid, terrain, procedural generation
    ├── needs.py            Body / Soul / Spirit
    ├── player.py           the character
    ├── skills.py           growth by doing
    ├── actions.py          what you can do with a day
    ├── game.py             the loop and the rules
    ├── chronicle.py        the life record and the ending
    ├── window.py           tkinter front end (default)
    └── ui.py               terminal front end (--terminal)
```

One architectural rule holds the project together: **the simulation never
touches the screen.** Only `window.py` and `ui.py` draw anything. That is why
the game runs in both a window and a terminal from one unchanged codebase.

---

## 🧭 Status and roadmap

Playable. Early, but genuinely playable end to end.

- [x] **Design** — core loop, systems, data model, scope
- [x] **Vertical slice** — world, day/night, survival loop, fire, death, chronicle
- [ ] **Systems** — save/load, injury and illness, multi-day projects, and the
      absence simulation: while you are away from the game, your character
      subsists on whatever you stored, so preparation buys you real-world time
- [ ] **Content** — recipes, events, seasons, encounters, difficulty curve
- [ ] **Polish** — configuration, error handling, packaging

Deliberately not built yet: NPCs and family, farming, herding, metals,
predators, and anything beyond a flat bounded map. Meeting another person should
land properly, and it will not if it is rushed.

---

## 📐 Design

The full design document — the loop, how the systems interact, the data model,
and everything explicitly ruled out of scope — is in
**[DESIGN.md](DESIGN.md)**.

---

## 🤝 Contributing

This is a personal hobby project, but issues and pull requests are welcome.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

If you are changing how the game *feels* rather than how it works, please read
`DESIGN.md` first — a good deal of what looks like a missing feature is a
deliberate omission.

---

## 📝 License

MIT — see [LICENSE](LICENSE).

---

## 👤 Author

**Reniel Galang**

- GitHub: [@Reniel-Relearn](https://github.com/Reniel-Relearn)
- Email: plaisolutionsph@gmail.com

---

**Status:** 🚧 Playable, early
**Last updated:** 1 August 2026
