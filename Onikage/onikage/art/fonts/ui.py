"""Bundled Japanese pixel font configuration for the game interface."""

from functools import lru_cache
from pathlib import Path

import pygame


def create_ui_fonts() -> tuple[pygame.font.Font, pygame.font.Font, pygame.font.Font]:
    font_path = (
        Path(__file__).resolve().parents[2]
        / "assets"
        / "fonts"
        / "DotGothic16-Regular.ttf"
    )
    title = pygame.font.Font(str(font_path), 36)
    title.set_bold(True)
    body = pygame.font.Font(str(font_path), 18)
    small = pygame.font.Font(str(font_path), 14)
    return title, body, small


@lru_cache(maxsize=16)
def load_pixel_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Return a shared DotGothic16 font. Multiples of 16 keep the pixels crisp."""
    font_path = (
        Path(__file__).resolve().parents[2]
        / "assets"
        / "fonts"
        / "DotGothic16-Regular.ttf"
    )
    font = pygame.font.Font(str(font_path), size)
    if bold:
        font.set_bold(True)
    return font
