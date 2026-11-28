from pathlib import Path
import unittest


class EnvironmentAtlasAssetTests(unittest.TestCase):
    def test_kagehama_ground_atlas_is_packaged(self):
        path = Path(__file__).parents[1] / "onikage" / "art" / "tiles" / "kagehama_ground_atlas.png"
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 10_000)

    def test_props_reference_atlas_is_packaged(self):
        path = Path(__file__).parents[1] / "onikage" / "art" / "tiles" / "kagehama_props_atlas.png"
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 100_000)


if __name__ == "__main__":
    unittest.main()
