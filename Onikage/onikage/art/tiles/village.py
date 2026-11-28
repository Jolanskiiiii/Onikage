"""Deterministic top-down terrain tiles for Kagehama Village.

The grass is layered mossy ground with visible plant clusters and fallen leaves.
The road is an irregular stone-and-packed-earth path with cracked joints and
moss seams; both are authored at the game's native 32px tile scale.
"""

import random
from functools import lru_cache
from pathlib import Path

import pygame


@lru_cache(maxsize=4)
def make_village_tiles(
    tile_size: int,
) -> tuple[tuple[pygame.Surface, ...], tuple[pygame.Surface, ...]]:
    """Load the coordinated Kagehama terrain atlas and scale to world tiles.

    The atlas is authored as 14 columns x 4 rows of 32px tiles. Row 0 is
    moss/grass variation; row 1 contains earth and cobblestone variants.
    Procedural fallback remains available if an asset is missing.
    """
    atlas_path = Path(__file__).with_name("kagehama_ground_atlas.png")
    if atlas_path.exists():
        atlas = pygame.image.load(str(atlas_path)).convert_alpha()
        grass_tiles: list[pygame.Surface] = []
        road_tiles: list[pygame.Surface] = []
        for column in range(14):
            grass = atlas.subsurface((column * 32, 0, 32, 32)).copy()
            road = atlas.subsurface((column * 32, 32, 32, 32)).copy()
            if tile_size != 32:
                grass = pygame.transform.scale(grass, (tile_size, tile_size))
                road = pygame.transform.scale(road, (tile_size, tile_size))
            grass_tiles.append(grass)
            # The last seven cells are the intended paved-road variants;
            # the first seven are packed earth and serve as transition choices.
            road_tiles.append(road)
        return tuple(grass_tiles), tuple(road_tiles)

    # Safe fallback for source distributions where the optional atlas is absent.
    grass_tiles: list[pygame.Surface] = []
    road_tiles: list[pygame.Surface] = []
    for variant in range(12):
        rng = random.Random(4100 + variant * 97)
        grass = pygame.Surface((tile_size, tile_size))
        grass.fill((25 + variant % 3, 35 + variant % 4, 27 + variant % 3))
        for _ in range(18):
            x, y = rng.randrange(tile_size), rng.randrange(tile_size)
            pygame.draw.circle(grass, rng.choice(((29, 46, 31), (47, 61, 36), (72, 76, 43))), (x, y), rng.randrange(1, 3))
        road = pygame.Surface((tile_size, tile_size))
        road.fill((48, 42, 39))
        for _ in range(6):
            x, y = rng.randrange(tile_size), rng.randrange(tile_size)
            pygame.draw.rect(road, rng.choice(((83, 73, 64), (91, 77, 65), (72, 66, 60))), (x, y, max(2, tile_size // 3), max(2, tile_size // 5)))
        grass_tiles.append(grass)
        road_tiles.append(road)
    return tuple(grass_tiles), tuple(road_tiles)
