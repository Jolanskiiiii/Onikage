"""Deterministic, cached terrain tiles for the starting village."""

import random
from functools import lru_cache

import pygame


@lru_cache(maxsize=4)
def make_village_tiles(
    tile_size: int,
) -> tuple[tuple[pygame.Surface, ...], tuple[pygame.Surface, ...]]:
    grass_tiles: list[pygame.Surface] = []
    path_tiles: list[pygame.Surface] = []
    for variant in range(8):
        rng = random.Random(810 + variant)
        grass = pygame.Surface((tile_size, tile_size))
        grass.fill((28 + variant % 3, 43 + variant % 2, 37 + variant % 3))
        for _ in range(18):
            x = rng.randrange(2, tile_size - 3)
            y = rng.randrange(2, tile_size - 3)
            width = rng.randrange(1, 4)
            shade = rng.choice(((35, 54, 43), (23, 38, 34), (43, 59, 43)))
            pygame.draw.rect(grass, shade, (x, y, width, rng.randrange(1, 3)))
        for _ in range(3):
            x = rng.randrange(3, tile_size - 4)
            y = rng.randrange(3, tile_size - 5)
            pygame.draw.line(grass, (64, 77, 50), (x, y + 3), (x + 1, y), 1)
            grass.set_at((x + 2, y + 2), (76, 80, 52))
        # Tiny moss blooms and scattered leaf pixels break up the repeated ground.
        for _ in range(4):
            x = rng.randrange(3, tile_size - 3)
            y = rng.randrange(3, tile_size - 3)
            accent = rng.choice(((81, 91, 57), (93, 79, 53), (54, 72, 48)))
            grass.set_at((x, y), accent)
            if rng.random() < 0.45:
                grass.set_at((x + 1, y), (accent[0] + 8, accent[1] + 5, accent[2] + 3))
        grass_tiles.append(grass)

        path = pygame.Surface((tile_size, tile_size))
        path.fill((69 + variant % 3, 56 + variant % 3, 49 + variant % 2))
        for _ in range(7):
            x = rng.randrange(1, tile_size - 7)
            y = rng.randrange(1, tile_size - 6)
            width = rng.randrange(3, 8)
            height = rng.randrange(2, 5)
            pygame.draw.rect(path, (82, 67, 55), (x, y + 1, width, height))
            pygame.draw.rect(path, (96, 79, 63), (x, y, width - 1, height - 1))
            pygame.draw.line(path, (111, 90, 69), (x + 1, y), (x + width - 2, y), 1)
            path.set_at((x + width - 1, y + height - 1), (52, 48, 42))
        for _ in range(5):
            x = rng.randrange(2, tile_size - 2)
            y = rng.randrange(2, tile_size - 2)
            pygame.draw.rect(path, (54, 48, 42), (x, y, 2, 1))
        for _ in range(3):
            x = rng.randrange(3, tile_size - 4)
            y = rng.randrange(3, tile_size - 4)
            pygame.draw.rect(path, (119, 97, 75), (x, y, 2, 1))
            path.set_at((x + 1, y + 1), (58, 51, 44))
        path_tiles.append(path)

    return tuple(grass_tiles), tuple(path_tiles)
