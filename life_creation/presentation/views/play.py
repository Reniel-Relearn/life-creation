"""The game itself.

The flow, every turn, is exactly one direction:

    key press -> controller -> simulation resolves -> outcome -> animation

Nothing in this file decides a rule. It reads the outcome it is handed and
shows it, and it refuses further input until it has finished showing it.
"""

from __future__ import annotations

import arcade

from ... import config
from ...outcomes import EventKind, Outcome
from .. import input as keys
from .. import space
from ..camera import Follow
from ..hud import Hud
from ..lighting import Lighting
from ..particles import Particles
from ..tile_renderer import TileRenderer
from .. import theme
from .base import BACKDROP, key_menu


class GameView(arcade.View):
    def __init__(self, app, session):
        super().__init__()
        self.app = app
        self.session = session

        game = session.game
        self.tiles = TileRenderer(game.world, app.assets)
        self.hud = Hud(app.width, app.height,
                       scrim=app.assets.scrim, scrim_top=app.assets.scrim_top,
                       scrim_corner=app.assets.scrim_corner)
        self.particles = Particles(app.assets.ember)
        self.lighting = Lighting(app.assets, game.world.height, game.clock.phase)

        self.player = arcade.Sprite(app.assets.figure)
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)

        self.fires = arcade.SpriteList()
        self._fire_sprites: list[arcade.Sprite] = []
        self._flame_frame = 0
        self._flame_timer = 0.0

        self.camera = Follow(app, game.world.width, game.world.height)

        # Movement animation. Presentation only - the turn is already resolved.
        self._from = space.tile_centre(game.player.x, game.player.y,
                                       game.world.height)
        self._to = self._from
        self._anim = 1.0
        self._anim_length = config.MOVE_ANIM_SECONDS
        self._death_wait = 0.0

        self.show_journal = False
        self._journal: list[arcade.Text] = []

        self.camera.snap_to(*self._from)
        self.refresh()

    # -- state --------------------------------------------------------------

    def refresh(self) -> None:
        game = self.session.game
        self.tiles.refresh(game.visible(), self._sight_sources())
        self.hud.update(self.session.view())
        self._sync_fires()

    def _sight_sources(self) -> list[tuple[int, int, int]]:
        """Everything that lights the world, for the renderer's soft falloff.

        The simulation decides what is visible; this only tells the renderer
        where sight comes from so the edge of it can fade."""
        game = self.session.game
        sources = [(game.player.x, game.player.y, game.sight_radius())]
        sources.extend((f.x, f.y, f.light_radius) for f in game.fires.lit_fires())
        return sources

    def _sync_fires(self) -> None:
        game = self.session.game
        lit = game.fires.lit_fires()
        texture = self.app.assets.flame_frames[self._flame_frame]
        while len(self._fire_sprites) < len(lit):
            sprite = arcade.Sprite(texture)
            self._fire_sprites.append(sprite)
            self.fires.append(sprite)
        for i, fire in enumerate(lit):
            sprite = self._fire_sprites[i]
            sprite.position = space.tile_centre(fire.x, fire.y,
                                                game.world.height)
            sprite.visible = True
            scale = 0.7 + 0.4 * fire.strength
            sprite.width = config.TILE_SIZE * scale
            sprite.height = config.TILE_SIZE * scale
        for spare in self._fire_sprites[len(lit):]:
            spare.visible = False

    def on_show_view(self) -> None:
        self.window.background_color = BACKDROP

    # -- input --------------------------------------------------------------

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == arcade.key.ESCAPE:
            self.app.show_pause(self)
            return
        if symbol == arcade.key.TAB:
            self.show_journal = not self.show_journal
            if self.show_journal:
                self._build_journal()
            return

        # The input lock. While the screen is still showing the last turn, keys
        # are dropped rather than queued, so leaning on a key cannot bank turns.
        if not self.session.accepting_input:
            return

        if symbol in keys.MOVEMENT:
            self._resolve(self.session.move(keys.MOVEMENT[symbol]))
            return
        if symbol == arcade.key.E:
            action = keys.contextual_action(self.session.game)
            if action:
                self._resolve(self.session.act(action))
            return
        if symbol in keys.ACTIONS:
            self._resolve(self.session.act(keys.ACTIONS[symbol]))

    # -- turn presentation --------------------------------------------------

    def _resolve(self, outcome: Outcome | None) -> None:
        if outcome is None:
            return

        if not outcome.ok:
            # Nothing happened and no time passed. Say so, and leave input open.
            if outcome.messages:
                self.hud.say(outcome.messages[0], seconds=1.4)
            return

        game = self.session.game
        self._from = space.tile_centre(outcome.from_x, outcome.from_y,
                                       game.world.height)
        self._to = space.tile_centre(outcome.to_x, outcome.to_y,
                                     game.world.height)
        self._anim = 0.0
        self._anim_length = self.session.animation_seconds(outcome)

        self.app.audio.for_outcome(outcome)
        self._spark(outcome)
        if outcome.messages:
            self.hud.say(outcome.messages[-1])
        self.refresh()
        if self.show_journal:
            self._build_journal()

    def _spark(self, outcome: Outcome) -> None:
        height = self.session.game.world.height
        for event in outcome.events:
            if event.x is None or event.y is None:
                continue
            x, y = space.tile_centre(event.x, event.y, height)
            if event.kind is EventKind.FIRE_LIT:
                self.particles.emit(x, y, count=18, rise=52, spread=30)
            elif event.kind is EventKind.FIRE_FAILED:
                self.particles.emit(x, y, count=5, rise=16, spread=10,
                                    colour=(120, 120, 128))
            elif event.kind is EventKind.WADED:
                self.particles.emit(x, y, count=10, rise=22, spread=22,
                                    colour=(120, 170, 210))
            elif event.kind is EventKind.GATHERED:
                self.particles.emit(x, y, count=6, rise=14, spread=16,
                                    colour=(140, 116, 82))

    # -- update -------------------------------------------------------------

    def on_update(self, delta_time: float) -> None:
        game = self.session.game

        if self._anim < 1.0:
            self._anim = min(1.0, self._anim + delta_time / self._anim_length)
            if self._anim >= 1.0 and self.session.busy:
                self.session.animation_finished()
                if not game.alive:
                    self._death_wait = config.DEATH_PAUSE_SECONDS

        eased = space.smoothstep(self._anim)
        px = space.lerp(self._from[0], self._to[0], eased)
        py = space.lerp(self._from[1], self._to[1], eased)
        self.player.position = (px, py)

        self.camera.follow(px, py, delta_time)
        self.lighting.update(game.clock.phase, delta_time)
        self.lighting.place(
            (px, py), game.fires.lit_fires(),
            player_light=(game.sight_radius() * 2 + 1) * config.TILE_SIZE * 0.42,
        )
        self.tiles.update_animation(delta_time)
        self.particles.fire_embers(game.fires.lit_fires(), game.world.height,
                                   delta_time)
        self.particles.update(delta_time)
        self.hud.update_animation(delta_time)
        self._animate_flames(delta_time)

        if self._death_wait > 0:
            self._death_wait -= delta_time
            if self._death_wait <= 0:
                self.app.show_chronicle(self.session)

    def _animate_flames(self, delta_time: float) -> None:
        if not self._fire_sprites:
            return
        self._flame_timer += delta_time
        if self._flame_timer < config.FIRE_ANIM_SECONDS:
            return
        self._flame_timer = 0.0
        frames = self.app.assets.flame_frames
        self._flame_frame = (self._flame_frame + 1) % len(frames)
        texture = frames[self._flame_frame]
        for sprite in self._fire_sprites:
            if sprite.visible:
                sprite.texture = texture

    # -- drawing ------------------------------------------------------------

    def on_draw(self) -> None:
        self.clear()

        self.camera.use()
        self.tiles.draw()
        self.fires.draw()
        self.player_list.draw()
        self.particles.draw()
        self.lighting.draw(self.camera.visible_bounds)

        self.window.default_camera.use()
        if self.app.assets.vignette is not None:
            arcade.draw_texture_rect(
                self.app.assets.vignette,
                arcade.LBWH(0, 0, self.window.width, self.window.height))
        self.hud.draw()
        if self.show_journal:
            self._draw_journal()

    # -- journal ------------------------------------------------------------

    def _build_journal(self) -> None:
        from ... import skills as skills_mod

        game = self.session.game
        skills = [
            (skills_mod.LABELS[key],
             skills_mod.describe(skills_mod.level(game.player.skills, key)))
            for key in skills_mod.ALL
        ]

        w, h = self.window.width, self.window.height
        top = h * 0.68
        self._journal = [
            arcade.Text(f"{game.player.name}, day {game.clock.day}",
                        w // 2, top, theme.INK, theme.HEADING,
                        font_name=config.TEXT_FONT, anchor_x="center"),
        ]
        # Competence in words, on the same two-column axis as every other list
        # in the game. There is no skill tree and no number anywhere here.
        self._journal.extend(
            key_menu(self.window, tuple(skills), top - theme.SPACE_6,
                     colour=theme.INK, key_colour=theme.MUTED))
        self._journal.append(
            arcade.Text(f"seed {game.seed}", w // 2,
                        top - theme.SPACE_6 - len(skills) * theme.SPACE_3
                        - theme.SPACE_4,
                        theme.SUBTLE, theme.SMALL,
                        font_name=config.TEXT_FONT, anchor_x="center"))

    def _draw_journal(self) -> None:
        w, h = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(
            w * 0.24, h * 0.22, w * 0.52, h * 0.58,
            theme.with_alpha(theme.SCRIM, 0.94))
        for text in self._journal:
            text.draw()
