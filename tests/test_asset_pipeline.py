import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from onikage.art.asset_pipeline import (
    Animation,
    SpriteSheet,
    TileMap,
    clear_asset_cache,
    load_image,
    scale_nearest,
)


class AssetPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        clear_asset_cache()

    def tearDown(self) -> None:
        clear_asset_cache()
        pygame.quit()

    def test_load_image_caches_decoded_surface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.png"
            source = pygame.Surface((2, 2), pygame.SRCALPHA)
            source.fill((80, 20, 10, 255))
            pygame.image.save(source, path)

            first = load_image(path)
            second = load_image(path)

            self.assertIs(first, second)
            self.assertEqual(first.get_at((0, 0)), (80, 20, 10, 255))

    def test_missing_image_reports_its_path(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "missing.png"):
            load_image(Path(tempfile.gettempdir()) / "missing.png")

    def test_sprite_sheet_slices_explicit_rows_and_columns(self) -> None:
        image = pygame.Surface((4, 2))
        image.fill((0, 0, 0))
        image.fill((255, 0, 0), (0, 0, 2, 2))
        image.fill((0, 255, 0), (2, 0, 2, 2))
        image.fill((0, 0, 255), (0, 1, 2, 1))

        sheet = SpriteSheet(image, (2, 1))

        self.assertEqual((sheet.columns, sheet.rows), (2, 2))
        self.assertEqual(sheet.frame(1, 0).get_at((0, 0)), (0, 255, 0, 255))
        self.assertEqual(len(sheet.row(1)), 2)

    def test_sprite_sheet_rejects_non_divisible_dimensions(self) -> None:
        with self.assertRaisesRegex(ValueError, "not divisible"):
            SpriteSheet(pygame.Surface((5, 4)), (2, 2))

    def test_animation_advances_loops_and_clamps_non_looping_frames(self) -> None:
        frames = tuple(pygame.Surface((1, 1)) for _ in range(3))
        animation = Animation(frames, frame_duration=0.1)

        animation.update(0.25)
        self.assertEqual(animation.index, 2)
        animation.update(0.1)
        self.assertEqual(animation.index, 0)

        one_shot = Animation(frames, frame_duration=0.1, loop=False)
        one_shot.update(0.5)
        self.assertEqual(one_shot.index, 2)
        self.assertTrue(one_shot.finished)
        one_shot.update(0.1)
        self.assertEqual(one_shot.index, 2)

    def test_nearest_scale_preserves_source_pixel_blocks(self) -> None:
        source = pygame.Surface((2, 1))
        source.set_at((0, 0), (255, 0, 0))
        source.set_at((1, 0), (0, 0, 255))

        scaled = scale_nearest(source, (4, 2))

        self.assertEqual(scaled.get_at((0, 0)), (255, 0, 0, 255))
        self.assertEqual(scaled.get_at((1, 1)), (255, 0, 0, 255))
        self.assertEqual(scaled.get_at((2, 0)), (0, 0, 255, 255))

    def test_tile_map_renders_and_rejects_missing_or_mismatched_tiles(self) -> None:
        red = pygame.Surface((2, 2))
        red.fill((255, 0, 0))
        blue = pygame.Surface((2, 2))
        blue.fill((0, 0, 255))
        tile_map = TileMap((("red", "blue"), (None, "red")), 2)
        target = pygame.Surface((4, 4))

        tile_map.draw(target, {"red": red, "blue": blue}, origin=(1, 1))

        self.assertEqual(target.get_at((1, 1)), (255, 0, 0, 255))
        self.assertEqual(target.get_at((3, 1)), (0, 0, 255, 255))
        self.assertEqual(target.get_at((1, 3)), (0, 0, 0, 255))
        with self.assertRaisesRegex(KeyError, "blue"):
            tile_map.draw(target, {"red": red})
        with self.assertRaisesRegex(ValueError, "expected"):
            tile_map.draw(target, {"red": pygame.Surface((1, 1)), "blue": blue})


if __name__ == "__main__":
    unittest.main()
