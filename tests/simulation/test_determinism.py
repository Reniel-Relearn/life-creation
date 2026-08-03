"""The same seed and the same choices must produce the same life."""

from __future__ import annotations

import random

import pytest

from life_creation import agents
from life_creation.application import Session
from life_creation.commands import Command, Direction

SEQUENCE = [
    Command.move(Direction.RIGHT), Command.move(Direction.DOWN),
    Command.action("g"), Command.action("f"), Command.action("d"),
    Command.move(Direction.LEFT), Command.action("b"), Command.action("m"),
    Command.action("r"), Command.move(Direction.UP), Command.action("b"),
]


def _fingerprint(session: Session):
    game = session.game
    needs = game.player.needs
    return (
        game.clock.minutes, game.player.x, game.player.y,
        round(needs.water, 9), round(needs.food, 9), round(needs.warmth, 9),
        round(needs.rest, 9), round(needs.health, 9),
        round(needs.soul, 9), round(needs.spirit, 9),
        tuple(sorted(game.player.inventory.items())),
        tuple(sorted((k, round(v, 9)) for k, v in game.player.skills.items())),
        len(game.fires), game.player.tiles_seen, tuple(game.log),
    )


def _play(seed: int, commands) -> Session:
    session = Session("Tester", seed)
    for command in commands:
        if not session.game.alive:
            break
        session.submit(command)
        session.animation_finished()
    return session


def test_the_same_seed_and_sequence_give_the_same_life():
    assert _fingerprint(_play(1234, SEQUENCE)) == _fingerprint(_play(1234, SEQUENCE))


def test_a_different_seed_gives_a_different_life():
    assert _fingerprint(_play(1, SEQUENCE)) != _fingerprint(_play(2, SEQUENCE))


def test_the_endings_match_too():
    assert _play(555, SEQUENCE).ending() == _play(555, SEQUENCE).ending()


def test_the_simulation_never_draws_from_the_global_random_stream():
    """Anything else in the process rolling dice must not change the game."""
    first = _play(4242, SEQUENCE)

    random.seed(0)
    for _ in range(500):
        random.random()
    second = _play(4242, SEQUENCE)

    assert _fingerprint(first) == _fingerprint(second)


@pytest.mark.parametrize("agent_name", sorted(agents.AGENTS))
def test_every_agent_replays_identically(agent_name):
    def run():
        session = Session("Tester", 777)
        rng = random.Random(99)
        for _ in range(120):
            if not session.game.alive:
                break
            session.submit(agents.AGENTS[agent_name](session.game, rng))
            session.animation_finished()
        return _fingerprint(session)

    assert run() == run()


@pytest.mark.parametrize("agent_name", sorted(agents.AGENTS))
def test_no_agent_crashes_or_live_locks(agent_name):
    from life_creation import config

    session = Session("Tester", 31337)
    rng = random.Random(5)
    refused_streak = 0
    for _ in range(300):
        if not session.game.alive:
            break
        outcome = session.submit(agents.AGENTS[agent_name](session.game, rng))
        session.animation_finished()
        assert outcome is not None
        refused_streak = 0 if outcome.ok else refused_streak + 1
        assert refused_streak < config.AGENT_STUCK_AFTER, (
            f"{agent_name} repeated a refused action "
            f"{refused_streak} times: {outcome.messages}")


def test_bare_subsistence_is_achievable():
    """It has to be possible to survive doing nothing but the minimum."""
    survived = 0
    for seed in range(20, 32):
        session = Session("Tester", seed)
        rng = random.Random(seed)
        for _ in range(300):
            if not session.game.alive:
                break
            session.submit(agents.subsistence_agent(session.game, rng))
            session.animation_finished()
        if session.game.player.nights_survived >= 1:
            survived += 1
    assert survived >= 6, f"only {survived}/12 subsistence runs saw a dawn"


def test_ignoring_the_cold_kills_you():
    """The first night is a real gate, not a formality."""
    died = 0
    for seed in range(40, 52):
        session = Session("Tester", seed)
        rng = random.Random(seed)
        for _ in range(300):
            if not session.game.alive:
                break
            session.submit(agents.explorer_agent(session.game, rng))
            session.animation_finished()
        if not session.game.alive:
            died += 1
    assert died >= 8, f"only {died}/12 fireless runs died"
