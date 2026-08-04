"""Every texture and sound the game uses, in one place.

Art is generated procedurally at load time from original code - there are no
downloaded assets and nothing is copyrighted. If a real PNG is later dropped
into `assets/tiles/<name>.png` it is used instead, so replacing placeholder art
never means touching the renderer.

Nothing in here is allowed to be fatal. A missing optional file is a missing
optional file, not a crash.
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

import arcade
from PIL import Image, ImageDraw

from .. import config
from ..world import TerrainType
from . import theme

log = logging.getLogger(__name__)

ASSET_ROOT = Path(__file__).resolve().parent.parent.parent / "assets"
TILE_DIR = ASSET_ROOT / "tiles"
SPRITE_DIR = ASSET_ROOT / "sprites"
AUDIO_DIR = ASSET_ROOT / "audio"

TERRAIN_VARIANTS = 3

# The palette each terrain is drawn from: base, and two shades for detail.
_PALETTE: dict[TerrainType, tuple[tuple[int, int, int], ...]] = {
    TerrainType.GRASS: ((104, 138, 78), (122, 156, 90), (86, 118, 66)),
    TerrainType.FOREST: ((48, 88, 56), (62, 106, 66), (32, 62, 42)),
    TerrainType.WATER: ((58, 110, 158), (86, 142, 188), (40, 84, 128)),
    TerrainType.MARSH: ((108, 116, 82), (126, 132, 98), (84, 92, 66)),
    TerrainType.HILLS: ((128, 122, 112), (152, 146, 136), (98, 92, 84)),
    TerrainType.BARE: ((122, 106, 88), (140, 124, 104), (98, 84, 70)),
}


def _noise(draw: ImageDraw.ImageDraw, rng: random.Random, size: int,
           colour: tuple[int, int, int], count: int, spread: int = 2) -> None:
    for _ in range(count):
        x = rng.randrange(size)
        y = rng.randrange(size)
        r = rng.randint(1, spread)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=colour)


def _grass(img: Image.Image, rng: random.Random, size: int, pal) -> None:
    draw = ImageDraw.Draw(img)
    _noise(draw, rng, size, pal[2], count=size // 3)
    for _ in range(size // 2):
        x, y = rng.randrange(size), rng.randrange(size)
        h = rng.randint(2, 5)
        draw.line((x, y, x + rng.randint(-1, 1), y - h), fill=pal[1], width=1)


def _forest(img: Image.Image, rng: random.Random, size: int, pal) -> None:
    draw = ImageDraw.Draw(img)
    _noise(draw, rng, size, pal[2], count=size // 4)
    for _ in range(rng.randint(3, 5)):
        cx = rng.randrange(6, size - 6)
        cy = rng.randrange(6, size - 4)
        r = rng.randint(size // 8, size // 5)
        draw.rectangle((cx - 1, cy, cx + 1, cy + r), fill=(58, 44, 32))
        draw.ellipse((cx - r, cy - r, cx + r, cy + r // 2), fill=pal[2])
        draw.ellipse((cx - r + 2, cy - r + 1, cx + r - 3, cy + r // 2 - 3),
                     fill=pal[1])


def _water(img: Image.Image, rng: random.Random, size: int, pal,
           phase: float = 0.0) -> None:
    draw = ImageDraw.Draw(img)
    for y in range(size):
        wave = math.sin((y / size) * math.tau * 2 + phase * math.tau)
        shade = int(14 * wave)
        base = pal[0]
        draw.line((0, y, size, y),
                  fill=tuple(max(0, min(255, c + shade)) for c in base))
    for _ in range(3):
        y = rng.randrange(size)
        x = (rng.randrange(size) + int(phase * size)) % size
        draw.line((x, y, x + rng.randint(4, 9), y), fill=pal[1], width=1)


def _marsh(img: Image.Image, rng: random.Random, size: int, pal) -> None:
    draw = ImageDraw.Draw(img)
    _noise(draw, rng, size, pal[2], count=size // 3, spread=3)
    for _ in range(rng.randint(2, 4)):
        x, y = rng.randrange(size), rng.randrange(size)
        w, h = rng.randint(5, 11), rng.randint(3, 6)
        draw.ellipse((x, y, x + w, y + h), fill=(74, 96, 96))
    for _ in range(rng.randint(5, 9)):
        x, y = rng.randrange(size), rng.randrange(size // 2, size)
        draw.line((x, y, x + rng.randint(-2, 2), y - rng.randint(5, 10)),
                  fill=(138, 140, 96), width=1)


def _hills(img: Image.Image, rng: random.Random, size: int, pal) -> None:
    draw = ImageDraw.Draw(img)
    _noise(draw, rng, size, pal[2], count=size // 4, spread=3)
    for _ in range(rng.randint(2, 4)):
        cx, cy = rng.randrange(4, size - 4), rng.randrange(4, size - 4)
        r = rng.randint(size // 7, size // 4)
        points = []
        for i in range(6):
            angle = math.tau * i / 6
            rr = r * rng.uniform(0.7, 1.15)
            points.append((cx + rr * math.cos(angle), cy + rr * math.sin(angle)))
        draw.polygon(points, fill=pal[2])
        draw.polygon([(x + 1, y - 1) for x, y in points[:4]], fill=pal[1])


def _bare(img: Image.Image, rng: random.Random, size: int, pal) -> None:
    draw = ImageDraw.Draw(img)
    _noise(draw, rng, size, pal[2], count=size)
    _noise(draw, rng, size, pal[1], count=size // 2, spread=1)


_PAINTERS = {
    TerrainType.GRASS: _grass,
    TerrainType.FOREST: _forest,
    TerrainType.MARSH: _marsh,
    TerrainType.HILLS: _hills,
    TerrainType.BARE: _bare,
}


def _terrain_image(kind: TerrainType, variant: int, size: int,
                   phase: float = 0.0) -> Image.Image:
    pal = _PALETTE[kind]
    img = Image.new("RGBA", (size, size), (*pal[0], 255))
    rng = random.Random(hash((kind.value, variant)) & 0xFFFFFFFF)
    if kind is TerrainType.WATER:
        _water(img, rng, size, pal, phase)
    else:
        _PAINTERS[kind](img, rng, size, pal)
    return img


def _figure_image(size: int) -> Image.Image:
    """The character. A small standing figure, not an @ sign."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = size // 2
    cloth = (196, 188, 172)
    skin = (222, 198, 168)
    draw.line((cx, size // 2, cx - size // 6, size - size // 6),
              fill=cloth, width=max(2, size // 12))
    draw.line((cx, size // 2, cx + size // 6, size - size // 6),
              fill=cloth, width=max(2, size // 12))
    draw.line((cx, size // 4, cx, size // 2 + 2),
              fill=cloth, width=max(3, size // 8))
    r = max(2, size // 9)
    draw.ellipse((cx - r, size // 5 - r, cx + r, size // 5 + r), fill=skin)
    return img


def _flame_image(size: int, frame: int, frames: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng = random.Random(frame)
    cx, base = size // 2, size - size // 6
    sway = math.sin(math.tau * frame / frames) * size * 0.06
    draw.ellipse((cx - size // 3, base - size // 8, cx + size // 3, base + 2),
                 fill=(64, 48, 40, 255))
    for scale, colour in ((1.0, (208, 92, 30, 230)),
                          (0.66, (240, 154, 46, 240)),
                          (0.34, (252, 224, 140, 250))):
        h = size * 0.62 * scale
        w = size * 0.26 * scale
        tip = (cx + sway * scale, base - h)
        draw.polygon(
            [(cx - w, base), (cx + w, base), tip,
             (cx + w * rng.uniform(0.2, 0.5), base - h * 0.5),
             (cx - w * rng.uniform(0.2, 0.5), base - h * 0.5)],
            fill=colour,
        )
    return img


def _radial_image(size: int, colour: tuple[int, int, int],
                  falloff: float = 2.0) -> Image.Image:
    """A soft light. Used additively, so the edge must reach true zero."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = img.load()
    centre = (size - 1) / 2.0
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - centre, y - centre) / centre
            if d >= 1.0:
                continue
            strength = (1.0 - d) ** falloff
            pixels[x, y] = (*colour, int(255 * strength))
    return img


def _dot_image(size: int, colour: tuple[int, int, int, int]) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((0, 0, size - 1, size - 1), fill=colour)
    return img


def _scrim_image(colour: tuple[int, int, int], height: int = 256,
                 strength: float = 0.92, solid_at_top: bool = False) -> Image.Image:
    """A vertical wash: solid at one edge, gone at the other.

    Drawn behind the HUD so the interface sits on darkness that fades into the
    world. A flat panel gives the scene a hard horizontal seam; this does not.
    """
    img = Image.new("RGBA", (8, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = (y / (height - 1)) if solid_at_top else 1.0 - (y / (height - 1))
        alpha = int(255 * strength * (t ** 1.7))
        draw.line((0, y, 8, y), fill=(*colour, alpha))
    return img


def _corner_scrim_image(colour: tuple[int, int, int], size: int = 256,
                        strength: float = 0.92) -> Image.Image:
    """A wash that fades on both axes: solid top-left, gone right and below.

    The single-axis version left a hard vertical edge where it stopped, which
    was visible straight across the map. Fading horizontally too means the
    reading surface behind the log has no edge at all.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = img.load()
    # Hold the wash at full strength across the area the text actually
    # occupies, then fade. A gradient that starts falling off immediately
    # leaves the middle of a sentence sitting on bright grass.
    hold_across, hold_down = 0.52, 0.62

    def shaped(t: float, hold: float, power: float) -> float:
        if t >= hold:
            return 1.0
        return (t / hold) ** power

    for y in range(size):
        down = 1.0 - (y / (size - 1))          # 1 at the top row
        v = shaped(down, hold_down, 1.4)
        if v <= 0.0:
            continue
        for x in range(size):
            across = 1.0 - (x / (size - 1))    # 1 at the left column
            alpha = strength * v * shaped(across, hold_across, 1.1)
            if alpha > 0.002:
                pixels[x, y] = (*colour, int(255 * alpha))
    return img


def _vignette_image(size: int = 320, strength: float = 0.55) -> Image.Image:
    """Darkness gathering in the corners. Frames the scene and settles the eye."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = img.load()
    centre = (size - 1) / 2.0
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - centre, y - centre) / centre
            if d <= 0.55:
                continue
            t = min(1.0, (d - 0.55) / 0.45)
            pixels[x, y] = (0, 0, 0, int(255 * strength * t * t))
    return img


@dataclass
class Assets:
    """Loaded once at start-up. Nothing reads a file inside a draw loop."""
    terrain: dict[tuple[TerrainType, int], arcade.Texture] = field(default_factory=dict)
    water_frames: list[arcade.Texture] = field(default_factory=list)
    flame_frames: list[arcade.Texture] = field(default_factory=list)
    figure: arcade.Texture | None = None
    light: arcade.Texture | None = None
    fire_light: arcade.Texture | None = None
    ember: arcade.Texture | None = None
    scrim: arcade.Texture | None = None
    scrim_top: arcade.Texture | None = None
    scrim_corner: arcade.Texture | None = None
    vignette: arcade.Texture | None = None
    sounds: dict[str, object] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)

    def terrain_texture(self, kind: TerrainType, variant: float) -> arcade.Texture:
        index = int(variant * TERRAIN_VARIANTS) % TERRAIN_VARIANTS
        return self.terrain[(kind, index)]


def _load_override(name: str, size: int) -> Image.Image | None:
    """Use a real PNG if the project has one, otherwise draw it ourselves."""
    path = TILE_DIR / f"{name}.png"
    if not path.exists():
        return None
    try:
        return Image.open(path).convert("RGBA").resize((size, size))
    except OSError as exc:
        log.warning("could not read %s (%s); drawing it instead", path, exc)
        return None


def load(tile_size: int = config.TILE_SIZE) -> Assets:
    assets = Assets()

    for kind in TerrainType:
        for variant in range(TERRAIN_VARIANTS):
            override = _load_override(f"{kind.value}_{variant}", tile_size)
            image = override or _terrain_image(kind, variant, tile_size)
            assets.terrain[(kind, variant)] = arcade.Texture(image)

    assets.water_frames = [
        arcade.Texture(_terrain_image(TerrainType.WATER, 0, tile_size,
                                      phase=i / config.WATER_ANIM_FRAMES))
        for i in range(config.WATER_ANIM_FRAMES)
    ]
    assets.flame_frames = [
        arcade.Texture(_flame_image(tile_size, i, config.FIRE_ANIM_FRAMES))
        for i in range(config.FIRE_ANIM_FRAMES)
    ]
    assets.figure = arcade.Texture(_figure_image(tile_size))
    assets.light = arcade.Texture(_radial_image(128, (110, 116, 150), 2.4))
    assets.fire_light = arcade.Texture(_radial_image(160, (255, 168, 74), 1.9))
    assets.ember = arcade.Texture(_dot_image(6, (255, 186, 96, 255)))
    assets.scrim = arcade.Texture(_scrim_image(theme.SCRIM))
    assets.scrim_top = arcade.Texture(
        _scrim_image(theme.SCRIM, solid_at_top=True))
    assets.scrim_corner = arcade.Texture(_corner_scrim_image(theme.SCRIM))
    assets.vignette = arcade.Texture(_vignette_image())

    assets.sounds = _load_sounds(assets)
    return assets


_SOUND_NAMES = ("footstep", "river", "fire", "wind", "transition")


def _load_sounds(assets: Assets) -> dict[str, object]:
    """Sound is optional. A silent game is a working game."""
    sounds: dict[str, object] = {}
    for name in _SOUND_NAMES:
        found = None
        for suffix in (".wav", ".ogg", ".mp3"):
            path = AUDIO_DIR / f"{name}{suffix}"
            if not path.exists():
                continue
            try:
                found = arcade.load_sound(path)
                break
            except Exception as exc:  # arcade raises several unrelated types
                log.warning("could not load sound %s (%s)", path, exc)
        if found is None:
            assets.missing.append(f"audio/{name}")
        else:
            sounds[name] = found
    return sounds
