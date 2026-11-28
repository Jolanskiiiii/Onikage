"""Pygame-free campaign progression regression tests."""
import unittest

from onikage.campaign import CampaignProgress, REGION_ORDER


class CampaignSequenceTests(unittest.TestCase):
    def test_five_guardians_unlock_regions_in_order(self):
        progress = CampaignProgress()
        self.assertTrue(progress.complete_prologue())
        expected = [
            ("ashen_oni", "drowned_temple"),
            ("weeping_bride", "cedar_forest"),
            ("hollow_stalker", "kurogane_castle"),
            ("fallen_shogun", "realm_between_worlds"),
        ]
        for guardian, next_region in expected:
            self.assertTrue(progress.record_guardian_victory(guardian))
            self.assertIn(next_region, progress.unlocked_regions)
        self.assertEqual(progress.unlocked_regions, list(REGION_ORDER))

    def test_final_guardian_unlocks_all_three_ending_choices(self):
        progress = CampaignProgress()
        progress.complete_prologue()
        for guardian in ("ashen_oni", "weeping_bride", "hollow_stalker", "fallen_shogun", "nameless_one"):
            progress.record_guardian_victory(guardian)
        for ending in ("humanity", "curse", "exile"):
            snapshot = CampaignProgress.from_dict(progress.to_dict())
            snapshot.choose_ending(ending)
            self.assertEqual(snapshot.ending, ending)

    def test_ending_cannot_be_chosen_before_final_guardian(self):
        progress = CampaignProgress()
        with self.assertRaises(ValueError):
            progress.choose_ending("exile")

    def test_guardian_rewards_are_idempotent(self):
        progress = CampaignProgress()
        self.assertTrue(progress.record_guardian_victory("nameless_one"))
        self.assertFalse(progress.record_guardian_victory("nameless_one"))
        self.assertEqual(progress.defeated_guardians.count("nameless_one"), 1)


if __name__ == "__main__":
    unittest.main()
