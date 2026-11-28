"""Cached directional animation frames for the spectral Wraith."""

from functools import lru_cache
from pathlib import Path

import pygame


SHEET_PATH = Path(__file__).with_name("wraith_sheet.png")
DIRECTIONS = ("down", "left", "up", "right")
ANIMATIONS = ("idle", "walk", "attack", "hurt", "death")
CELL_SIZE = 96
SPRITE_SIZE = (72, 80)


@lru_cache(maxsize=1)
def _sheet() -> pygame.Surface:
    """Load the transparent 4-direction x 5-animation atlas once."""
    return pygame.image.load(str(SHEET_PATH))


@lru_cache(maxsize=80)
def wraith_animation_frame(
    animation: str,
    direction: str,
    frame: int,
) -> pygame.Surface:
    """Return a 72x80 frame; atlas rows are idle, walk, attack, hurt, death."""
    animation = animation if animation in ANIMATIONS else "idle"
    direction = direction if direction in DIRECTIONS else "down"
    row = ANIMATIONS.index(animation)
    column = DIRECTIONS.index(direction)
    frame = max(0, min(3, int(frame)))
    rect = pygame.Rect(column * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    source = _sheet().subsurface(rect)
    return pygame.transform.scale(source, SPRITE_SIZE)


@lru_cache(maxsize=4)
def wraith_frame(frame: int) -> pygame.Surface:
    """Backward-compatible idle frame accessor."""
    return wraith_animation_frame("idle", "down", frame % 4)


@lru_cache(maxsize=4)
def battle_wraith_frame(frame: int) -> pygame.Surface:
    """Return a crisp enlarged idle frame for battle previews."""
    return pygame.transform.scale(wraith_frame(frame), (144, 160))
