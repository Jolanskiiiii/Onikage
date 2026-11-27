"""Reusable frame, portrait, and item-icon surfaces for the game UI."""

from functools import lru_cache

import pygame


def draw_frame(
    surface: pygame.Surface,
    rect: pygame.Rect,
    fill: tuple[int, int, int] = (18, 19, 23),
    border: tuple[int, int, int] = (164, 125, 75),
) -> None:
    pygame.draw.rect(surface, (7, 9, 12), rect.move(0, 5))
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, (52, 45, 39), rect, 4)
    pygame.draw.rect(surface, border, rect, 2)
    pygame.draw.rect(surface, (98, 79, 58), rect.inflate(-8, -8), 1)
    for x, y, flip_x, flip_y in (
        (rect.left + 5, rect.top + 5, False, False),
        (rect.right - 6, rect.top + 5, True, False),
        (rect.left + 5, rect.bottom - 6, False, True),
        (rect.right - 6, rect.bottom - 6, True, True),
    ):
        line_x = x - 7 if flip_x else x
        line_y = y - 7 if flip_y else y
        pygame.draw.rect(surface, (216, 177, 108), (line_x, y, 8, 2))
        pygame.draw.rect(surface, (216, 177, 108), (x, line_y, 2, 8))


@lru_cache(maxsize=1)
def hana_portrait() -> pygame.Surface:
    portrait = pygame.Surface((32, 32), pygame.SRCALPHA)
    portrait.fill((46, 42, 39))
    pygame.draw.rect(portrait, (124, 92, 61), (2, 2, 28, 28))
    pygame.draw.rect(portrait, (69, 88, 82), (4, 4, 24, 24))
    pygame.draw.rect(portrait, (39, 32, 31), (8, 5, 16, 13))
    pygame.draw.rect(portrait, (25, 24, 28), (7, 6, 18, 11))
    pygame.draw.rect(portrait, (189, 145, 107), (10, 10, 12, 10))
    pygame.draw.rect(portrait, (204, 163, 119), (11, 10, 10, 8))
    pygame.draw.rect(portrait, (25, 23, 25), (10, 8, 12, 3))
    pygame.draw.rect(portrait, (184, 51, 52), (9, 7, 14, 2))
    pygame.draw.rect(portrait, (30, 27, 30), (13, 14, 2, 1))
    pygame.draw.rect(portrait, (30, 27, 30), (18, 14, 2, 1))
    pygame.draw.rect(portrait, (108, 48, 50), (7, 20, 18, 10))
    pygame.draw.polygon(portrait, (158, 66, 59), [(7, 21), (16, 18), (25, 21), (23, 29), (9, 29)])
    pygame.draw.line(portrait, (213, 173, 104), (16, 20), (16, 29), 1)
    pygame.draw.rect(portrait, (222, 182, 111), (23, 20, 2, 2))
    return pygame.transform.scale(portrait, (64, 64))


@lru_cache(maxsize=4)
def item_icon(kind: str) -> pygame.Surface:
    icon = pygame.Surface((48, 48), pygame.SRCALPHA)
    pygame.draw.rect(icon, (22, 23, 27), (1, 1, 46, 46))
    pygame.draw.rect(icon, (118, 91, 60), (2, 2, 44, 44), 1)

    if kind == "katana":
        pygame.draw.line(icon, (36, 35, 38), (11, 38), (36, 8), 6)
        pygame.draw.line(icon, (179, 197, 194), (13, 36), (36, 8), 3)
        pygame.draw.line(icon, (230, 229, 208), (14, 34), (34, 9), 1)
        pygame.draw.line(icon, (151, 46, 46), (8, 40), (15, 33), 4)
        pygame.draw.line(icon, (218, 179, 105), (12, 32), (18, 36), 2)
    elif kind == "ration":
        pygame.draw.rect(icon, (87, 60, 42), (10, 11, 28, 30))
        pygame.draw.rect(icon, (152, 105, 63), (12, 14, 24, 25))
        pygame.draw.rect(icon, (190, 145, 83), (14, 12, 20, 4))
        pygame.draw.rect(icon, (122, 53, 46), (19, 20, 10, 10))
        pygame.draw.rect(icon, (220, 187, 120), (22, 22, 4, 6))
        pygame.draw.rect(icon, (225, 203, 148), (17, 33, 14, 2))
    elif kind == "mask":
        pygame.draw.polygon(icon, (30, 36, 42), [(8, 13), (15, 7), (33, 7), (40, 14), (36, 36), (24, 43), (12, 36)])
        pygame.draw.polygon(icon, (124, 54, 48), [(12, 15), (17, 10), (31, 10), (36, 15), (33, 33), (24, 39), (15, 33)])
        pygame.draw.polygon(icon, (28, 29, 34), [(14, 20), (20, 18), (22, 24), (18, 27)])
        pygame.draw.polygon(icon, (28, 29, 34), [(26, 24), (28, 18), (34, 20), (30, 27)])
        pygame.draw.polygon(icon, (203, 166, 106), [(8, 13), (13, 8), (15, 15)])
        pygame.draw.polygon(icon, (203, 166, 106), [(33, 15), (37, 8), (40, 14)])
    else:
        pygame.draw.polygon(icon, (48, 37, 35), [(6, 15), (24, 8), (42, 15), (38, 20), (10, 20)])
        pygame.draw.rect(icon, (128, 45, 45), (11, 20, 5, 23))
        pygame.draw.rect(icon, (128, 45, 45), (32, 20, 5, 23))
        pygame.draw.rect(icon, (170, 61, 52), (7, 18, 34, 4))
        pygame.draw.line(icon, (215, 136, 90), (13, 23), (13, 39), 1)
        pygame.draw.line(icon, (215, 136, 90), (34, 23), (34, 39), 1)
    return icon
