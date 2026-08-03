# Life Creation — Design Document

A survival game that starts you with nothing in a world that already contains
everything you need.

It exists to ask one question, shown on the first screen and answered on the last:

> **How will you live your life?**

No fixed narrative. The world is complete and indifferent. What you do with it is
the entire content of the game.

---

## 1. The three needs

The core structure. Each fails on a different timescale, derived from real survival
doctrine (the "Rule of Threes"), extended by two steps.

| Need | Fails in | Domain | How the player sees it |
|---|---|---|---|
| Air | ~3 minutes | Body | *Not implemented — see below* |
| Warmth / shelter | ~3 hours | Body | Number |
| Water | ~3 days | Body | Number |
| Food | ~3 weeks | Body | Number |
| Purpose, company | ~3 months | **Soul** | Prose only — never a number |
| Meaning | ~3 years, or never | **Spirit** | Never displayed at all |

**Body** kills you. Loud, urgent, visible.

**Soul** does not kill you — it narrows you. As Soul degrades, actions quietly
disappear from the available list, unannounced, because the character stops
thinking of them. The game never explains this.

**Spirit** does nothing when neglected. No warning, no penalty, no death. What it
does when tended:

- slows Soul's decay under hardship
- determines whether the character can rebuild after catastrophe
- widens perception — a higher Spirit reveals more of the world (a season turning,
  an animal that is sick, a person who is not alright)

**Framing rule:** prayer, meditation, stillness, reading and reflection are real
actions with real mechanical effects. The game never names what is read or who is
prayed to.

**Anti-chore rule:** Body has bars. Soul has sentences. Spirit has nothing. Three
needs, three levels of visibility. This is what stops the game becoming "feed three
meters."

**Air, and why there is no air meter.** The Rule of Threes starts at three minutes
without air, so the table lists it. It is deliberately *not* built. A breathing bar
that drains during ordinary play is exactly the chore the anti-chore rule exists to
prevent: it would tick down forever and be refilled by doing nothing, which is the
worst kind of meter. Air is reserved as future support for **exceptional
conditions only** — drowning, smoke, a collapsed space — and no such condition
exists yet. When one arrives, air becomes a temporary timer that appears with the
danger and vanishes with it, never a permanent gauge.

---

## 2. Core loop

**Daily survival sits under long-term projects.**

- **Daily:** wake → spend the day's segments → travel, gather, drink, build, rest →
  night → cold and hunger and whatever is out there → wake.
- **Projects:** multi-day commitments deliberately taken on. A house, a field, a
  herd, crossing the map. A project eats days that never come back, competes
  directly with staying safe, and can fail.

The loop is the pressure. The projects are the life. Which projects a player chose
*is* their answer to the question.

Turn-based. Sessions of 20–40 minutes. One run = one life.

**Central tension:** surviving is easy, living is expensive. Bare subsistence must be
genuinely achievable and genuinely empty. The game never says this; it just makes it
true (see Soul decay under monotony).

---

## 3. Time

One clock, fed two ways:

- **Turn-based while playing.** Actions advance game time.
- **Real time while away.** Elapsed wall-clock time is simulated forward on load.

Consequence: a life can be lived quickly by playing a lot, or slowly by letting real
time carry it. Both are legitimate.

### Absence

While away, the character does not freeze — they **subsist on what was prepared**,
consuming stores, burning stacked wood, sheltering in what was built.

- Well provisioned → return to someone thin, lonely, alive.
- Hand to mouth → dead in two weeks.

Preparation is insurance against the player's own real-life absence. Returning after
a long gap should hurt in the right ways: Soul badly decayed, fire long out, field
gone to weeds, an animal wandered off. Alive, but diminished.

Starting ratio: **~1 real hour ≈ 1 game day** while away. Configurable in
`config.py`, tuned after play.

### Aging

One run = one life, 60–70 years. Effort ceiling falls with age. Permadeath, one save.

**Not in this slice, and deliberately not faked.** The graphical vertical slice runs
on minutes, hours and days. It does not simulate a lifetime, and it does not reach
one by making time pass absurdly fast — a sixty-year life compressed into an evening
would be a number going up, not a life. What exists now is the groundwork:
`Clock.step` is a variable, `Player.age_days` is a real field, and the tick is
already chunked so a widening step cannot skip over the moment of death.

### Development requirement

Time acceleration debug mode **from day one**, or none of this is testable.

---

## 4. Systems and how they interact

```
                 ┌──────────┐
    monotony ───▶│   SOUL   │◀─── sustained by SPIRIT
    isolation    └────┬─────┘
    loss              │ narrows available actions
                      │ slows Effort recovery
                      ▼
   food ────▶ ┌───────────────┐ ────▶ can you work today
   water ────▶│  BODY/EFFORT  │ ────▶ can you travel
   warmth ───▶└───────┬───────┘ ────▶ can you survive the night
                      │
                      ▼
              projects advance ────▶ finishing feeds SOUL
              stores accumulate ───▶ survives ABSENCE
```

The single spiral that must always be live: **cold + hungry + tired → injury risk up
→ injury cuts labour → less food → colder.**

**Skills grow by doing.** No experience menu, no character creation. Spend 200 days
hunting and the character is a hunter. The character is the thing the game is about
creating.

---

## 5. Data model

Plain classes and dataclasses. JSON save. No ORM, no schema library.

```
Clock
    game_minutes: int          # absolute game time since birth
    real_saved_at: float       # UTC epoch, for absence simulation
    step: int                  # minutes per turn — VARIABLE from day one

Tile
    terrain: TerrainType
    resources: dict[str, int]
    seen: bool

World
    seed: int
    width, height: int
    tiles: list[list[Tile]]

Needs
    # Body — visible
    water, food, warmth, rest, health: float
    # Soul — described, not shown
    soul: float
    # Spirit — never shown
    spirit: float

Player
    name: str
    x, y: int
    needs: Needs
    inventory: dict[str, int]
    skills: dict[str, float]
    age_days: int
    alive: bool

Action
    name, key: str
    time_cost: int             # minutes
    effort_cost: float
    requires: dict
    effects: callable

Chronicle
    entries: list[(game_minutes, str)]
```

**`Clock.step` is a variable, not a constant, from the first commit.** Retrofitting a
widening time step (hours → days → seasons) later would be miserable.

---

## 6. Module layout

Flat. Twelve modules. Split only when a file actually gets big.

```
life-creation/                  (repo root)
├── main.py                     entry point — python main.py
├── DESIGN.md                   this file
├── pyproject.toml              dependencies, pytest config
├── assets/                     empty; art is drawn procedurally at start-up
├── life_creation/
│   ├── config.py               all tunables: rates, ratios, map size, timings
│   │
│   │                           — the simulation —
│   ├── clock.py                game time, phases, variable step, debug scale
│   ├── world.py                grid, terrain, generation, validation
│   ├── player.py               the character
│   ├── needs.py                Body / Soul / Spirit definitions and decay
│   ├── fire.py                 fire as an object: fuel, warmth, light
│   ├── perception.py           sight radius, fog of war, Spirit's widening
│   ├── actions.py              what can be done, costs, effects
│   ├── skills.py               growth by doing
│   ├── game.py                 the rules. Commands in, Outcomes out.
│   ├── commands.py             what the player may ask for
│   ├── outcomes.py             what the simulation says happened
│   ├── chronicle.py            life record and ending text
│   ├── viewmodel.py            what the screen is allowed to know
│   ├── agents.py               rule-based agents for the test harness
│   │
│   │                           — the controller —
│   ├── application.py          input lock, turn gate, runs and restarts
│   │
│   │                           — the front ends —
│   ├── ui.py                   terminal, optional debugging  `--terminal`
│   └── presentation/           the game: arcade window, views, renderers
│
│   ├── absence.py              offline simulation on load      (Phase 3)
│   └── save.py                 JSON persistence                (Phase 3)
├── tests/                      unit, integration, simulation, smoke
└── tools/simulate.py           headless play, thousands of runs
```

The twelve-module target in the original plan was a guideline, not a budget. The
count grew where the code genuinely split along a seam — fire, perception,
commands, outcomes — and nowhere else.

### Architectural rules

1. **Game logic never prints and never draws.** Only the front ends
   (`presentation/`, `ui.py`) touch the screen or read keys. Everything else
   returns data. This has paid for itself twice now: the windowed front end and
   then the graphical one both arrived without changing a single rule.
2. **The simulation imports no graphics framework.** Dependencies run one way —
   presentation → application → simulation — and never back. Enforced by
   `tests/smoke/test_architecture.py`, which parses every simulation module and
   fails on a forbidden import.
3. **All tunables live in `config.py`.** No magic numbers in system code.
4. **Every random draw comes from a seeded generator.** The global `random`
   stream is never used, or seeds would not reproduce. Also enforced by test.

### Front ends

- **Graphical (default).** Arcade 3.3. Procedurally generated tile textures,
  animated water and flame, layered lighting, a following camera.
- **Terminal (`--terminal`).** Kept only as a debugging interface, for a machine
  with no working OpenGL. ANSI escapes with VT processing enabled on Windows via
  `ctypes`; single keypress via `msvcrt`, with a `termios`/`tty` fallback.

---

## 7. Repo decisions

- The game **is** the repo's purpose. The remote is already named `life-creation`.
- `the-game-theory/` was removed in commit `899ad83`, when the game first landed.
  This paragraph used to say it was being kept untouched; it is recorded here as
  history rather than quietly deleted.
- `README.md` describes the game.
- Entry point is a root-level `main.py`.

---

## 8. MVP — the Phase 2 vertical slice

The smallest thing that proves the concept and is playable tonight.

1. `python main.py` opens the graphical game (after `pip install -r requirements.txt`)
2. Opening screen: *How will you live your life?* → asks a name, nothing else
3. Flat square grid (64×40), procedurally generated, several terrain types
4. Rendered terrain tiles, animated water and flame, layered day/night lighting,
   fog of war with memory, a quiet HUD
5. Single-key movement, turn-based, one keypress = one turn
6. Clock advancing, day/night
7. **Body** needs ticking at Rule-of-Threes rates: water, food, warmth, rest
8. 4–5 actions: drink, forage, gather wood, rest, build fire
9. Fire as the first real gate — build it, keep it lit, survive the night
10. **Soul** present and ticking, expressed in one line of prose
11. **Spirit** present and ticking, never displayed
12. Death when a Body need bottoms out
13. Chronicle on death — the plain facts of the life, ending on *This is how you lived.*

**The fun test:** does surviving the first cold night, by a fire you fought for, feel
earned? If yes, the concept works. If no, no amount of later content saves it.

---

## 9. Explicitly out of scope

Deferred to later phases, listed so nobody quietly builds them:

- Save/load and absence simulation → **Phase 3**
- Seasons beyond the first, weather events → Phase 3/4
- Projects system (the multi-day commitments) → Phase 3
- Injury and illness as conditions → Phase 3
- NPCs, meeting people, partners, children → Phase 4 at the earliest.
  Meeting a person should land properly; it will not if rushed into the slice.
- Farming, herding, taming, the dog → Phase 4
- Metals, bronze, kilns → Phase 4
- Widening time step (hours → days → seasons) → post-MVP, but the data model
  supports it from day one
- Predators and any combat → Phase 4. Human violence stays rare; there is no combat
  system.
- Anything past a flat bounded square map

---

## 10. Settled, for the record

| Decision | |
|---|---|
| Name | Life Creation |
| Platform | **Graphical Python desktop application** |
| Gameplay | **Turn-based.** The simulation advances only when an action resolves. |
| Framework | **Arcade 3.3.** Verified working before the migration began. |
| Terminal mode | **Optional debugging interface only** (`--terminal`) |
| Opening | You wake. No backstory, no explanation. Asked only a name. |
| Character creation | None. Skills grow by doing. |
| Needs | Body (numbers) / Soul (prose) / Spirit (invisible) |
| Rates | Realistic. Water is the emergency, food is the strategy, cold is the ambush. |
| Faith framing | Structure explicit, object unnamed |
| Time | Turn-based playing, real-time away, one clock |
| Absence | Subsist on what was stored |
| Lifespan | One run = one life, 60–70 years, permadeath |
| Map | Flat square grid, procedurally generated |
| Ending | No score. A chronicle. |
| Danger | Winter, then predators, then injury and illness, then weather |
| People | Emergent, never given. Living alone is a valid answer, not a failure. |
