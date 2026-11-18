import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from tools.asset_preview import AssetPackPreview, WINDOW_SIZE


class AssetPackPreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.preview = AssetPackPreview()
        self.target = pygame.Surface(WINDOW_SIZE)

    def tearDown(self) -> None:
        pygame.quit()

    def test_selected_animation_layouts_match_source_sheets(self) -> None:
        self.assertEqual((self.preview.ninja_idle.columns, self.preview.ninja_idle.rows), (4, 1))
        self.assertEqual((self.preview.ninja_walk.columns, self.preview.ninja_walk.rows), (4, 4))
        self.assertEqual(len(self.preview.crawler_animations["Idle Down"].frames), 4)
        self.assertEqual(len(self.preview.crawler_animations["Walk Down"].frames), 6)
        self.assertEqual(len(self.preview.crawler_animations["Slice Down"].frames), 8)

    def test_all_four_pack_scenes_render(self) -> None:
        for pack_index in range(4):
            with self.subTest(pack_index=pack_index):
                self.preview.current_pack = pack_index
                self.preview.draw(self.target, 0.1)
                self.assertEqual(self.target.get_size(), WINDOW_SIZE)
                self.assertNotEqual(self.target.get_at((10, 10)), (0, 0, 0, 255))


if __name__ == "__main__":
    unittest.main()
