"""Region-specific pixel-art terrain atlas renderer for ONIKAGE chapters."""
from functools import lru_cache
from pathlib import Path
import pygame

_ATLAS_DIR = Path(__file__).resolve().parent / "regions"

@lru_cache(maxsize=8)
def _tiles(region_id: str):
    path = _ATLAS_DIR / f"{region_id}_tiles.png"
    atlas = pygame.image.load(str(path)).convert_alpha()
    return tuple(atlas.subsurface((i * 32, 0, 32, 32)).copy() for i in range(8))

def draw_region_tiles(surface, camera, tile_size, columns, rows, road_test, region_id):
    """Blit a dedicated 4-ground/4-path atlas with stable variation per tile."""
    tiles = _tiles(region_id)
    left = max(0, int(camera.x // tile_size))
    top = max(0, int(camera.y // tile_size))
    right = min(columns, int((camera.x + surface.get_width()) // tile_size) + 2)
    bottom = min(rows, int((camera.y + surface.get_height()) // tile_size) + 2)
    for row in range(top, bottom):
        for col in range(left, right):
            road = road_test(col, row)
            # Spatial hash avoids visible checkerboard/repeating stripes.
            h = (col * 73856093) ^ (row * 19349663) ^ (col * row * 83492791)
            index = (h & 0x7fffffff) % 4
            tile = tiles[(4 if road else 0) + index]
            surface.blit(tile, (col * tile_size - round(camera.x), row * tile_size - round(camera.y)))
