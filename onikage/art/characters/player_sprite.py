"""Small, palette-driven pixel-art frames for the wandering samurai."""

from functools import lru_cache

import pygame


_INK = (20, 23, 29)
_HAIR = (25, 24, 29)
_HAIR_HI = (51, 46, 46)
_SKIN = (207, 165, 121)
_SKIN_SHADE = (164, 112, 82)
_RED = (151, 43, 48)
_RED_HI = (207, 77, 62)
_GOLD = (213, 173, 100)
_ARMOR = (37, 46, 58)
_ARMOR_HI = (67, 77, 88)
_ARMOR_LO = (27, 33, 43)
_CLOTH = (119, 43, 47)
_CLOTH_HI = (172, 65, 58)
_TROUSERS = (42, 48, 57)
_BOOT = (25, 27, 30)
_STEEL = (170, 190, 191)
_STEEL_HI = (224, 222, 201)

_FRAME_CACHE: dict[tuple[str, int], pygame.Surface] = {}


def player_frame(direction: str, frame: int) -> pygame.Surface:
    """Return a cached 32x48, nearest-neighbor pixel-art player frame."""
    direction = direction if direction in ("down", "up", "left", "right") else "down"
    key = (direction, frame % 3)
    if key not in _FRAME_CACHE:
        _FRAME_CACHE[key] = _make_frame(*key)
    return _FRAME_CACHE[key]


@lru_cache(maxsize=12)
def battle_player_frame(direction: str, frame: int) -> pygame.Surface:
    """Return a large nearest-neighbor sprite for battle scenes."""
    return pygame.transform.scale(player_frame(direction, frame), (128, 192))


def _make_frame(direction: str, frame: int) -> pygame.Surface:
    image = pygame.Surface((16, 24), pygame.SRCALPHA)
    stride = (0, -1, 1)[frame]

    _draw_sword(image, direction)
    _draw_legs(image, stride)
    _draw_robe(image, frame)
    _draw_head(image, direction)
    if direction == "left":
        image = pygame.transform.flip(image, True, False)
    return pygame.transform.scale(image, (32, 48))


def _draw_sword(image: pygame.Surface, direction: str) -> None:
    if direction == "up":
        pygame.draw.line(image, _INK, (11, 9), (15, 17), 3)
        pygame.draw.line(image, (92, 48, 42), (11, 9), (15, 17), 1)
        pygame.draw.line(image, _STEEL, (13, 12), (15, 16), 1)
        image.set_at((14, 12), _STEEL_HI)
        pygame.draw.line(image, _GOLD, (10, 8), (12, 10), 2)
    elif direction in ("left", "right"):
        pygame.draw.line(image, _INK, (3, 10), (1, 16), 3)
        pygame.draw.line(image, (92, 48, 42), (3, 10), (1, 16), 1)
        pygame.draw.line(image, _STEEL, (2, 13), (1, 15), 1)
        pygame.draw.line(image, _GOLD, (4, 8), (2, 10), 2)
    else:
        pygame.draw.line(image, _INK, (12, 10), (15, 17), 3)
        pygame.draw.line(image, (92, 48, 42), (12, 10), (15, 17), 1)
        pygame.draw.line(image, _STEEL, (14, 12), (15, 16), 1)
        image.set_at((14, 12), _STEEL_HI)
        pygame.draw.line(image, _GOLD, (11, 9), (13, 11), 2)


def _draw_legs(image: pygame.Surface, stride: int) -> None:
    left_shift = stride
    right_shift = -stride
    for x, shift in ((4, left_shift), (9, right_shift)):
        pygame.draw.rect(image, _INK, (x, 16 + shift, 4, 6))
        pygame.draw.rect(image, _TROUSERS, (x + 1, 16 + shift, 2, 5))
        image.set_at((x + 1, 18 + shift), _ARMOR_HI)
        pygame.draw.rect(image, _INK, (x - 1, 21 + shift, 5, 2))
        pygame.draw.rect(image, _BOOT, (x, 21 + shift, 3, 1))
        image.set_at((x + 1, 21 + shift), _ARMOR_HI)


def _draw_robe(image: pygame.Surface, frame: int) -> None:
    pygame.draw.rect(image, _INK, (2, 10, 12, 8))
    pygame.draw.rect(image, _ARMOR, (3, 10, 10, 7))
    pygame.draw.rect(image, _ARMOR_HI, (4, 11, 8, 1))

    pygame.draw.rect(image, _INK, (1, 11, 4, 5))
    pygame.draw.rect(image, _ARMOR, (2, 12, 3, 3))
    pygame.draw.rect(image, _ARMOR_HI, (2, 12, 1, 2))
    pygame.draw.rect(image, _INK, (11, 11, 4, 5))
    pygame.draw.rect(image, _ARMOR, (11, 12, 3, 3))
    pygame.draw.rect(image, _ARMOR_HI, (13, 12, 1, 2))

    pygame.draw.rect(image, _ARMOR_LO, (4, 12, 8, 5))
    pygame.draw.rect(image, _ARMOR_HI, (5, 12, 1, 4))
    pygame.draw.rect(image, _ARMOR, (7, 12, 5, 4))
    for row in (13, 15):
        pygame.draw.line(image, _INK, (7, row), (11, row), 1)
        image.set_at((8, row - 1), _GOLD)
        image.set_at((10, row - 1), _GOLD)

    pygame.draw.line(image, _CLOTH, (5, 10), (8, 14), 2)
    pygame.draw.line(image, _CLOTH_HI, (6, 10), (9, 14), 1)
    pygame.draw.line(image, _GOLD, (8, 11), (8, 14), 1)
    pygame.draw.rect(image, _RED, (4, 16, 8, 2))
    pygame.draw.line(image, _RED_HI, (5, 16), (10, 16), 1)
    image.set_at((10, 17), _GOLD)

    sleeve_y = 14 + (1 if frame == 1 else -1 if frame == 2 else 0)
    pygame.draw.rect(image, _INK, (1, sleeve_y, 3, 3))
    pygame.draw.rect(image, _SKIN, (2, sleeve_y + 1, 2, 2))
    pygame.draw.rect(image, _INK, (12, 14 - (sleeve_y - 14), 3, 3))
    pygame.draw.rect(image, _SKIN, (12, 15 - (sleeve_y - 14), 2, 2))
    image.set_at((3, sleeve_y + 1), _SKIN_SHADE)


def _draw_head(image: pygame.Surface, direction: str) -> None:
    pygame.draw.rect(image, _INK, (4, 2, 8, 9))
    pygame.draw.rect(image, _HAIR, (5, 2, 6, 8))
    pygame.draw.rect(image, _HAIR_HI, (6, 2, 4, 1))
    pygame.draw.rect(image, _INK, (7, 0, 3, 3))
    pygame.draw.rect(image, _HAIR_HI, (8, 1, 2, 1))

    if direction == "up":
        pygame.draw.rect(image, _HAIR, (5, 4, 6, 6))
        pygame.draw.rect(image, _HAIR_HI, (6, 6, 4, 1))
        pygame.draw.rect(image, _RED, (4, 4, 8, 1))
        image.set_at((10, 4), _RED_HI)
        pygame.draw.rect(image, _GOLD, (7, 8, 2, 1))
        return

    pygame.draw.rect(image, _SKIN_SHADE, (5, 5, 6, 5))
    pygame.draw.rect(image, _SKIN, (5, 5, 5, 4))
    pygame.draw.rect(image, _RED, (4, 4, 8, 2))
    pygame.draw.line(image, _RED_HI, (5, 4), (9, 4), 1)
    image.set_at((10, 5), _GOLD)

    if direction in ("left", "right"):
        image.set_at((9, 7), _INK)
        image.set_at((10, 8), _SKIN_SHADE)
        image.set_at((5, 7), _HAIR)
        image.set_at((5, 8), _HAIR)
    else:
        image.set_at((6, 7), _INK)
        image.set_at((9, 7), _INK)
        image.set_at((8, 8), _SKIN_SHADE)

    pygame.draw.rect(image, _HAIR, (4, 6, 1, 3))
    pygame.draw.rect(image, _HAIR, (11, 6, 1, 3))
    image.set_at((6, 6), _HAIR_HI)
