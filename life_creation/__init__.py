"""Life Creation - a survival game that asks how you will live your life.

Layering, strictly one direction:

    life_creation.presentation   graphics, input, sound      (imports arcade)
        v
    life_creation.application    controller, input lock      (no framework)
        v
    life_creation.game           the simulation and rules    (no framework)

Nothing below the presentation package may import a graphics framework, and
nothing in the simulation may draw or print. There is a test for both.
"""

__version__ = "0.2.0"
