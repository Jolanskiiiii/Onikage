import unittest

import pygame

import pygame

from onikage.combat import AttackDefinition, AttackInstance, AttackKind, Damage, Hitbox, RealtimeCombat
from onikage.enemy import Enemy
from onikage.masks import (
    SHRINE_PROGRESS, WRAITH_PROGRESS, MaskAbilityKind, MaskManager, MaskType,
    all_mask_types, create_mask,
)
from onikage.player import Player


class MaskStoryAlignmentTests(unittest.TestCase):
    def test_five_masks_match_story_regions_guardians_and_abilities(self):
        expected = {
            MaskType.WRATH: ("Burning Village", "Ashen Oni", "Inferno Slash"),
            MaskType.GRIEF: ("Drowned Temple", "Weeping Bride", "Spirit Veil"),
            MaskType.FEAR: ("Whispering Cedar Forest", "Hollow Stalker", "Shadow Step"),
            MaskType.PRIDE: ("Fallen Kurogane Castle", "Fallen Shogun", "Heavenly Judgment"),
            MaskType.DECEPTION: ("Realm Between Worlds", "Nameless One", "Phantom Double"),
        }
        self.assertEqual(len(all_mask_types()), 5)
        for mask_type, (region, guardian, ability) in expected.items():
            mask = create_mask(mask_type)
            self.assertEqual((mask.region, mask.guardian, mask.ability.name), (region, guardian, ability))

    def test_village_progress_does_not_award_regional_masks(self):
        manager = MaskManager()
        self.assertEqual(manager.advance_story(SHRINE_PROGRESS), ())
        self.assertEqual(manager.advance_story(WRAITH_PROGRESS), ())
        self.assertFalse(manager.owned)
        for mask_type in MaskType:
            self.assertFalse(manager.can_acquire(mask_type))

    def test_guardian_victory_awards_only_its_matching_mask(self):
        manager = MaskManager()
        self.assertTrue(manager.defeat_guardian(MaskType.WRATH))
        self.assertEqual(manager.owned, {MaskType.WRATH})
        self.assertFalse(manager.can_acquire(MaskType.GRIEF))
        self.assertFalse(manager.defeat_guardian(MaskType.WRATH))
        self.assertTrue(manager.defeat_guardian(MaskType.GRIEF))
        self.assertEqual(manager.owned, {MaskType.WRATH, MaskType.GRIEF})

    def test_all_five_guardians_can_award_all_five_masks(self):
        manager = MaskManager()
        for mask_type in MaskType:
            self.assertTrue(manager.defeat_guardian(mask_type))
        self.assertEqual(manager.owned, set(MaskType))


class MaskAbilityTests(unittest.TestCase):
    def _combat_with_mask(self, mask_type):
        player = Player(100, 100)
        enemy = Enemy(150, 100)
        player.mask_manager.defeat_guardian(mask_type)
        player.mask_manager.equipped = mask_type
        return player, enemy, RealtimeCombat(player, enemy)

    def test_wrath_inferno_slash_is_charged_mask_attack(self):
        player, _, combat = self._combat_with_mask(MaskType.WRATH)
        self.assertTrue(combat.begin_mask_charge())
        player.mask_manager.update(1.0)
        self.assertTrue(combat.release_mask_charge((300, 136)))
        self.assertEqual(combat.player_attack.definition.name, "Inferno Slash")
        self.assertEqual(combat.player_attack.definition.kind, AttackKind.MASK)

    def test_grief_spirit_veil_grants_temporary_protection(self):
        player, _, combat = self._combat_with_mask(MaskType.GRIEF)
        self.assertTrue(combat.activate_mask_ability((300, 136)))
        self.assertGreater(combat.spirit_veil_remaining, 0)
        self.assertGreater(combat.player_state.invulnerability_remaining, 0)
        self.assertLess(player.mask_manager.energy, player.mask_manager.max_energy)

    def test_fear_shadow_step_moves_and_grants_invulnerability(self):
        player, _, combat = self._combat_with_mask(MaskType.FEAR)
        origin = player.position.copy()
        self.assertTrue(combat.activate_mask_ability((400, 136)))
        self.assertNotEqual(player.position, origin)
        self.assertGreater(combat.player_state.invulnerability_remaining, 0)

    def test_pride_heavenly_judgment_counters_incoming_attack(self):
        player, enemy, combat = self._combat_with_mask(MaskType.PRIDE)
        combat.counter_remaining = 0.8
        combat.counter_damage_multiplier = 1.55
        attack = AttackInstance(
            AttackDefinition("Enemy windup", AttackKind.ENEMY, 12, 1, 2, 1, 40, 30, 0, 0),
            "left",
        )
        attack.hitbox = Hitbox(pygame.Rect(90, 90, 60, 60), Damage(12))
        player_health, enemy_health = player.health, enemy.health
        self.assertTrue(combat._try_counter(attack))
        self.assertEqual(player.health, player_health)
        self.assertLess(enemy.health, enemy_health)
        self.assertIn("Heavenly Judgment", combat.message)

    def test_deception_phantom_double_becomes_enemy_target(self):
        _, enemy, combat = self._combat_with_mask(MaskType.DECEPTION)
        self.assertTrue(combat.activate_mask_ability((300, 136)))
        decoy = combat.phantom_decoy
        self.assertIsNotNone(decoy)
        self.assertGreater(decoy.remaining, 0)
        combat.enemy_cooldown = 0
        combat.update(0.05)
        self.assertIsNotNone(combat.enemy_attack)
        self.assertNotEqual(combat.enemy_attack.direction, "")
        self.assertGreater(decoy.health, 0)
        self.assertGreater(enemy.health, 0)

    def test_phantom_double_absorbs_an_enemy_hit_instead_of_player(self):
        player, enemy, combat = self._combat_with_mask(MaskType.DECEPTION)
        self.assertTrue(combat.activate_mask_ability((300, 136)))
        decoy = combat.phantom_decoy
        decoy_health = decoy.health
        player_health = player.health
        attack = AttackInstance(
            AttackDefinition("Enemy strike", AttackKind.ENEMY, 12, 1, 2, 1, 100, 30, 0, 0),
            "left",
        )
        attack.hitbox = Hitbox(decoy.rect.copy(), Damage(12))
        self.assertTrue(combat._try_attack_hit(attack, enemy, decoy, combat.phantom_decoy_state))
        self.assertLess(decoy.health, decoy_health)
        self.assertEqual(player.health, player_health)

    def test_phantom_double_expires(self):
        _, _, combat = self._combat_with_mask(MaskType.DECEPTION)
        self.assertTrue(combat.activate_mask_ability((300, 136)))
        combat.update(0.1)
        combat.phantom_decoy.remaining = 0.01
        combat.update(0.05)
        self.assertIsNone(combat.phantom_decoy)


class MaskSaveMigrationTests(unittest.TestCase):
    def test_legacy_ids_and_levels_are_preserved(self):
        legacy = {
            "owned": ["wrath", "shadows", "tengu", "suffering", "onikage"],
            "equipped": "suffering",
            "levels": {"wrath": 3, "shadows": 2, "tengu": 1, "suffering": 3, "onikage": 2},
            "progression": [SHRINE_PROGRESS, WRAITH_PROGRESS],
            "upgrade_tokens": 4,
            "energy": 61.5,
        }
        restored = MaskManager.from_dict(legacy)
        self.assertEqual(restored.owned, set(MaskType))
        self.assertEqual(restored.equipped, MaskType.PRIDE)
        self.assertEqual(restored.level(MaskType.WRATH), 3)
        self.assertEqual(restored.level(MaskType.GRIEF), 2)
        self.assertEqual(restored.level(MaskType.PRIDE), 3)
        self.assertEqual(restored.level(MaskType.DECEPTION), 2)
        self.assertEqual(restored.upgrade_tokens, 4)
        self.assertAlmostEqual(restored.energy, 61.5)

    def test_canonical_save_round_trip_preserves_masks(self):
        manager = MaskManager()
        for mask_type in MaskType:
            manager.defeat_guardian(mask_type)
        manager.upgrade(MaskType.GRIEF)
        manager.equipped = MaskType.DECEPTION
        restored = MaskManager.from_dict(manager.to_dict())
        self.assertEqual(restored.owned, manager.owned)
        self.assertEqual(restored.equipped, manager.equipped)
        self.assertEqual(restored.level(MaskType.GRIEF), 2)


if __name__ == "__main__":
    unittest.main()
