"""Cached top-down Akihiro sprites loaded from the bundled sprite sheet."""

from functools import lru_cache
from pathlib import Path

import pygame


_SHEET_PATH = Path(__file__).with_name("akihiro_sheet.png")
_FRAME_WIDTH = 48
_FRAME_HEIGHT = 64
_DIRECTION_ROWS = {
    "down": 0,
    "up": 1,
    "left": 2,
    "right": 3,
}


@lru_cache(maxsize=1)
def _load_sheet() -> pygame.Surface:
    """Load the transparent 4-direction, 4-frame Akihiro sprite sheet."""
    if not _SHEET_PATH.is_file():
        raise FileNotFoundError(
            f"Akihiro sprite sheet is missing: {_SHEET_PATH}. "
            "Copy akihiro_sheet.png beside player_sprite.py."
        )
    return pygame.image.load(str(_SHEET_PATH))


@lru_cache(maxsize=16)
def player_frame(direction: str, frame: int) -> pygame.Surface:
    """Return one cached 48x64 frame (rows: down, up, left, right)."""
    row = _DIRECTION_ROWS.get(direction, _DIRECTION_ROWS["down"])
    column = frame % 4
    source = _load_sheet()
    rectangle = pygame.Rect(
        column * _FRAME_WIDTH,
        row * _FRAME_HEIGHT,
        _FRAME_WIDTH,
        _FRAME_HEIGHT,
    )
    return source.subsurface(rectangle).copy()


@lru_cache(maxsize=16)
def battle_player_frame(direction: str, frame: int) -> pygame.Surface:
    """Return a larger nearest-neighbor sprite for battle and dialogue scenes."""
    return pygame.transform.scale(player_frame(direction, frame), (128, 192))
