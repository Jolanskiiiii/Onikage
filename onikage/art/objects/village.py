"""Lantern, shrine, and barrel pixel art with cached warm light."""

import math
from functools import lru_cache

import pygame


def draw_village_object(
    surface: pygame.Surface,
    x: int,
    y: int,
    kind: str,
    camera: pygame.Vector2,
) -> None:
    sx, sy = x - round(camera.x), y - round(camera.y)
    if kind == "lantern":
        pygame.draw.ellipse(surface, (18, 22, 19), (sx - 3, sy + 24, 26, 7))
        pygame.draw.rect(surface, (52, 36, 30), (sx + 8, sy + 8, 5, 22))
        pygame.draw.rect(surface, (95, 55, 40), (sx + 5, sy + 18, 11, 3))
        pygame.draw.rect(surface, (126, 62, 47), (sx + 1, sy + 1, 19, 15))
        pygame.draw.rect(surface, (45, 37, 35), (sx + 3, sy + 3, 15, 11))
        pygame.draw.rect(surface, (208, 124, 65), (sx + 5, sy + 4, 11, 9))
        pygame.draw.rect(surface, (238, 167, 87), (sx + 7, sy + 5, 7, 7))
        pygame.draw.rect(surface, (247, 204, 119), (sx + 9, sy + 6, 3, 5))
        pygame.draw.line(surface, (143, 75, 48), (sx + 7, sy + 3), (sx + 7, sy + 14), 1)
        pygame.draw.line(surface, (143, 75, 48), (sx + 14, sy + 3), (sx + 14, sy + 14), 1)
        pygame.draw.rect(surface, (55, 40, 35), (sx + 3, sy, 15, 2))
        pygame.draw.rect(surface, (55, 40, 35), (sx + 4, sy + 16, 13, 2))
        pygame.draw.rect(surface, (178, 125, 68), (sx + 9, sy + 30, 3, 3))
    elif kind == "shrine":
        pygame.draw.ellipse(surface, (14, 20, 19), (sx - 4, sy + 32, 52, 13))
        pygame.draw.rect(surface, (78, 34, 39), (sx + 4, sy + 12, 8, 25))
        pygame.draw.rect(surface, (78, 34, 39), (sx + 30, sy + 12, 8, 25))
        pygame.draw.rect(surface, (156, 50, 47), (sx + 6, sy + 14, 4, 20))
        pygame.draw.rect(surface, (156, 50, 47), (sx + 32, sy + 14, 4, 20))
        pygame.draw.rect(surface, (103, 43, 42), (sx, sy + 8, 42, 6))
        pygame.draw.rect(surface, (159, 53, 49), (sx - 4, sy + 3, 50, 6))
        pygame.draw.line(surface, (208, 111, 74), (sx + 1, sy + 4), (sx + 41, sy + 4), 1)
        pygame.draw.polygon(surface, (45, 39, 39), [(sx - 7, sy + 3), (sx + 21, sy - 5), (sx + 49, sy + 3)])
        pygame.draw.rect(surface, (65, 43, 39), (sx + 17, sy + 18, 8, 15))
        pygame.draw.rect(surface, (192, 149, 83), (sx + 18, sy + 19, 6, 12))
        pygame.draw.line(surface, (225, 194, 131), (sx + 20, sy + 20), (sx + 20, sy + 30), 1)
        pygame.draw.rect(surface, (111, 92, 69), (sx - 5, sy + 36, 52, 4))
        pygame.draw.rect(surface, (71, 66, 54), (sx - 8, sy + 40, 58, 4))
    elif kind == "barrel":
        pygame.draw.ellipse(surface, (15, 19, 18), (sx - 3, sy + 23, 31, 7))
        pygame.draw.rect(surface, (63, 42, 34), (sx + 2, sy + 9, 20, 18))
        pygame.draw.rect(surface, (116, 73, 46), (sx + 1, sy + 8, 21, 17))
        pygame.draw.rect(surface, (144, 96, 58), (sx + 3, sy + 10, 17, 2))
        pygame.draw.rect(surface, (75, 50, 37), (sx - 2, sy + 5, 27, 6))
        pygame.draw.rect(surface, (152, 108, 66), (sx - 1, sy + 5, 24, 2))
        pygame.draw.line(surface, (79, 51, 38), (sx + 8, sy + 11), (sx + 8, sy + 25), 1)
        pygame.draw.line(surface, (79, 51, 38), (sx + 15, sy + 11), (sx + 15, sy + 25), 1)
        pygame.draw.rect(surface, (169, 125, 74), (sx + 10, sy + 14, 3, 5))
    else:
        raise ValueError(f"Unknown village object kind: {kind}")


def draw_lantern_lighting(
    surface: pygame.Surface,
    camera: pygame.Vector2,
    decorations: list[tuple[int, int, str]],
    elapsed: float,
) -> None:
    for x, y, kind in decorations:
        if kind != "lantern":
            continue
        screen_x = x - round(camera.x)
        screen_y = y - round(camera.y)
        if -100 < screen_x < surface.get_width() + 100 and -100 < screen_y < surface.get_height() + 100:
            phase = int((elapsed * 4 + x * 0.1) % 4)
            surface.blit(_lantern_glow(phase), (screen_x - 62, screen_y - 57))


@lru_cache(maxsize=4)
def _lantern_glow(phase: int) -> pygame.Surface:
    glow = pygame.Surface((128, 128), pygame.SRCALPHA)
    center = 64
    strength = 92 + phase * 3
    for y in range(128):
        for x in range(128):
            distance = math.hypot(x - center, y - center)
            if distance < 63:
                alpha = int(strength * (1 - distance / 63) ** 2)
                if alpha:
                    glow.set_at((x, y), (246, 145, 68, alpha))
    return glow
