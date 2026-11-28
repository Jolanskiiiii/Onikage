from pathlib import Path
import unittest
import pygame


class TerrainAtlasCleanTests(unittest.TestCase):
    def test_ground_and_road_tile_edges_have_no_transparent_or_pale_grid(self):
        path = (Path(__file__).parents[1] / "onikage" / "art" / "tiles"
                / "kagehama_ground_atlas.png")
        atlas = pygame.image.load(str(path))
        self.assertEqual(atlas.get_size(), (448, 128))
        # Rows 0 and 1 are the grass and road tiles used by VillageWorld.
        for row in (0, 1):
            for column in range(14):
                ox, oy = column * 32, row * 32
                for local_y in range(32):
                    for local_x in range(32):
                        if local_x not in (0, 1, 30, 31) and local_y not in (0, 1, 30, 31):
                            continue
                        r, g, b, a = atlas.get_at((ox + local_x, oy + local_y))
                        self.assertEqual(a, 255, f"Transparent tile seam at {(column, row, local_x, local_y)}")
                        self.assertFalse(
                            min(r, g, b) >= 145 and max(r, g, b) - min(r, g, b) <= 25,
                            f"Pale tile outline at {(column, row, local_x, local_y)}"
                        )
