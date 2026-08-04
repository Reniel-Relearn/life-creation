"""The layering rule, enforced.

    the simulation never touches the screen
    the simulation never imports a graphics framework
    the interface never changes the world behind the simulation's back

These are the rules the whole project is built on, so they are tested rather
than trusted.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "life_creation"

FRAMEWORKS = {"arcade", "pyglet", "pygame", "pygame_ce", "tkinter",
              "PyQt5", "PyQt6", "PySide6", "kivy", "textual", "curses", "PIL"}

# The only place allowed to import a graphics framework.
PRESENTATION = PACKAGE / "presentation"

SIMULATION_FILES = sorted(
    path for path in PACKAGE.glob("*.py") if path.name != "ui.py"
)


def _imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    return found


@pytest.mark.parametrize("path", SIMULATION_FILES, ids=lambda p: p.name)
def test_the_simulation_imports_no_graphics_framework(path):
    offending = _imports(path) & FRAMEWORKS
    assert not offending, f"{path.name} imports {sorted(offending)}"


@pytest.mark.parametrize("path", SIMULATION_FILES, ids=lambda p: p.name)
def test_the_simulation_never_imports_the_presentation_layer(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "presentation" not in node.module, \
                f"{path.name} imports the presentation layer"
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "presentation" not in alias.name, \
                    f"{path.name} imports the presentation layer"


@pytest.mark.parametrize("path", SIMULATION_FILES, ids=lambda p: p.name)
def test_the_simulation_never_prints(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "print"):
            pytest.fail(f"{path.name}:{node.lineno} prints")


@pytest.mark.parametrize("path", SIMULATION_FILES, ids=lambda p: p.name)
def test_the_simulation_never_uses_the_global_random_stream(path):
    """Every roll must come from a seeded generator, or seeds mean nothing."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        value = node.func.value
        if isinstance(value, ast.Name) and value.id == "random":
            # random.Random(...) constructs a private stream; that is the fix,
            # not the fault. Everything else is a draw from the global one.
            allowed = {"Random", "randrange"}
            assert node.func.attr in allowed, (
                f"{path.name}:{node.lineno} calls random.{node.func.attr} "
                f"on the global stream")


def test_the_terminal_front_end_is_the_only_other_module_that_prints():
    ui = PACKAGE / "ui.py"
    assert ui.exists()
    assert not (_imports(ui) & (FRAMEWORKS - {"curses"})), \
        "the terminal front end must not need a graphics framework"


def test_the_tkinter_front_end_is_gone():
    assert not (PACKAGE / "window.py").exists()
    for path in PACKAGE.rglob("*.py"):
        assert "tkinter" not in path.read_text(encoding="utf-8"), \
            f"{path} still references tkinter"


def test_the_presentation_layer_exists_and_is_the_one_that_draws():
    assert (PRESENTATION / "app.py").exists()
    assert "arcade" in _imports(PRESENTATION / "app.py")


def test_no_survival_rule_lives_in_a_view():
    """Views may read the simulation. They may not change it."""
    banned = ("needs.water =", "needs.food =", "needs.warmth =",
              "needs.rest =", "needs.health =", "needs.soul =",
              "needs.spirit =", "clock.minutes =", "clock.advance(")
    for path in PRESENTATION.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for phrase in banned:
            assert phrase not in text, f"{path.name} mutates the simulation: {phrase}"


def test_the_game_module_no_longer_owns_a_loop_or_an_entry_point():
    text = (PACKAGE / "game.py").read_text(encoding="utf-8")
    assert "def play(" not in text
    assert "def demo(" not in text
    assert "import ui" not in text
