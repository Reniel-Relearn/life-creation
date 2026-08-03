# Life Creation

> ### *How will you live your life?*

A survival game that starts you with nothing in a world that already contains
everything you need. It asks that question on the first screen, and answers it
on the last.

A turn-based graphical desktop game in Python. One keypress is one turn.

---

## 📋 Table of Contents

- [About](#-about)
- [The three needs](#-the-three-needs)
- [Installation](#-installation)
- [Playing](#-playing)
- [Controls](#-controls)
- [Surviving the first night](#-surviving-the-first-night)
- [The chronicle](#-the-chronicle)
- [Architecture](#-architecture)
- [Project structure](#-project-structure)
- [Testing](#-testing)
- [The simulator](#-the-simulator)
- [Packaging](#-packaging)
- [Status and roadmap](#-status-and-roadmap)
- [Known limitations](#-known-limitations)
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

The game is turn-based. Time moves when you act, and only when you act. Opening
a menu costs nothing. Leaving the window open costs nothing. Walking one tile
costs twelve minutes you do not get back.

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

**Requirements:** Python 3.10 or newer, and a machine that can open an OpenGL
3.3 window. An ordinary laptop is fine; no gaming GPU is needed.

There **is** an install step. The game uses [Arcade](https://api.arcade.academy)
for rendering.

### Windows, from scratch

1. Open the repository folder in VS Code.
2. Open the VS Code terminal — **Terminal → New Terminal**.
3. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

4. Activate it:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks the script, run
   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first.

5. Install the dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

6. Run the game:

   ```powershell
   python main.py
   ```

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

---

## 💻 Playing

```bash
python main.py                 # play
python main.py --seed 1234     # a specific world; the same seed is the same world
python main.py --mute          # no sound
python main.py --terminal      # the terminal debugging interface
python main.py --smoke-test    # verify the graphical stack and exit
```

Developer flags — these are typed deliberately and are never reachable by a key
combination during ordinary play:

```bash
python main.py --debug            # developer logging
python main.py --time-scale 20    # time acceleration, for testing the long game
```

You can also enter a seed on the name screen, so you never need the command line
to replay a world.

---

## 🎮 Controls

| Key | Action |
|---|---|
| `arrows` / `WASD` / `HJKL` | Move one tile — and one turn |
| `E` | Do the obvious thing here |
| `Q` | Drink |
| `F` | Forage |
| `G` | Gather deadwood |
| `B` | Build a fire, or feed one |
| `R` | Rest |
| `Z` | Sleep |
| `M` | Be still |
| `Tab` | Journal |
| `Esc` | Pause |

The screen only ever offers you what is worth doing where you are standing.
There is no permanent menu of every action.

> **Why `Q` for drink and `Z` for sleep?** `WASD` movement collides with the
> older `D` (drink) and `S` (sleep) bindings — `D` cannot be both "move right"
> and "drink". Movement won, because it is what you do most. `F`, `G`, `B`, `R`
> and `M` never collided and did not move. The terminal interface still uses the
> original letters; it has no `WASD` to clash with.

### The world

| | |
|---|---|
| Grassland | some forage |
| Forest | deadwood, forage, shelter from the cold |
| Running water | safe to drink, cold to wade across |
| Marsh | reeds, and flat brackish water that slakes less |
| Rocky hills | stone and flint, and no shelter at all |

Terrain you have seen stays on the map, subdued. At night the world closes in to
a few paces, and a fire pushes it back out again.

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
    Adam lived 2 days.

    The cold took you.
    You spent most of your days asleep.
    By the end you were untried at wandering.
    You saw a good deal of the world.
    You made fire on the 1st day.

    You were still curious at the end.
    There were long stretches where you did the same thing over and over.
    You were still, now and then.

    This is how you lived.
```

Every line is generated from what was actually recorded during the run — hours
spent, places drunk from, nights survived, the day the first fire caught.

---

## 🏗 Architecture

One rule holds the project together:

> **The simulation never touches the screen.**

Dependencies run one way and never back:

```
presentation/   graphics, input, sound        imports arcade
      |
application.py  input lock, turns, restarts   no framework
      |
game.py         the rules                     no framework, never prints
```

Every turn takes the same path:

```
key press -> Command -> simulation resolves -> Outcome -> animation -> input reopens
```

The graphical layer animates a turn that has *already* been decided. Animation
length never affects a rule, and input is refused while an animation is playing,
so leaning on a key cannot bank a queue of accidental turns.

Both rules are enforced by tests, not by good intentions:
`tests/smoke/test_architecture.py` parses every simulation module and fails the
build if one imports a graphics framework, prints, reaches into the presentation
layer, or draws from the global `random` stream.

---

## 📁 Project structure

```
life-creation/
├── main.py                     entry point
├── requirements.txt
├── pyproject.toml
├── DESIGN.md                   the full design document
├── assets/                     empty; art is drawn procedurally at start-up
├── life_creation/
│   ├── config.py               every tunable number in the game
│   │
│   ├── clock.py                game time, phases, variable step
│   ├── world.py                grid, terrain, generation, validation
│   ├── needs.py                Body / Soul / Spirit
│   ├── player.py               the character
│   ├── fire.py                 fuel, warmth, light, going out
│   ├── perception.py           sight, fog of war, Spirit's quiet widening
│   ├── skills.py               growth by doing
│   ├── actions.py              what you can do with a day
│   ├── game.py                 the rules. Commands in, Outcomes out.
│   ├── commands.py             what the player may ask for
│   ├── outcomes.py             what the simulation says happened
│   ├── chronicle.py            the life record and the ending
│   ├── viewmodel.py            what the screen is allowed to know
│   ├── agents.py               rule-based agents for the harness
│   │
│   ├── application.py          the controller: input lock, runs, restarts
│   │
│   ├── ui.py                   terminal interface (debugging only)
│   └── presentation/           the graphical game
│       ├── app.py              window and screen transitions
│       ├── assets.py           procedural textures, robust loading
│       ├── audio.py            optional sound, fails gracefully
│       ├── camera.py           follows, and stops at the world's edge
│       ├── hud.py              the quiet interface
│       ├── input.py            key bindings
│       ├── lighting.py         ambient wash, fire light, day and night
│       ├── particles.py        embers, bounded
│       ├── tile_renderer.py    batched terrain and fog of war
│       ├── smoke.py            the graphical smoke test
│       └── views/              opening, naming, play, pause, help, chronicle
├── tests/                      unit, integration, simulation, smoke
└── tools/simulate.py           headless play, thousands of runs
```

---

## 🧪 Testing

```bash
python -m pytest
```

284 tests covering the clock, world generation and validation, movement and the
input lock, Body decay and death, Soul narrowing, Spirit's invisibility, every
action, fire, the chronicle, determinism, and the architectural rules above.

Tests drive the game the same way the game does — through `Session` and
`Command` — so a passing test means the real path works.

### Graphical smoke test

```bash
python main.py --smoke-test
```

Builds the real window, real assets and real game view, drives synthetic turns
through the real key handler, and reads the framebuffer back. It reports each
stage as PASS / FAIL / NOT TESTED, and is careful to say **NOT TESTED** rather
than PASS when there is no display to render to.

---

## 🤖 The simulator

```bash
python -m tools.simulate --seed 1234 --runs 100
```

Plays the game headlessly with six deterministic rule-based agents — random,
first-night survivor, fire-focused, explorer, stillness-focused and bare
subsistence. It checks after **every turn** that needs stay in range, inventory
never goes negative, the clock never freezes, fires never burn impossible
amounts of fuel, impossible actions never succeed, one-time milestones happen
once, and the same seed and command sequence always replay identically.

It also detects live-locks — an agent repeating a refused action forever — which
is how two agent bugs were found and fixed during this migration.

The statistics are for correctness and gross balance only. They say the rules
hold together. They do not say the game is any good.

---

## 📦 Packaging

A Windows executable can be built with PyInstaller:

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm --windowed --name "Life Creation" ^
            --add-data "assets;assets" ^
            main.py
```

- `--windowed` suppresses the console window.
- `--add-data "assets;assets"` includes the asset folders. They are empty today
  (all art is procedural), but including them means dropped-in art keeps working.
- The executable lands in `dist/Life Creation/`.
- Save files, when they arrive in Phase 3, must go in the user's
  `%LOCALAPPDATA%` — never beside the executable, which may be read-only.

**This build has not been run.** The command is documented, not verified.

`dist/` and `build/` are not committed.

---

## 🧭 Status and roadmap

Playable. A complete first-night vertical slice, graphical and turn-based.

- [x] **Design** — core loop, systems, data model, scope
- [x] **Vertical slice** — world, day/night, survival loop, fire, death, chronicle
- [x] **Graphical migration** — Arcade, turn-based, animated, tested
- [ ] **Systems** — save/load, injury and illness, multi-day projects, and the
      absence simulation: while you are away from the game, your character
      subsists on whatever you stored, so preparation buys you real-world time
- [ ] **Content** — recipes, events, seasons, encounters, difficulty curve
- [ ] **Polish** — audio, packaging, settings

Deliberately not built yet: NPCs and family, farming, herding, metals,
predators, and anything beyond a flat bounded map. Meeting another person should
land properly, and it will not if it is rushed.

---

## ⚠️ Known limitations

Stated plainly, so nothing here reads as more finished than it is.

- **No save or load.** Closing the window ends the life. Absence simulation
  depends on saves and is therefore not built either.
- **No aging and no lifespan.** `Clock.step` and `Player.age_days` exist so the
  time scale can widen later; a sixty-year life is not simulated, and is not
  faked by making time race.
- **No air system.** Reserved for drowning and smoke; there is deliberately no
  breathing meter. See DESIGN.md section 1.
- **One season.** Temperature follows a day/night curve. There is no winter yet,
  and no weather.
- **No sound files ship with the game.** The audio architecture is in place and
  silent; drop a `.wav` into `assets/audio/` and it is used.
- **The Windows executable has not been built.** The command is documented only.
- **Death is currently almost always cold.** Across 100 simulated runs every
  death was exposure. Thirst and hunger are implemented and tested, but the
  first night reaches you long before they do.
- **`--time-scale` is not covered by a long-run test.** It works and is unit
  tested, but nothing yet plays a full accelerated life end to end.

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

Please run `python -m pytest` before opening a pull request.

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

**Status:** 🚧 Playable — graphical first-night vertical slice
**Last updated:** 3 August 2026
