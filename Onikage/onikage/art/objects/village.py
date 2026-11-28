"""Lantern, shrine, and barrel pixel art with cached warm light."""

import math
from functools import lru_cache

import pygame
from onikage.art.objects.region_props import sprite

from onikage.art.effects.ground_shadows import draw_ground_shadow


def draw_village_object(
    surface: pygame.Surface,
    x: int,
    y: int,
    kind: str,
    camera: pygame.Vector2,
) -> None:
    sx, sy = x - round(camera.x), y - round(camera.y)
    if kind == "lantern":
        surface.blit(sprite("kagehama_lantern.png"), (sx - 9, sy - 18))
        return
    if kind == "lantern_legacy":
        # A compact wooden tōrō-style lantern. All parts share the same
        # origin, and the plinth/shadow meet at the declared ground anchor.
        draw_ground_shadow(surface, (sx - 5, sy + 30, 31, 8), opacity=86)
        pygame.draw.rect(surface, (48, 45, 39), (sx + 3, sy + 27, 17, 7))
        pygame.draw.rect(surface, (111, 99, 78), (sx + 4, sy + 28, 15, 2))
        pygame.draw.line(surface, (157, 139, 108), (sx + 5, sy + 31), (sx + 18, sy + 31), 1)

        # Pedestal and central timber stem.
        pygame.draw.rect(surface, (61, 39, 30), (sx + 9, sy + 17, 6, 12))
        pygame.draw.line(surface, (139, 91, 52), (sx + 10, sy + 18), (sx + 10, sy + 27), 1)
        pygame.draw.rect(surface, (83, 52, 36), (sx + 6, sy + 15, 12, 3))

        # Warm lantern housing and visible timber corner posts.
        pygame.draw.rect(surface, (53, 36, 30), (sx + 3, sy + 3, 18, 14))
        pygame.draw.rect(surface, (135, 75, 43), (sx + 5, sy + 4, 14, 11))
        pygame.draw.rect(surface, (39, 33, 30), (sx + 7, sy + 5, 10, 9))
        pygame.draw.rect(surface, (211, 123, 57), (sx + 8, sy + 6, 8, 7))
        pygame.draw.rect(surface, (246, 177, 88), (sx + 9, sy + 6, 6, 6))
        pygame.draw.rect(surface, (255, 218, 139), (sx + 11, sy + 7, 3, 4))
        pygame.draw.line(surface, (158, 83, 48), (sx + 6, sy + 4), (sx + 6, sy + 15), 1)
        pygame.draw.line(surface, (158, 83, 48), (sx + 18, sy + 4), (sx + 18, sy + 15), 1)
        # Fine joinery details add texture without changing the silhouette.
        pygame.draw.line(surface, (205, 133, 75), (sx + 8, sy + 5), (sx + 16, sy + 5), 1)
        pygame.draw.line(surface, (91, 54, 37), (sx + 8, sy + 14), (sx + 16, sy + 14), 1)
        pygame.draw.rect(surface, (190, 119, 67), (sx + 4, sy + 7, 1, 3))
        pygame.draw.rect(surface, (190, 119, 67), (sx + 19, sy + 7, 1, 3))
        pygame.draw.rect(surface, (38, 31, 28), (sx + 4, sy + 3, 2, 1))
        pygame.draw.rect(surface, (38, 31, 28), (sx + 18, sy + 3, 2, 1))

        # Overhanging roof, ridge cap, and lower housing rail.
        pygame.draw.polygon(
            surface,
            (48, 37, 32),
            [(sx + 1, sy + 4), (sx + 4, sy + 1), (sx + 12, sy - 2),
             (sx + 20, sy + 1), (sx + 23, sy + 4)],
        )
        pygame.draw.line(surface, (153, 104, 65), (sx + 4, sy + 2), (sx + 12, sy - 1), 1)
        pygame.draw.line(surface, (153, 104, 65), (sx + 12, sy - 1), (sx + 20, sy + 2), 1)
        pygame.draw.rect(surface, (61, 39, 31), (sx + 3, sy + 16, 18, 2))
        pygame.draw.line(surface, (170, 103, 59), (sx + 5, sy + 16), (sx + 19, sy + 16), 1)
        pygame.draw.line(surface, (88, 57, 39), (sx + 3, sy + 5), (sx + 1, sy + 5), 1)
        pygame.draw.line(surface, (88, 57, 39), (sx + 21, sy + 5), (sx + 23, sy + 5), 1)
        pygame.draw.rect(surface, (185, 132, 78), (sx + 11, sy - 2, 2, 2))
    elif kind == "shrine":
        # A broad feathered footprint blends into the soil, while the smaller
        # contact core anchors the stone base without making it look outlined.
        draw_ground_shadow(surface, (sx - 8, sy + 34, 60, 13), opacity=58)
        draw_ground_shadow(surface, (sx - 4, sy + 38, 52, 7), opacity=100)
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
        # Keep a soft soil halo, with a slightly stronger narrow contact
        # shadow directly beneath the barrel's lower rim.
        draw_ground_shadow(surface, (sx - 5, sy + 23, 35, 9), opacity=58)
        draw_ground_shadow(surface, (sx - 1, sy + 25, 27, 5), opacity=98)
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
        if -120 < screen_x < surface.get_width() + 120 and -100 < screen_y < surface.get_height() + 100:
            phase = int((elapsed * 4 + x * 0.1) % 4)
            # A broad, low-opacity pool falls onto the road below the flame;
            # a smaller halo remains centered on the flame itself.
            surface.blit(_lantern_ground_glow(phase), _lantern_ground_glow_origin(screen_x, screen_y))
            surface.blit(_lantern_glow(phase), _lantern_glow_origin(screen_x, screen_y))


def _lantern_glow_origin(screen_x: int, screen_y: int) -> tuple[int, int]:
    """Center the small warm halo on the visible flame."""
    return screen_x - 20, screen_y - 23


def _lantern_ground_glow_origin(screen_x: int, screen_y: int) -> tuple[int, int]:
    """Center a broad, subtle pool on the lantern's ground contact."""
    return screen_x - 52, screen_y - 3


@lru_cache(maxsize=4)
def _lantern_glow(phase: int) -> pygame.Surface:
    """Soft flame halo; cached by flicker phase to avoid per-frame raster work."""
    glow = pygame.Surface((64, 64), pygame.SRCALPHA)
    strength = 62 + phase * 3
    center_x = center_y = 32
    radius = 31
    for py in range(64):
        for px in range(64):
            distance = math.hypot(px - center_x, (py - center_y) * 1.08)
            if distance < radius:
                falloff = 1.0 - distance / radius
                alpha = int(strength * falloff * falloff)
                if alpha:
                    glow.set_at((px, py), (255, 166, 91, alpha))
    return glow


@lru_cache(maxsize=4)
def _lantern_ground_glow(phase: int) -> pygame.Surface:
    """Wide elliptical ground illumination with a gentle, non-ringed falloff."""
    glow = pygame.Surface((128, 72), pygame.SRCALPHA)
    strength = 39 + phase * 2
    center_x, center_y = 64, 36
    radius_x, radius_y = 62.0, 33.0
    for py in range(72):
        for px in range(128):
            distance = math.sqrt(
                ((px - center_x) / radius_x) ** 2
                + ((py - center_y) / radius_y) ** 2
            )
            if distance < 1.0:
                falloff = 1.0 - distance
                # A smooth cubic falloff keeps the edge subtle and avoids a hard halo.
                alpha = int(strength * falloff * falloff * (0.75 + 0.25 * falloff))
                if alpha:
                    glow.set_at((px, py), (235, 143, 76, alpha))
    return glow
