"""Licensed pixel-art props used by the starting village."""

from collections import deque
from functools import lru_cache
from pathlib import Path

import pygame

from onikage.art.asset_pipeline import load_image


_PROP_DIRECTORY = (
    Path(__file__).resolve().parents[2]
    / "assets"
    / "artpacks"
    / "feudal_japan"
    / "props"
)
_PROP_FILES = {
    "torii": "01_torii_gate_32x32.png",
    "stone_lantern": "02_stone_lantern_32x32.png",
    "bamboo": "03_bamboo_cluster_32x32.png",
    "barrel": "04_sake_barrel_32x32.png",
    "katana_stand": "05_katana_stand_32x32.png",
    "paper_lantern": "06_paper_lantern_32x32.png",
    "fence": "07_wooden_fence_32x32.png",
    "offering_box": "08_offering_box_32x32.png",
}
_BACKGROUND_COLORS = {
    "torii": {(58, 53, 48)},
    "stone_lantern": {(42, 56, 34)},
    "bamboo": {(42, 62, 26), (30, 48, 20)},
    "barrel": {(48, 40, 32)},
    "katana_stand": {(42, 32, 24), (32, 24, 16)},
    "paper_lantern": {(10, 10, 24)},
    "fence": {(30, 50, 20), (36, 58, 24)},
    "offering_box": {(58, 48, 40), (72, 64, 56), (90, 82, 72)},
}


def _remove_border_background(
    image: pygame.Surface,
    background_colors: set[tuple[int, int, int]],
) -> pygame.Surface:
    """Make only border-connected pixels of known background colors transparent."""
    result = image.copy()
    width, height = result.get_size()
    visited = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        for y in (0, height - 1):
            if result.get_at((x, y))[:3] in background_colors:
                queue.append((x, y))
    for y in range(height):
        for x in (0, width - 1):
            if result.get_at((x, y))[:3] in background_colors:
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        index = y * width + x
        if visited[index]:
            continue
        pixel = result.get_at((x, y))
        if pixel[:3] not in background_colors:
            continue
        visited[index] = 1
        result.set_at((x, y), (*pixel[:3], 0))
        for neighbor_x, neighbor_y in (
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
        ):
            if (
                0 <= neighbor_x < width
                and 0 <= neighbor_y < height
                and not visited[neighbor_y * width + neighbor_x]
            ):
                queue.append((neighbor_x, neighbor_y))
    return result


@lru_cache(maxsize=8)
def _prop_image(kind: str) -> pygame.Surface:
    try:
        filename = _PROP_FILES[kind]
    except KeyError as error:
        raise ValueError(f"Unknown village prop: {kind}") from error
    source = load_image(_PROP_DIRECTORY / filename)
    return _remove_border_background(source, _BACKGROUND_COLORS[kind])


@lru_cache(maxsize=3)
def _sakura_image(variant: int) -> pygame.Surface:
    if not 0 <= variant < 3:
        raise ValueError(f"Unknown sakura variation: {variant}")
    image = pygame.Surface((80, 96), pygame.SRCALPHA)
    pygame.draw.ellipse(image, (8, 15, 17, 125), (8, 76, 64, 15))

    trunk = ((65, 43, 37), (58, 42, 42), (72, 48, 39))[variant]
    bark = ((119, 76, 55), (105, 72, 60), (133, 86, 59))[variant]
    pygame.draw.polygon(image, trunk, ((35, 86), (40, 35), (45, 35), (49, 86)))
    pygame.draw.line(image, bark, (40, 80), (43, 40), 2)
    branches = (
        ((42, 55), (27, 38), (20, 29)),
        ((44, 49), (56, 32), (63, 24)),
        ((41, 63), (28, 54), (17, 51)),
        ((45, 60), (57, 48), (68, 42)),
        ((42, 44), (38, 29), (37, 22)),
    )
    for start, middle, end in branches:
        pygame.draw.line(image, trunk, start, middle, 4)
        pygame.draw.line(image, bark, middle, end, 2)

    blossom_colors = (
        ((86, 47, 66), (133, 69, 87), (178, 101, 116), (212, 151, 155)),
        ((75, 43, 60), (119, 64, 82), (164, 92, 111), (201, 140, 153)),
        ((92, 49, 61), (141, 72, 84), (185, 108, 116), (220, 159, 158)),
    )[variant]
    clusters = (
        (22, 28, 13, 10),
        (39, 20, 14, 11),
        (58, 26, 13, 11),
        (18, 43, 12, 10),
        (36, 39, 16, 13),
        (61, 43, 12, 10),
        (27, 54, 13, 9),
        (50, 55, 14, 10),
    )
    for cluster_index, (x, y, width, height) in enumerate(clusters):
        shadow = blossom_colors[0]
        mid = blossom_colors[1 + (cluster_index + variant) % 2]
        pygame.draw.ellipse(image, (*shadow, 255), (x - 3, y + 2, width, height - 2))
        for offset_x, offset_y, petal_width, petal_height in (
            (0, 3, 7, 5),
            (5, 0, 7, 6),
            (10, 4, 6, 5),
            (4, 6, 8, 5),
            (7, 2, 4, 3),
        ):
            color = mid if (offset_x + offset_y + cluster_index) % 3 else blossom_colors[2]
            pygame.draw.rect(
                image,
                (*color, 255),
                (x + offset_x, y + offset_y, petal_width, petal_height),
            )
        image.set_at((x + 8, y + 3), (*blossom_colors[3], 255))

    for x, y in ((23, 36), (59, 34), (31, 51), (51, 47), (41, 26)):
        image.set_at((x, y), (232, 186, 174, 255))
    return image


@lru_cache(maxsize=1)
def _bamboo_grove_image() -> pygame.Surface:
    image = pygame.Surface((80, 88), pygame.SRCALPHA)
    pygame.draw.ellipse(image, (8, 15, 17, 120), (7, 74, 67, 12))
    stalks = (
        (18, 16, 66),
        (28, 6, 73),
        (39, 18, 68),
        (50, 9, 75),
        (61, 21, 65),
    )
    for index, (x, top, bottom) in enumerate(stalks):
        stalk = (34, 67, 48) if index % 2 else (44, 82, 54)
        highlight = (87, 112, 62)
        pygame.draw.rect(image, (14, 34, 31), (x - 2, top, 6, bottom - top))
        pygame.draw.rect(image, stalk, (x, top, 3, bottom - top))
        pygame.draw.line(image, highlight, (x, top + 2), (x, bottom - 2), 1)
        for band_y in range(top + 13, bottom - 3, 14):
            pygame.draw.line(image, (19, 40, 35), (x - 1, band_y), (x + 4, band_y), 2)
        for leaf_y, direction in (
            (top + 7, -1 if index % 2 else 1),
            (top + 17, 1 if index % 2 else -1),
        ):
            end_x = x + direction * 13
            pygame.draw.line(image, (24, 53, 38), (x + 1, leaf_y), (end_x, leaf_y - 7), 2)
            pygame.draw.polygon(
                image,
                (52, 83, 47),
                (
                    (end_x, leaf_y - 7),
                    (end_x - direction * 9, leaf_y - 7),
                    (end_x - direction * 3, leaf_y - 3),
                ),
            )
    return image


@lru_cache(maxsize=1)
def _bridge_image() -> pygame.Surface:
    image = pygame.Surface((80, 112), pygame.SRCALPHA)
    pygame.draw.ellipse(image, (5, 14, 18, 150), (5, 8, 70, 99))
    pygame.draw.polygon(
        image,
        (35, 32, 30),
        ((12, 3), (68, 3), (76, 108), (4, 108)),
    )
    pygame.draw.polygon(
        image,
        (99, 65, 43),
        ((17, 6), (63, 6), (69, 104), (11, 104)),
    )
    pygame.draw.polygon(
        image,
        (139, 94, 58),
        ((21, 9), (58, 9), (63, 100), (17, 100)),
    )
    for y in range(13, 99, 8):
        left = 20 + (y - 9) // 20
        right = 59 - (y - 9) // 20
        pygame.draw.line(image, (77, 51, 38), (left, y), (right, y), 2)
        pygame.draw.line(image, (171, 120, 74), (left + 2, y + 2), (right - 2, y + 2), 1)
        for x in (left + 3, right - 4):
            image.set_at((x, y), (55, 42, 35, 255))

    for rail_x in (11, 64):
        pygame.draw.line(image, (37, 32, 31), (rail_x, 6), (rail_x + (2 if rail_x == 11 else -2), 104), 4)
        pygame.draw.line(image, (105, 70, 47), (rail_x, 7), (rail_x + (2 if rail_x == 11 else -2), 104), 2)
        for post_y in range(10, 104, 20):
            post_x = rail_x + ((post_y - 6) // 49 if rail_x == 11 else -((post_y - 6) // 49))
            pygame.draw.rect(image, (45, 34, 30), (post_x - 2, post_y - 2, 6, 7))
            pygame.draw.rect(image, (151, 103, 62), (post_x - 1, post_y - 2, 3, 4))
    return image


def _draw_prop(
    surface: pygame.Surface,
    kind: str,
    x: int,
    y: int,
) -> None:
    surface.blit(_prop_image(kind), (x, y))


def draw_village_object(
    surface: pygame.Surface,
    x: int,
    y: int,
    kind: str,
    camera: pygame.Vector2,
) -> None:
    sx, sy = x - round(camera.x), y - round(camera.y)
    if kind == "shrine":
        _draw_prop(surface, "torii", sx - 8, sy - 2)
        _draw_prop(surface, "stone_lantern", sx - 40, sy + 15)
        _draw_prop(surface, "offering_box", sx + 10, sy + 22)
        return
    if kind == "barrel":
        _draw_prop(surface, kind, sx - 2, sy + 5)
        return
    if kind == "bamboo_grove":
        surface.blit(_bamboo_grove_image(), (sx - 24, sy - 76))
        return
    if kind == "sakura":
        variant = (x + y) % 3
        surface.blit(_sakura_image(variant), (sx - 40, sy - 92))
        return
    if kind == "bridge":
        surface.blit(_bridge_image(), (sx - 40, sy - 104))
        return
    _draw_prop(surface, kind, sx, sy)
