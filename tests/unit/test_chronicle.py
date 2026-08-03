"""The chronicle: the plain facts of a life, read back in order."""

from __future__ import annotations

import pytest

from life_creation import config
from life_creation.chronicle import Chronicle, compose
from life_creation.commands import Command, Direction
from life_creation.game import Game
from tests.conftest import FixedRng, give_wood, set_time
from life_creation.world import TerrainType

FINAL = "This is how you lived."


def _ending(game: Game) -> list[str]:
    return game.ending()


def _on_grass(game):
    for y in range(game.world.height):
        for x in range(game.world.width):
            if game.world.at(x, y).terrain.key is TerrainType.GRASS:
                game.player.x, game.player.y = x, y
                return


def test_it_always_ends_on_the_same_line(game):
    assert _ending(game)[-1] == FINAL


def test_it_opens_with_the_name_and_the_days_lived(game):
    lines = _ending(game)
    assert lines[0] == f"{game.player.name} lived 1 day."

    # The clock is moved directly: this is about how the chronicle counts days,
    # not about whether the character could have survived them.
    game.clock.advance(3 * config.MINUTES_PER_DAY)
    assert _ending(game)[0].startswith(f"{game.player.name} lived 4 days")


def test_a_single_day_is_not_pluralised(game):
    assert "lived 1 day." in _ending(game)[0]


def test_the_cause_of_death_is_named(game):
    game.player.needs.warmth = 0.0
    game.player.needs.health = 1.0
    game.advance(config.MINUTES_PER_HOUR)
    assert not game.alive
    assert "The cold took you." in _ending(game)


@pytest.mark.parametrize("cause,phrase", [
    ("cold", "The cold took you."),
    ("thirst", "You died of thirst."),
    ("hunger", "You starved."),
])
def test_each_cause_of_death_has_its_own_line(game, cause, phrase):
    game.player.needs.health = 0.0
    game.player.needs.death_cause = cause
    assert phrase in _ending(game)


def test_surviving_says_so_instead(game):
    assert "You were still alive when you set this down." in _ending(game)


def test_the_most_common_activity_is_measured_in_time_not_tallies(game):
    """Twenty short drinks are not 'most of your days'; a long sleep is."""
    chronicle = Chronicle()
    for _ in range(20):
        chronicle.record_action("d", config.DRINK_MINUTES)
    chronicle.record_action("s", 8 * config.MINUTES_PER_HOUR)
    key, _ = chronicle.most_time_on()
    assert key == "s"


def test_what_you_actually_did_is_what_it_reports(session):
    game = session.game
    for _ in range(8):
        session.submit(Command.move(Direction.RIGHT))
        session.animation_finished()
    assert "You spent most of your days walking." in _ending(game)


def test_the_first_fire_is_dated(game):
    _on_grass(game)
    give_wood(game, 2)
    game.rng = FixedRng(0.0)
    game.submit(Command.action("b"))
    assert "You made fire on the 1st day." in _ending(game)


def test_never_making_fire_is_recorded_too(game):
    assert "You never made fire." in _ending(game)


def test_a_fire_lit_on_a_later_day_is_dated_correctly(game):
    game.advance(2 * config.MINUTES_PER_DAY)
    _on_grass(game)
    give_wood(game, 2)
    game.rng = FixedRng(0.0)
    game.submit(Command.action("b"))
    if game.alive:
        assert "You made fire on the 3rd day." in _ending(game)


def test_nights_survived_are_counted(game):
    set_time(game, 5, 30)
    game.advance(config.MINUTES_PER_HOUR)
    assert "You came through 1 night." in _ending(game)


def test_exploration_is_described_in_proportion_to_the_world(game):
    lines = _ending(game)
    assert any(line.startswith("You never went far")
               or line.startswith("You kept to one corner")
               or line.startswith("You saw") for line in lines)


def test_walking_further_changes_what_it_says(session):
    game = session.game
    near = [line for line in _ending(game) if "world" in line or "far" in line]
    for _ in range(30):
        session.submit(Command.move(Direction.RIGHT))
        session.animation_finished()
        session.submit(Command.move(Direction.DOWN))
        session.animation_finished()
    far = [line for line in _ending(game) if "world" in line or "far" in line]
    assert near != far


def test_stillness_is_reported_through_spirit_and_nowhere_else(game):
    for _ in range(30):
        if not game.alive:
            break
        game.submit(Command.action("m"))
    lines = _ending(game)
    assert any("still" in line for line in lines)
    assert not any("spirit" in line.lower() for line in lines)


def test_never_stopping_is_recorded(game):
    game.player.needs.spirit = 0.0
    assert "You never once stopped." in _ending(game)


def test_the_chronicle_names_no_faith_and_no_text(game):
    for _ in range(20):
        if not game.alive:
            break
        game.submit(Command.action("m"))
    text = " ".join(_ending(game)).lower()
    for word in ("god", "pray", "prayer", "bible", "scripture", "church",
                 "religion", "holy"):
        assert word not in text


def test_there_is_no_score_no_grade_and_no_verdict(game):
    text = " ".join(_ending(game)).lower()
    for word in ("score", "grade", "rank", "medal", "points", "percent",
                 "win", "lose", "good ending", "bad ending", "congratulations"):
        assert word not in text


def test_skills_are_described_in_words_not_numbers(game):
    for _ in range(10):
        if not game.alive:
            break
        game.submit(Command.action("m"))
    line = next((line for line in _ending(game) if "By the end" in line), None)
    assert line is not None
    assert not any(ch.isdigit() for ch in line)


def test_a_life_with_no_practice_says_so(game):
    assert "You never got good at anything." in _ending(game)


def test_water_sources_found_are_remembered(game):
    game.chronicle.found_water(1, 1)
    game.chronicle.found_water(1, 1)
    game.chronicle.found_water(9, 9)
    assert len(game.chronicle.water_sources) == 2
    assert "You drank from 2 different places." in _ending(game)


def test_milestones_are_recorded_once_even_if_marked_twice(game):
    game.chronicle.mark("first_fire", game.clock, "you made fire for the first time")
    day = game.chronicle.day_of("first_fire")
    game.advance(config.MINUTES_PER_DAY)
    game.chronicle.mark("first_fire", game.clock, "you made fire for the first time")
    assert game.chronicle.day_of("first_fire") == day


def test_the_running_record_is_bounded(game):
    for i in range(config.MAX_CHRONICLE_ENTRIES + 50):
        game.chronicle.note(i, f"entry {i}")
    assert len(game.chronicle.entries) <= config.MAX_CHRONICLE_ENTRIES


def test_the_log_is_bounded(game):
    for i in range(config.MAX_LOG_ENTRIES + 50):
        game.say(f"line {i}")
    assert len(game.log) <= config.MAX_LOG_ENTRIES
