import unittest
from pathlib import Path

from onikage.campaign import CampaignProgress


class RealmBetweenWorldsChapterTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parents[1]

    def test_final_region_and_guardian_are_registered(self):
        from onikage.campaign import GUARDIAN_BY_REGION, REGION_ORDER
        self.assertEqual(REGION_ORDER[-1], "realm_between_worlds")
        self.assertEqual(GUARDIAN_BY_REGION["realm_between_worlds"], "nameless_one")

    def test_shogun_victory_unlocks_final_realm_and_final_boss_unlocks_endings(self):
        campaign = CampaignProgress(
            current_region="kurogane_castle",
            unlocked_regions=["kagehama_village", "burning_village", "drowned_temple", "cedar_forest", "kurogane_castle"],
            defeated_guardians=["ashen_oni", "weeping_bride", "hollow_stalker"],
        )
        self.assertTrue(campaign.record_guardian_victory("fallen_shogun"))
        self.assertIn("realm_between_worlds", campaign.unlocked_regions)
        self.assertTrue(campaign.travel_to("realm_between_worlds"))
        self.assertTrue(campaign.record_guardian_victory("nameless_one"))
        campaign.choose_ending("humanity")
        self.assertEqual(campaign.ending, "humanity")

    def test_realm_world_has_final_guardian_and_return_gate(self):
        source = (self.root / "onikage" / "realm_between_worlds.py").read_text(encoding="utf-8")
        self.assertIn('self.wraith.name = "Nameless One"', source)
        self.assertIn("RETURN_GATE", source)
        self.assertIn("FINAL CHAPTER", source)

    def test_game_routes_saves_and_rewards_final_guardian(self):
        source = (self.root / "onikage" / "game.py").read_text(encoding="utf-8")
        self.assertIn('self.campaign.current_region == "realm_between_worlds"', source)
        self.assertIn('"Nameless One": ("nameless_one", MaskType.DECEPTION', source)
        self.assertIn('self.campaign.choose_ending(ending)', source)
        self.assertIn('self.campaign.travel_to("realm_between_worlds")', source)


if __name__ == "__main__":
    unittest.main()
