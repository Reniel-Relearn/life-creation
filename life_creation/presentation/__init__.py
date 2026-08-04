"""The graphical front end.

This is the only package in the project permitted to import a graphics
framework. Everything it needs from the simulation arrives as a view model or
an outcome; it reaches into the game state to draw the world, and never to
change it.
"""

from .app import LifeCreation, run

__all__ = ["LifeCreation", "run"]
