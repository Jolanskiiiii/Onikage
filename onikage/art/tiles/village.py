"""Cached hand-built ground and naturally broken village-road tiles."""

import random
from functools import lru_cache

import pygame


ROAD_VARIANTS = 8
_GRASS_DARK = (19, 32, 30)


def _make_grass_tile(tile_size: int, variant: int) -> pygame.Surface:
    rng = random.Random(810 + variant * 17)
    tile = pygame.Surface((tile_size, tile_size))
    base = (
        _GRASS_DARK[0] + variant % 3,
        _GRASS_DARK[1] + variant % 4,
        _GRASS_DARK[2] + variant % 3,
    )
    tile.fill(base)

    for _ in range(34):
        x, y = rng.randrange(tile_size), rng.randrange(tile_size)
        patch_width = rng.choice((1, 1, 2, 3))
        patch_height = rng.choice((1, 1, 2))
        shade = rng.choice(
            (
                (14, 25, 25),
                (22, 38, 34),
                (32, 48, 39),
                (36, 47, 39),
            )
        )
        pygame.draw.rect(tile, shade, (x, y, patch_width, patch_height))

    for _ in range(4):
        x = rng.randrange(3, tile_size - 3)
        y = rng.randrange(3, tile_size - 5)
        pygame.draw.line(tile, (43, 61, 43), (x, y + 3), (x + 1, y), 1)
        tile.set_at((x + 2, y + 2), (69, 75, 47))

    if variant in (2, 7, 11):
        for offset in range(3):
            tile.set_at((7 + offset, 21), (83, 45, 54))
        tile.set_at((9, 20), (104, 57, 61))
    if variant in (4, 9):
        pygame.draw.ellipse(tile, (17, 26, 26), (18, 19, 8, 4))
        tile.set_at((20, 20), (39, 51, 41))
    return tile


def _edge_points(
    tile_size: int,
    connections: int,
    rng: random.Random,
) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    edge_span = max(4, tile_size // 5)

    top = 0 if connections & 1 else rng.randrange(2, 7)
    right = tile_size - 1 if connections & 2 else tile_size - 1 - rng.randrange(2, 7)
    bottom = tile_size - 1 if connections & 4 else tile_size - 1 - rng.randrange(2, 7)
    left = 0 if connections & 8 else rng.randrange(2, 7)

    for x in range(0, tile_size, edge_span):
        offset = 0 if connections & 1 else rng.randrange(0, 4)
        points.append((x, min(tile_size - 1, top + offset)))
    points.append((tile_size - 1, top if connections & 1 else top + 2))
    for y in range(0, tile_size, edge_span):
        offset = 0 if connections & 2 else rng.randrange(0, 4)
        points.append((min(tile_size - 1, right - offset), y))
    points.append((right, tile_size - 1))
    for x in range(tile_size - 1, -1, -edge_span):
        offset = 0 if connections & 4 else rng.randrange(0, 4)
        points.append((x, max(0, bottom - offset)))
    points.append((0, bottom))
    for y in range(tile_size - 1, -1, -edge_span):
        offset = 0 if connections & 8 else rng.randrange(0, 4)
        points.append((min(tile_size - 1, left + offset), y))
    return points


def _make_road_tile(
    tile_size: int,
    variant: int,
    connections: int,
) -> pygame.Surface:
    rng = random.Random(4100 + variant * 53 + connections * 107)
    road = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
    edge = _edge_points(tile_size, connections, rng)
    pygame.draw.polygon(road, (68, 53, 43, 255), edge)

    for _ in range(26):
        x, y = rng.randrange(tile_size), rng.randrange(tile_size)
        if road.get_at((x, y)).a == 0:
            continue
        shade = rng.choice(
            (
                (53, 44, 38, 255),
                (61, 48, 40, 255),
                (78, 61, 47, 255),
                (88, 69, 51, 255),
            )
        )
        pygame.draw.rect(
            road,
            shade,
            (x, y, rng.choice((1, 2, 3)), rng.choice((1, 1, 2))),
        )

    for _ in range(3):
        x, y = rng.randrange(2, tile_size - 3), rng.randrange(2, tile_size - 3)
        if road.get_at((x, y)).a:
            pygame.draw.line(road, (111, 84, 59, 255), (x, y), (x + 1, y + 1))
    if connections in (3, 12) and variant % 3 == 0:
        for offset in range(3):
            x = tile_size // 2 + offset
            road.set_at((x, tile_size // 2), (104, 72, 53, 255))
            road.set_at((x + 1, tile_size // 2 + 1), (104, 72, 53, 255))
    return road


@lru_cache(maxsize=4)
def make_village_tiles(
    tile_size: int,
) -> tuple[tuple[pygame.Surface, ...], tuple[pygame.Surface, ...]]:
    if tile_size < 16:
        raise ValueError("Village terrain tiles must be at least 16 pixels.")

    grass_tiles = tuple(
        _make_grass_tile(tile_size, variant) for variant in range(16)
    )
    road_tiles = tuple(
        _make_road_tile(tile_size, variant, connections)
        for connections in range(16)
        for variant in range(ROAD_VARIANTS)
    )
    return grass_tiles, road_tiles


def road_tile_index(connections: int, variant: int) -> int:
    """Map N/E/S/W connection bits and a visual variant to a cached tile."""
    if not 0 <= connections < 16:
        raise ValueError("Road connection mask must be between 0 and 15.")
    if not 0 <= variant < ROAD_VARIANTS:
        raise ValueError(f"Road variant must be between 0 and {ROAD_VARIANTS - 1}.")
    return connections * ROAD_VARIANTS + variant


@lru_cache(maxsize=4)
def make_stream_tiles(tile_size: int) -> tuple[pygame.Surface, ...]:
    if tile_size < 16:
        raise ValueError("Village terrain tiles must be at least 16 pixels.")

    tiles: list[pygame.Surface] = []
    for variant in range(4):
        rng = random.Random(731 + variant * 29)
        tile = pygame.Surface((tile_size, tile_size))
        tile.fill((18, 35, 40))
        for _ in range(20):
            x, y = rng.randrange(tile_size), rng.randrange(tile_size)
            shade = rng.choice(
                ((23, 45, 50), (28, 52, 55), (34, 60, 61), (16, 29, 34))
            )
            pygame.draw.line(
                tile,
                shade,
                (x, y),
                (min(tile_size - 1, x + rng.randrange(2, 8)), y),
                1,
            )
        for x in range(variant % 2, tile_size, 11):
            tile.set_at((x, (x * 3 + variant * 7) % tile_size), (55, 74, 70))
        tiles.append(tile)
    return tuple(tiles)
