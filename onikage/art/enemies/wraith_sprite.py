"""Cached pixel-art frames for the cedar-wood wraith."""

from functools import lru_cache

import pygame


_INK = (17, 24, 27)
_BODY = (39, 55, 55)
_BODY_HI = (69, 92, 82)
_BODY_LO = (28, 40, 43)
_MOSS = (105, 117, 83)
_BONE = (166, 173, 145)
_EYE = (234, 105, 62)
_GLOW = (248, 161, 78)


@lru_cache(maxsize=2)
def wraith_frame(frame: int) -> pygame.Surface:
    """Return one of two 48x64 idle frames."""
    frame %= 2
    image = pygame.Surface((24, 32), pygame.SRCALPHA)
    sway = frame

    pygame.draw.polygon(
        image,
        _INK,
        [
            (4, 17), (7, 9), (11, 6), (11, 2), (14, 8), (18, 5),
            (20, 12), (23, 18), (21, 26), (17, 29), (14, 27 + sway),
            (11, 31 - sway), (7, 28), (3, 29), (5, 23),
        ],
    )
    pygame.draw.polygon(
        image,
        _BODY,
        [
            (6, 17), (8, 11), (12, 8), (13, 11), (17, 8), (19, 14),
            (21, 19), (19, 24), (16, 27 + sway), (13, 25 + sway),
            (10, 29 - sway), (7, 26), (5, 27), (7, 22),
        ],
    )
    pygame.draw.polygon(
        image,
        _BODY_HI,
        [(8, 16), (10, 11), (13, 10), (15, 13), (12, 17), (10, 22), (7, 23)],
    )
    pygame.draw.polygon(
        image,
        _BODY_LO,
        [(14, 15), (18, 12), (20, 18), (19, 23), (16, 26), (14, 23)],
    )
    pygame.draw.polygon(image, _MOSS, [(8, 7), (6, 1), (12, 6), (11, 9)])
    pygame.draw.polygon(image, _MOSS, [(16, 8), (21, 2), (19, 12)])
    pygame.draw.rect(image, _INK, (8, 14, 9, 7))
    pygame.draw.rect(image, _BONE, (9, 15, 7, 4))
    pygame.draw.rect(image, _INK, (10, 16, 2, 2))
    pygame.draw.rect(image, _INK, (14, 16, 2, 2))
    pygame.draw.rect(image, _EYE, (10, 16, 1, 1))
    pygame.draw.rect(image, _GLOW, (14, 16, 1, 1))
    pygame.draw.line(image, _BODY_HI, (8, 24), (6, 27), 1)
    pygame.draw.line(image, _BODY_HI, (18, 23), (20, 26), 1)
    return pygame.transform.scale(image, (48, 64))


@lru_cache(maxsize=2)
def battle_wraith_frame(frame: int) -> pygame.Surface:
    """Return a crisp 144x192 battle sprite."""
    return pygame.transform.scale(wraith_frame(frame), (144, 192))
