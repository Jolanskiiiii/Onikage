import unittest
from onikage.campaign import CampaignProgress, LORE_FRAGMENTS

class CampaignChronicleTests(unittest.TestCase):
    def test_prologue_unlocks_first_lore(self):
        progress = CampaignProgress()
        self.assertTrue(progress.complete_prologue())
        self.assertIn("prologue", progress.lore_unlocked)

    def test_guardian_victories_unlock_chapter_lore(self):
        progress = CampaignProgress()
        progress.record_guardian_victory("ashen_oni")
        self.assertIn("wrath", progress.lore_unlocked)
        progress.record_guardian_victory("weeping_bride")
        self.assertIn("grief", progress.lore_unlocked)
        progress.record_guardian_victory("hollow_stalker")
        self.assertIn("fear", progress.lore_unlocked)
        progress.record_guardian_victory("fallen_shogun")
        self.assertIn("pride", progress.lore_unlocked)
        progress.record_guardian_victory("nameless_one")
        self.assertIn("deception", progress.lore_unlocked)

    def test_lore_survives_save_round_trip(self):
        progress = CampaignProgress()
        progress.complete_prologue()
        progress.record_guardian_victory("ashen_oni")
        restored = CampaignProgress.from_dict(progress.to_dict())
        self.assertEqual(restored.lore_unlocked, ["prologue", "wrath"])

    def test_ending_unlocks_epilogue(self):
        progress = CampaignProgress()
        progress.record_guardian_victory("nameless_one")
        progress.choose_ending("humanity")
        self.assertIn("humanity_ending", progress.lore_unlocked)

    def test_every_fragment_has_story_text(self):
        self.assertEqual(len(LORE_FRAGMENTS), 9)
        self.assertTrue(all(entry["text"] for entry in LORE_FRAGMENTS.values()))

if __name__ == "__main__":
    unittest.main()
