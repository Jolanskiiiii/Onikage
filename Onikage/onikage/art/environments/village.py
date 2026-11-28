"""Layered house and cedar-tree pixel art for the starting village."""

import pygame
from functools import lru_cache
from onikage.art.objects.region_props import sprite

from onikage.art.effects.ground_shadows import draw_ground_shadow


@lru_cache(maxsize=24)
def _scaled_house(name: str, size: tuple[int, int]) -> pygame.Surface:
    return pygame.transform.scale(sprite(name), size)


def draw_village_building(
    surface: pygame.Surface,
    rect: pygame.Rect,
    camera: pygame.Vector2,
) -> None:
    x, y = rect.x - round(camera.x), rect.y - round(camera.y)
    # Smaller footprint and three genuinely different building silhouettes.
    variant = ((rect.x // 160) + (rect.y // 120)) % 3
    names = ("kagehama_house.png", "kagehama_house_b.png", "kagehama_house_c.png")
    # Keep the original ground-contact point so collision and depth sorting remain stable.
    target_w = int((rect.width + 34) * 0.78)
    target_h = int((rect.height + 42) * 0.78)
    rendered = _scaled_house(names[variant], (target_w, target_h))
    surface.blit(rendered, (x + (rect.width-target_w)//2, y + rect.height-target_h+3))


@lru_cache(maxsize=16)
def _scaled_tree(name: str, size: tuple[int, int]) -> pygame.Surface:
    return pygame.transform.scale(sprite(name), size)


def draw_cedar_tree(
    surface: pygame.Surface,
    x: int,
    y: int,
    height: int,
    camera: pygame.Vector2,
) -> None:
    sx, sy = x - round(camera.x), y - round(camera.y)
    # Alternate tiered cedar and broad maple silhouettes. Scaling is cached so
    # the richer trees do not reintroduce the frame-time spikes from Pass 25.
    variant = (x * 3 + y * 7) % 5
    names = (
        "kagehama_tree.png", "kagehama_tree_b.png", "kagehama_maple.png",
        "kagehama_tree.png", "kagehama_maple.png",
    )
    name = names[variant]
    factor = max(0.78, min(1.18, height / 48))
    w, h = int(88 * factor), int(112 * factor)
    tree = _scaled_tree(name, (w, h))
    surface.blit(tree, (sx - w // 2, sy - h + 8))
