"""Play the game thousands of times with no window and no keyboard.

    python -m tools.simulate --seed 1234 --runs 100

This is a correctness harness. It opens no window, imports no graphics
framework, and checks after every single turn that the simulation is still
telling the truth about itself.

The statistics it prints are for spotting gross balance faults and nothing
else. A ninety percent first-night survival rate would say the rules hold
together; it would not say the game is worth playing.
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
from dataclasses import dataclass, field

from life_creation import actions as actions_mod
from life_creation import agents, config
from life_creation.application import Session
from life_creation.commands import Command, CommandKind


@dataclass
class RunResult:
    seed: int
    agent: str
    turns: int = 0
    days: int = 0
    survived_first_night: bool = False
    nights: int = 0
    alive: bool = True
    death_cause: str | None = None
    hit_turn_cap: bool = False
    problems: list[str] = field(default_factory=list)
    command_log: list[tuple] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Invariants - checked after every turn of every run
# ---------------------------------------------------------------------------

def check_invariants(game, outcome, before_minutes: int) -> list[str]:
    bad: list[str] = []
    needs = game.player.needs

    for name in ("water", "food", "warmth", "rest", "health", "soul", "spirit"):
        value = getattr(needs, name)
        if not (0.0 <= value <= 100.0):
            bad.append(f"{name} out of bounds: {value!r}")

    for item, count in game.player.inventory.items():
        if count < 0:
            bad.append(f"negative inventory: {item}={count}")

    if not game.world.in_bounds(game.player.x, game.player.y):
        bad.append(f"player off the map at ({game.player.x},{game.player.y})")

    for fire in game.fires:
        if fire.fuel < 0 or fire.fuel > config.FIRE_MAX_FUEL:
            bad.append(f"fire fuel out of range: {fire.fuel}")
        if fire.lit and fire.lit_at_minute > game.clock.minutes:
            bad.append("fire lit in the future")

    if outcome.ok and outcome.minutes > 0 and game.clock.minutes <= before_minutes:
        bad.append(
            f"frozen clock: {outcome.command_name} cost {outcome.minutes}m "
            f"but the clock stayed at {game.clock.minutes}")

    if needs.health <= 0.0 and game.player.alive:
        bad.append("health at zero but still alive")
    if not game.player.alive and needs.death_cause is None:
        bad.append("dead with no cause of death")

    first_fires = [t for _, t in game.chronicle.entries
                   if t == "you made fire for the first time"]
    if len(first_fires) > 1:
        bad.append(f"first fire recorded {len(first_fires)} times")

    return bad


def check_action_legality(game_before: dict, command: Command,
                          outcome) -> list[str]:
    """Impossible actions must fail, and possible ones must not fail wrongly."""
    bad: list[str] = []
    if command.kind is not CommandKind.ACTION:
        return bad

    key = command.action_key
    if key == actions_mod.DRINK:
        if outcome.ok and not game_before["water_in_reach"]:
            bad.append("drank with no water in reach")
        if not outcome.ok and game_before["water_in_reach"]:
            bad.append("refused to drink with water in reach")
    elif key == actions_mod.GATHER:
        if outcome.ok and game_before["wood_here"] <= 0:
            bad.append("gathered wood from a tile with none")
    elif key == actions_mod.FORAGE:
        if outcome.ok and game_before["forage_here"] <= 0:
            bad.append("foraged food from a tile with none")
    elif key == actions_mod.FIRE:
        if outcome.ok and game_before["wet_ground"] and not game_before["fire_here"]:
            bad.append("lit a fire on wet ground")
        if (outcome.ok and not game_before["fire_here"]
                and game_before["wood_carried"] <= 0):
            bad.append("built a fire with no wood")
    return bad


def snapshot(game) -> dict:
    tile = game.tile()
    return {
        "water_in_reach": (
            tile.terrain.drinkable
            or any(t.terrain.drinkable
                   for _, _, t in game.world.neighbours(game.player.x, game.player.y))
        ),
        "wood_here": tile.resources.get("wood", 0),
        "forage_here": tile.resources.get("forage", 0),
        "wet_ground": tile.terrain.drinkable,
        "fire_here": game.fires.at(game.player.x, game.player.y) is not None,
        "wood_carried": game.player.carrying("wood"),
        "exhausted": game.player.needs.exhausted,
    }


# ---------------------------------------------------------------------------
# One run
# ---------------------------------------------------------------------------

def play_run(seed: int, agent_name: str, max_turns: int) -> RunResult:
    result = RunResult(seed=seed, agent=agent_name)
    choose = agents.AGENTS[agent_name]
    rng = random.Random(seed ^ hash(agent_name) & 0xFFFF)

    session = Session("Test", seed)
    game = session.game

    if game.world_report.problems:
        result.problems.append(
            "world: " + "; ".join(game.world_report.problems))

    refused_streak = 0
    for _ in range(max_turns):
        if not game.alive:
            break
        before_minutes = game.clock.minutes
        before = snapshot(game)

        command = choose(game, rng)
        outcome = session.submit(command)
        session.animation_finished()

        if outcome is None:
            result.problems.append("controller refused a turn while accepting")
            break

        result.command_log.append(
            (command.kind.value, command.direction.value if command.direction
             else command.action_key))

        if outcome.ok:
            result.turns += 1
            refused_streak = 0
        else:
            # A refused action costs no time. Repeating one forever is a
            # live-lock: the run would burn its whole budget standing still.
            refused_streak += 1
            if refused_streak >= config.AGENT_STUCK_AFTER:
                message = outcome.messages[0] if outcome.messages else "(silent)"
                result.problems.append(
                    f"live-lock: {refused_streak} consecutive refused "
                    f"'{outcome.command_name}' - {message}")
                break

        result.problems.extend(check_invariants(game, outcome, before_minutes))
        result.problems.extend(check_action_legality(before, command, outcome))

        if game.player.nights_survived >= 1 and not result.survived_first_night:
            result.survived_first_night = True
    else:
        result.hit_turn_cap = True
        if game.player.needs.health <= 0:
            result.problems.append("body was fatally depleted but the run never ended")

    result.days = game.clock.day
    result.nights = game.player.nights_survived
    result.alive = game.alive
    result.death_cause = game.player.needs.death_cause

    # The ending must always compose, whatever shape the life took.
    ending = game.ending()
    if not ending or ending[-1] != "This is how you lived.":
        result.problems.append("chronicle did not end correctly")

    return result


def replay(seed: int, commands: list[tuple]) -> tuple:
    """Re-run a recorded command sequence and fingerprint the result."""
    from life_creation.commands import Direction

    session = Session("Test", seed)
    game = session.game
    for kind, value in commands:
        if not game.alive:
            break
        command = (Command.move(Direction(value)) if kind == "move"
                   else Command.action(value))
        session.submit(command)
        session.animation_finished()
    needs = game.player.needs
    return (
        game.clock.minutes, game.player.x, game.player.y,
        round(needs.water, 6), round(needs.food, 6), round(needs.warmth, 6),
        round(needs.rest, 6), round(needs.health, 6), round(needs.soul, 6),
        round(needs.spirit, 6), game.player.carrying("wood"),
        game.player.nights_survived, len(game.fires),
    )


# ---------------------------------------------------------------------------
# The harness
# ---------------------------------------------------------------------------

def simulate(seed: int, runs: int, agent_names: list[str],
             max_turns: int, check_determinism: int) -> int:
    results: list[RunResult] = []
    crashes: list[str] = []

    for index in range(runs):
        agent_name = agent_names[index % len(agent_names)]
        run_seed = seed + index
        try:
            results.append(play_run(run_seed, agent_name, max_turns))
        except Exception as exc:               # a crash is the headline result
            crashes.append(f"seed {run_seed} agent {agent_name}: "
                           f"{type(exc).__name__}: {exc}")

    determinism_failures = []
    for result in results[:check_determinism]:
        first = replay(result.seed, result.command_log)
        second = replay(result.seed, result.command_log)
        if first != second:
            determinism_failures.append(
                f"seed {result.seed} agent {result.agent}: {first} != {second}")

    return report(results, crashes, determinism_failures, runs)


def report(results: list[RunResult], crashes: list[str],
           determinism_failures: list[str], requested: int) -> int:
    print()
    print("Life Creation - simulation harness")
    print("=" * 66)
    print(f"  runs requested      {requested}")
    print(f"  runs completed      {len(results)}")
    print(f"  crashes             {len(crashes)}")

    for line in crashes:
        print(f"      ! {line}")

    if not results:
        print("\n  RESULT: FAIL (no run completed)\n")
        return 1

    days = [r.days for r in results]
    first_nights = [r for r in results if r.survived_first_night]
    print(f"  first-night survival {len(first_nights)}/{len(results)} "
          f"({100.0 * len(first_nights) / len(results):.0f}%)")
    print(f"  average days lived   {statistics.mean(days):.2f}")
    print(f"  median days lived    {statistics.median(days):.1f}")
    print(f"  average turns/life   "
          f"{statistics.mean([r.turns for r in results]):.1f}")

    causes: dict[str, int] = {}
    for result in results:
        key = result.death_cause if not result.alive else "survived to the cap"
        causes[key or "unknown"] = causes.get(key or "unknown", 0) + 1
    print("  causes of death")
    for cause, count in sorted(causes.items(), key=lambda kv: -kv[1]):
        print(f"      {cause:<22}{count}")

    print("  by agent")
    by_agent: dict[str, list[RunResult]] = {}
    for result in results:
        by_agent.setdefault(result.agent, []).append(result)
    for name, group in sorted(by_agent.items()):
        survived = sum(1 for r in group if r.survived_first_night)
        mean_days = statistics.mean([r.days for r in group])
        print(f"      {name:<14}{len(group):>3} runs   "
              f"first night {survived}/{len(group):<4} "
              f"mean {mean_days:.1f} days")

    suspicious = [r for r in results if r.problems]
    print(f"  suspicious runs     {len(suspicious)}")
    seen: set[str] = set()
    for result in suspicious[:12]:
        for problem in result.problems:
            if problem in seen:
                continue
            seen.add(problem)
            print(f"      ! seed {result.seed} ({result.agent}): {problem}")

    print(f"  determinism checks  {len(determinism_failures)} failed")
    for line in determinism_failures:
        print(f"      ! {line}")

    failed = bool(crashes or suspicious or determinism_failures)
    print("=" * 66)
    print("  RESULT: " + ("FAIL" if failed else "PASS"))
    print()
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tools.simulate",
        description="Run the simulation headlessly and check it holds together.",
    )
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--agents", default="all",
                        help="comma separated, or 'all'")
    parser.add_argument("--max-turns", type=int, default=config.AGENT_MAX_TURNS)
    parser.add_argument("--determinism-checks", type=int, default=6,
                        help="how many runs to replay twice and compare")
    args = parser.parse_args(argv)

    if args.agents == "all":
        names = list(agents.AGENTS)
    else:
        names = [n.strip() for n in args.agents.split(",") if n.strip()]
        unknown = [n for n in names if n not in agents.AGENTS]
        if unknown:
            parser.error(f"unknown agents: {', '.join(unknown)}")

    return simulate(args.seed, args.runs, names, args.max_turns,
                    args.determinism_checks)


if __name__ == "__main__":
    sys.exit(main())
