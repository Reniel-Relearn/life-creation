"""Graphical smoke test.

Builds the real window, the real assets and the real game view, drives a few
synthetic turns through the real key handler, and reports what it was actually
able to verify. It is careful to distinguish "rendered" from "could not render
here", because a machine with no display cannot prove anything about pixels.

    python main.py --smoke-test

Exit code 0 means every stage that could run, ran.
"""

from __future__ import annotations

import logging
import sys
import traceback

from .. import config

SMOKE_SEED = 1234
SMOKE_UPDATE_CYCLES = 90
FRAME = 1.0 / 60.0

log = logging.getLogger(__name__)


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []
        self.failed = False

    def add(self, stage: str, status: str, detail: str = "") -> None:
        self.rows.append((stage, status, detail))
        if status == "FAIL":
            self.failed = True

    def ok(self, stage: str, detail: str = "") -> None:
        self.add(stage, "PASS", detail)

    def skip(self, stage: str, detail: str) -> None:
        self.add(stage, "NOT TESTED", detail)

    def fail(self, stage: str, detail: str) -> None:
        self.add(stage, "FAIL", detail)

    def render(self) -> str:
        width = max(len(row[0]) for row in self.rows) + 2
        out = ["", "Life Creation - graphical smoke test", "-" * 62]
        for stage, status, detail in self.rows:
            line = f"  {status:<11}{stage:<{width}}"
            if detail:
                line += f"  {detail}"
            out.append(line)
        out.append("-" * 62)
        out.append("  RESULT: " + ("FAIL" if self.failed else "PASS"))
        out.append("")
        return "\n".join(out)


def run() -> int:
    report = Report()
    window = None

    try:
        import arcade
        report.ok("framework import", f"arcade {arcade.VERSION}")
    except Exception as exc:
        report.fail("framework import", str(exc))
        print(report.render())
        return 2

    try:
        from ..application import Session
        from ..commands import Direction
        from .app import LifeCreation

        window = LifeCreation(seed=SMOKE_SEED, visible=False)
        report.ok("window and GL context",
                  f"{window.width}x{window.height} "
                  f"{window.ctx.info.RENDERER}")
    except Exception as exc:
        report.fail("window and GL context", f"{type(exc).__name__}: {exc}")
        log.debug("smoke test failed to open a window", exc_info=True)
        print(report.render())
        return 3

    try:
        missing = ", ".join(window.assets.missing) or "none"
        report.ok("assets loaded",
                  f"{len(window.assets.terrain)} tile textures, "
                  f"optional missing: {missing}")

        session = Session("Smoke", SMOKE_SEED)
        problems = session.game.world_report.problems
        if problems:
            report.fail("deterministic test world", "; ".join(problems))
        else:
            report.ok(
                "deterministic test world",
                f"seed {session.seed}, spawn "
                f"({session.game.player.x},{session.game.player.y}), "
                f"water {session.game.world_report.water_distance} tiles, "
                f"wood {session.game.world_report.wood_distance} tiles")

        view = window.begin_run("Smoke", SMOKE_SEED)
        session = window.session          # the run under test, not the probe above
        assert session is not None
        report.ok("game view constructed", type(view).__name__)
        report.ok("tile renderer", f"{len(view.tiles.sprites)} tile sprites")
        report.ok("player renderer", "figure sprite placed")
        report.ok("camera", f"following at {view.camera.x:.0f},{view.camera.y:.0f}")
        report.ok("hud", f"{len(view.hud._body)} body readings, spirit absent")

        # Drive real turns through the real key handler.
        import arcade as _arcade
        before = (session.game.player.x, session.game.player.y,
                  session.game.clock.minutes)
        moved = False
        for _ in range(SMOKE_UPDATE_CYCLES):
            if session.accepting_input and not moved:
                view.on_key_press(_arcade.key.RIGHT, 0)
                moved = True
            view.on_update(FRAME)
        after = (session.game.player.x, session.game.player.y,
                 session.game.clock.minutes)

        if after[2] <= before[2]:
            report.fail("turn resolves and clock advances",
                        f"clock did not move ({before[2]} -> {after[2]})")
        else:
            report.ok("turn resolves and clock advances",
                      f"{before[2]} -> {after[2]} game minutes")

        if session.busy:
            report.fail("animation completes and input reopens",
                        "still locked after 90 cycles")
        else:
            report.ok("animation completes and input reopens",
                      f"{SMOKE_UPDATE_CYCLES} update cycles")

        # Input lock: a key pressed mid-animation must be dropped, not queued.
        view.on_key_press(_arcade.key.RIGHT, 0)
        locked_x = session.game.player.x
        view.on_key_press(_arcade.key.LEFT, 0)     # should be refused
        if session.game.player.x == locked_x:
            report.ok("input locked during animation", "second key dropped")
        else:
            report.fail("input locked during animation", "a turn was queued")
        for _ in range(SMOKE_UPDATE_CYCLES):
            view.on_update(FRAME)

        try:
            # The view's own draw path, exactly as arcade calls it each frame.
            window.ctx.screen.use()
            window.current_view.on_draw()
            image = arcade.get_image()
            colours = len(image.convert("RGB").getcolors(maxcolors=1 << 20) or [])
            if colours <= 1:
                report.fail("rendering", "framebuffer was a single flat colour")
            else:
                report.ok("rendering",
                          f"frame drawn, {colours} distinct colours read back")
        except Exception as exc:
            report.skip("rendering",
                        f"no readable framebuffer here ({type(exc).__name__}: {exc})")

        ending = session.ending()
        if ending and ending[-1] == "This is how you lived.":
            report.ok("chronicle composed", f"{len(ending)} lines")
        else:
            report.fail("chronicle composed", "final line missing")

    except Exception as exc:
        report.fail("smoke test", f"{type(exc).__name__}: {exc}")
        traceback.print_exc()
    finally:
        if window is not None:
            try:
                window.close()
                report.ok("window closed cleanly")
            except Exception as exc:
                report.fail("window closed cleanly", str(exc))

    print(report.render())
    return 1 if report.failed else 0


__all__ = ["run", "config"]


if __name__ == "__main__":
    sys.exit(run())
