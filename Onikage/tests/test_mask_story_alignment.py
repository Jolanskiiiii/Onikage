import unittest

from onikage.masks import MaskManager, MaskType, all_mask_types, create_mask


class FiveMaskStoryAlignmentTests(unittest.TestCase):
    def test_mask_definitions_match_the_story_document(self):
        expected = {
            MaskType.WRATH: ("Burning Village", "Ashen Oni", "Inferno Slash"),
            MaskType.GRIEF: ("Drowned Temple", "Weeping Bride", "Spirit Veil"),
            MaskType.FEAR: ("Whispering Cedar Forest", "Hollow Stalker", "Shadow Step"),
            MaskType.PRIDE: ("Fallen Kurogane Castle", "Fallen Shogun", "Heavenly Judgment"),
            MaskType.DECEPTION: ("Realm Between Worlds", "Nameless One", "Phantom Double"),
        }
        self.assertEqual(len(all_mask_types()), 5)
        for mask_type, expected_fields in expected.items():
            mask = create_mask(mask_type)
            self.assertEqual((mask.region, mask.guardian, mask.ability.name), expected_fields)

    def test_only_the_matching_guardian_unlocks_a_mask(self):
        manager = MaskManager()
        for mask_type in all_mask_types():
            self.assertFalse(manager.can_acquire(mask_type))
        self.assertTrue(manager.defeat_guardian(MaskType.FEAR))
        self.assertEqual(manager.owned, {MaskType.FEAR})
        self.assertFalse(manager.can_acquire(MaskType.PRIDE))

    def test_village_milestones_do_not_award_regional_masks(self):
        manager = MaskManager()
        manager.advance_story("shrine_quest_completed")
        manager.advance_story("wraith_defeated")
        self.assertEqual(manager.owned, set())

    def test_legacy_mask_ids_migrate_without_losing_equipment_or_upgrades(self):
        manager = MaskManager.from_dict({
            "owned": ["wrath", "shadows", "tengu", "suffering", "onikage"],
            "equipped": "tengu",
            "levels": {"wrath": 3, "shadows": 2, "tengu": 2, "suffering": 1, "onikage": 3},
            "progression": ["shrine_quest_completed", "wraith_defeated"],
            "upgrade_tokens": 5,
            "energy": 43.5,
        })
        self.assertEqual(manager.owned, set(MaskType))
        self.assertEqual(manager.equipped, MaskType.FEAR)
        self.assertEqual(manager.level(MaskType.WRATH), 3)
        self.assertEqual(manager.level(MaskType.GRIEF), 2)
        self.assertEqual(manager.level(MaskType.FEAR), 2)
        self.assertEqual(manager.level(MaskType.DECEPTION), 3)
        self.assertEqual(manager.upgrade_tokens, 5)
        self.assertEqual(manager.energy, 43.5)


if __name__ == "__main__":
    unittest.main()
