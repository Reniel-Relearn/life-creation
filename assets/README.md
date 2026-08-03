# Assets

The game ships with **no image or sound files**. Everything you see is drawn
procedurally at start-up by `life_creation/presentation/assets.py` using
original code. Nothing here is downloaded, and nothing is copyrighted.

These folders exist so that art and audio can be dropped in later without
touching the renderer.

## Replacing the placeholder art

Put a PNG in `tiles/` named `<terrain>_<variant>.png`, where variant is `0`,
`1` or `2`:

```
tiles/grass_0.png   tiles/forest_0.png   tiles/water_0.png
tiles/grass_1.png   tiles/forest_1.png   tiles/marsh_0.png
tiles/grass_2.png   tiles/hills_0.png    tiles/bare_0.png
```

It is resized to the tile size in `config.py` and used in place of the drawn
version. Any file you do not supply keeps its procedural version, so you can
replace one tile at a time.

## Adding sound

Drop `footstep`, `river`, `fire`, `wind` or `transition` into `audio/` as
`.wav`, `.ogg` or `.mp3`. They are picked up automatically.

Audio is entirely optional. A missing sound file is not an error, and a dead
audio device mutes the game rather than ending the run — there is a test for
the first and a guard for the second.

## Rules

- Nothing copyrighted, ever.
- A missing optional asset must never crash the game.
- All loading happens once at start-up. Nothing reads a file inside a draw loop.
