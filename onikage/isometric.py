"""Reusable isometric/world coordinate helpers.

World coordinates remain rectangular grid coordinates.  Screen coordinates are
produced only at rendering boundaries, keeping movement, collision, quests,
and interactions independent of the camera and projection.
"""

from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class IsoTransform:
    tile_width: int = 64
    tile_height: int = 32

    def world_to_screen(
        self,
        world_x: float,
        world_y: float,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
    ) -> pygame.Vector2:
        screen_x = (world_x - world_y) * self.tile_width / 2.0
        screen_y = (world_x + world_y) * self.tile_height / 2.0
        return pygame.Vector2(screen_x + origin_x, screen_y + origin_y)

    def screen_to_world(
        self,
        screen_x: float,
        screen_y: float,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
    ) -> pygame.Vector2:
        dx = (screen_x - origin_x) / (self.tile_width / 2.0)
        dy = (screen_y - origin_y) / (self.tile_height / 2.0)
        return pygame.Vector2((dx + dy) / 2.0, (dy - dx) / 2.0)

    @property
    def depth_height(self) -> float:
        """Half-height used when reporting the isometric ground plane."""
        return float(self.tile_height)


def normalized_direction(dx: float, dy: float) -> pygame.Vector2:
    """Normalize a two-axis input so diagonal movement is not faster."""
    movement = pygame.Vector2(dx, dy)
    if movement.length_squared() > 0:
        movement = movement.normalize()
    return movement


def isometric_screen_direction(move_x: float, move_y: float) -> pygame.Vector2:
    """Map screen-style arrows/WASD into normalized isometric world axes."""
    transform = IsoTransform()
    world = transform.screen_to_world(
        move_x * transform.tile_width,
        move_y * transform.tile_height,
    )
    return normalized_direction(world.x, world.y)


def direction_name(dx: float, dy: float) -> str:
    """Convert a movement vector to one of eight isometric directions."""
    if dx == 0.0 and dy == 0.0:
        return "down"
    import math
    degrees = math.degrees(math.atan2(dy, dx)) % 360.0
    names = ("right", "down-right", "down", "down-left",
             "left", "up-left", "up", "up-right")
    sector = int((degrees + 22.5) // 45.0) % 8
    return names[sector]


def interaction_point(
    ground_position: pygame.Vector2,
    direction: str,
    distance: float = 32.0,
) -> pygame.Vector2:
    """Calculate an interaction position on the player's ground plane."""
    offsets = {
        "right": (distance, 0), "down-right": (distance, distance),
        "down": (0, distance), "down-left": (-distance, distance),
        "left": (-distance, 0), "up-left": (-distance, -distance),
        "up": (0, -distance), "up-right": (distance, -distance),
    }
    dx, dy = offsets.get(direction, (0, distance))
    return pygame.Vector2(ground_position.x + dx, ground_position.y + dy)


def ground_depth(world_x: float, world_y: float) -> float:
    """Stable depth key for isometric ground-plane depth sorting."""
    return world_x + world_y


def sprite_direction(direction: str) -> str:
    """Map an eight-direction isometric direction to an existing four-frame sprite."""
    if direction in ("up", "up-left", "up-right"):
        return "up"
    if direction in ("down", "down-left", "down-right"):
        return "down"
    return direction
