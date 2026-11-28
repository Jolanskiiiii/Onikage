import unittest

from onikage.campaign import CampaignProgress, REGION_ORDER
from onikage.save_data import SaveData


class CampaignProgressTests(unittest.TestCase):
    def test_campaign_starts_in_village_only(self):
        progress = CampaignProgress()
        self.assertEqual(progress.current_region, "kagehama_village")
        self.assertEqual(progress.unlocked_regions, ["kagehama_village"])

    def test_guardian_unlocks_next_region(self):
        progress = CampaignProgress()
        self.assertFalse(progress.unlock_region("drowned_temple"))
        self.assertTrue(progress.record_guardian_victory("ashen_oni"))
        self.assertIn("drowned_temple", progress.unlocked_regions)

    def test_guardian_victory_is_idempotent(self):
        progress = CampaignProgress()
        self.assertTrue(progress.record_guardian_victory("ashen_oni"))
        self.assertFalse(progress.record_guardian_victory("ashen_oni"))

    def test_travel_requires_unlocked_region(self):
        progress = CampaignProgress()
        self.assertFalse(progress.travel_to("cedar_forest"))
        progress.record_guardian_victory("ashen_oni")
        progress.record_guardian_victory("weeping_bride")
        self.assertTrue(progress.travel_to("cedar_forest"))

    def test_final_ending_requires_final_guardian(self):
        progress = CampaignProgress()
        with self.assertRaises(ValueError):
            progress.choose_ending("humanity")
        for guardian in ("ashen_oni", "weeping_bride", "hollow_stalker", "fallen_shogun", "nameless_one"):
            progress.record_guardian_victory(guardian)
        progress.choose_ending("humanity")
        self.assertEqual(progress.ending, "humanity")

    def test_invalid_campaign_data_is_rejected(self):
        with self.assertRaises(ValueError):
            CampaignProgress.from_dict({"current_region": "unknown"})

    def test_campaign_round_trips_through_save_data(self):
        progress = CampaignProgress()
        progress.record_guardian_victory("ashen_oni")
        save = SaveData(campaign=progress.to_dict())
        loaded = SaveData.from_dict(save.to_dict())
        self.assertEqual(loaded.campaign["defeated_guardians"], ["ashen_oni"])
        self.assertIn("drowned_temple", loaded.campaign["unlocked_regions"])

    def test_version_two_saves_migrate_with_default_campaign(self):
        old = SaveData().to_dict()
        old["version"] = 2
        old.pop("campaign")
        loaded = SaveData.from_dict(old)
        self.assertEqual(loaded.version, 3)
        self.assertEqual(loaded.campaign["current_region"], REGION_ORDER[0])


if __name__ == "__main__":
    unittest.main()
