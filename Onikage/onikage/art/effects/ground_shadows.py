"""Reusable, cached pixel-art contact shadows for village scenery."""

import math
from functools import lru_cache

import pygame


@lru_cache(maxsize=96)
def _ground_shadow_surface(width: int, height: int, opacity: int) -> pygame.Surface:
    """Build a softly feathered, pixel-stepped elliptical shadow once."""
    width = max(3, int(width))
    height = max(3, int(height))
    opacity = max(0, min(160, int(opacity)))
    shadow = pygame.Surface((width, height), pygame.SRCALPHA)

    center_x = (width - 1) / 2
    center_y = (height - 1) / 2
    radius_x = max(1.0, width / 2 - 1)
    radius_y = max(1.0, height / 2 - 1)

    for py in range(height):
        for px in range(width):
            distance = math.sqrt(
                ((px - center_x) / radius_x) ** 2
                + ((py - center_y) / radius_y) ** 2
            )
            if distance >= 1.0:
                continue

            # A broad soft body with a restrained, darker contact core.
            falloff = 1.0 - distance
            alpha = int(opacity * falloff * (0.72 + 0.28 * falloff))
            if alpha:
                shadow.set_at((px, py), (12, 16, 15, alpha))

    return shadow


def draw_ground_shadow(
    surface: pygame.Surface,
    rect: tuple[int, int, int, int],
    opacity: int = 88,
) -> None:
    """Blit a cached feathered shadow at a screen-space ground footprint."""
    x, y, width, height = (int(value) for value in rect)
    if width < 3 or height < 3 or opacity <= 0:
        return
    surface.blit(_ground_shadow_surface(width, height, opacity), (x, y))
