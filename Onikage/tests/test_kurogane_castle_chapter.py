import unittest
from pathlib import Path


class KuroganeCastleChapterSourceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parents[1]

    def test_castle_world_defines_fallen_shogun_and_return_gate(self):
        source = (self.root / "onikage" / "kurogane_castle.py").read_text(encoding="utf-8")
        self.assertIn('self.wraith.name = "Fallen Shogun"', source)
        self.assertIn("RETURN_GATE", source)
        self.assertIn("CHAPTER V", source)

    def test_game_routes_and_restores_castle_region(self):
        source = (self.root / "onikage" / "game.py").read_text(encoding="utf-8")
        self.assertIn('self.campaign.current_region == "kurogane_castle"', source)
        self.assertIn('"kurogane_castle": "fallen_shogun"', source)
        self.assertIn('"Fallen Shogun": ("fallen_shogun", MaskType.PRIDE', source)
        self.assertIn('self.campaign.travel_to("kurogane_castle")', source)


if __name__ == "__main__":
    unittest.main()
