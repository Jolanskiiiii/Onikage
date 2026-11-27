"""Screen-space direction helpers for ONIKAGE's traditional top-down world."""

from __future__ import annotations

import math

import pygame


DIRECTION_VECTORS: dict[str, pygame.Vector2] = {
    "right": pygame.Vector2(1, 0),
    "down-right": pygame.Vector2(1, 1).normalize(),
    "down": pygame.Vector2(0, 1),
    "down-left": pygame.Vector2(-1, 1).normalize(),
    "left": pygame.Vector2(-1, 0),
    "up-left": pygame.Vector2(-1, -1).normalize(),
    "up": pygame.Vector2(0, -1),
    "up-right": pygame.Vector2(1, -1).normalize(),
}


def normalized_direction(dx: float, dy: float) -> pygame.Vector2:
    """Return a normalized screen-space movement vector."""
    vector = pygame.Vector2(dx, dy)
    if vector.length_squared() > 0:
        vector.normalize_ip()
    return vector


def direction_name(dx: float, dy: float) -> str:
    """Convert a screen-space vector into one of eight facing directions."""
    if dx == 0 and dy == 0:
        return "down"
    degrees = math.degrees(math.atan2(dy, dx)) % 360.0
    names = ("right", "down-right", "down", "down-left", "left", "up-left", "up", "up-right")
    return names[int((degrees + 22.5) // 45.0) % 8]


def interaction_point(
    ground_position: pygame.Vector2,
    direction: str,
    distance: float = 32.0,
) -> pygame.Vector2:
    """Return a point directly ahead of the player in screen coordinates."""
    vector = DIRECTION_VECTORS.get(direction, DIRECTION_VECTORS["down"])
    return ground_position + vector * distance


def sprite_direction(direction: str) -> str:
    """Map eight-way facing to the existing four-way character art."""
    if direction in ("up", "up-left", "up-right"):
        return "up"
    if direction in ("down", "down-left", "down-right"):
        return "down"
    return direction
