import tempfile
import unittest
from pathlib import Path

import pygame

from onikage.combat import (
    AttackDefinition,
    AttackInstance,
    AttackKind,
    Damage,
    Hitbox,
    RealtimeCombat,
)
from onikage.enemy import Enemy
from onikage.masks import (
    SHRINE_PROGRESS,
    WRAITH_PROGRESS,
    MaskAbilityKind,
    MaskManager,
    MaskType,
)
from onikage.player import Player
from onikage.save_data import SaveData, SaveManager


class MaskProgressionTests(unittest.TestCase):
    def test_story_gates_prevent_early_mask_acquisition(self) -> None:
        manager = MaskManager()
        for mask_type in MaskType:
            self.assertFalse(manager.can_acquire(mask_type))
            self.assertFalse(manager.acquire(mask_type))

        discovered = manager.advance_story(SHRINE_PROGRESS)
        self.assertIn(MaskType.SHADOWS, discovered)
        self.assertTrue(manager.can_acquire(MaskType.TENGU))
        self.assertFalse(manager.can_acquire(MaskType.WRATH))
        self.assertFalse(manager.can_acquire(MaskType.SUFFERING))
        self.assertFalse(manager.can_acquire(MaskType.ONIKAGE))

        manager.advance_story(WRAITH_PROGRESS)
        self.assertIn(MaskType.WRATH, manager.owned)
        self.assertTrue(manager.can_acquire(MaskType.SUFFERING))
        self.assertFalse(manager.can_acquire(MaskType.ONIKAGE))

    def test_onikage_requires_all_four_lesser_masks(self) -> None:
        manager = MaskManager()
        manager.advance_story(SHRINE_PROGRESS)
        manager.advance_story(WRAITH_PROGRESS)
        self.assertTrue(manager.acquire(MaskType.TENGU))
        self.assertFalse(manager.can_acquire(MaskType.ONIKAGE))
        self.assertTrue(manager.acquire(MaskType.SUFFERING))
        self.assertIn(MaskType.ONIKAGE, manager.owned)


class MaskSwitchingTests(unittest.TestCase):
    def test_switch_uses_transition_and_configured_cooldown(self) -> None:
        manager = MaskManager(switch_cooldown_seconds=1.0, transition_seconds=0.2)
        manager.advance_story(SHRINE_PROGRESS)
        manager.advance_story(WRAITH_PROGRESS)

        self.assertTrue(manager.equip(MaskType.WRATH))
        self.assertAlmostEqual(manager.transition_remaining, 0.2)
        self.assertIsNone(manager.cycle(1))
        manager.update(0.2)
        self.assertFalse(manager.equip(MaskType.SHADOWS))
        manager.update(0.8)
        self.assertEqual(manager.cycle(1), MaskType.SHADOWS)
        self.assertEqual(manager.equipped, MaskType.SHADOWS)

    def test_combat_mask_switch_does_not_interrupt_an_attack(self) -> None:
        player = Player(100, 100)
        enemy = Enemy(600, 600)
        player.mask_manager.advance_story(SHRINE_PROGRESS)
        player.mask_manager.advance_story(WRAITH_PROGRESS)
        combat = RealtimeCombat(player, enemy)
        self.assertTrue(combat.start_light((300, 136)))
        self.assertFalse(combat.switch_mask(MaskType.WRATH))
        self.assertIsNotNone(combat.player_attack)
        self.assertNotEqual(player.mask_manager.equipped, MaskType.WRATH)


class MaskAbilityTests(unittest.TestCase):
    def test_wrath_charge_consumes_energy_and_starts_cooldown(self) -> None:
        player = Player(100, 100)
        enemy = Enemy(600, 600)
        player.mask_manager.advance_story(WRAITH_PROGRESS)
        combat = RealtimeCombat(player, enemy)
        manager = player.mask_manager
        energy_before = manager.energy

        self.assertTrue(combat.begin_mask_charge())
        self.assertFalse(combat.start_light((300, 136)))
        manager.update(1.0)
        self.assertTrue(combat.release_mask_charge((300, 136)))
        self.assertEqual(combat.player_attack.definition.kind, AttackKind.MASK)
        self.assertLess(manager.energy, energy_before)
        self.assertGreater(manager.cooldowns[MaskType.WRATH], 0)
        self.assertTrue(combat.player_attack.definition.damage > 34)
        self.assertFalse(combat.begin_mask_charge())

    def test_shadows_dash_moves_and_grants_brief_invulnerability(self) -> None:
        player = Player(100, 100)
        enemy = Enemy(600, 600)
        player.mask_manager.advance_story(SHRINE_PROGRESS)
        combat = RealtimeCombat(player, enemy)
        origin = player.position.copy()
        energy_before = player.mask_manager.energy

        self.assertTrue(combat.activate_mask_ability((400, 136)))
        self.assertNotEqual(player.position, origin)
        self.assertGreater(combat.player_state.invulnerability_remaining, 0)
        self.assertLess(player.mask_manager.energy, energy_before)
        self.assertGreater(player.mask_manager.cooldowns[MaskType.SHADOWS], 0)

    def test_tengu_counter_replaces_incoming_hit_with_weapon_counter(self) -> None:
        player = Player(100, 100)
        enemy = Enemy(150, 100)
        player.mask_manager.advance_story(SHRINE_PROGRESS)
        player.mask_manager.advance_story(WRAITH_PROGRESS)
        player.mask_manager.acquire(MaskType.TENGU)
        player.mask_manager.equipped = MaskType.TENGU
        combat = RealtimeCombat(player, enemy)
        combat.counter_remaining = 0.6
        combat.counter_damage_multiplier = 1.2
        attack = AttackInstance(
            AttackDefinition("Wraith windup", AttackKind.ENEMY, 12, 1, 2, 1, 40, 30, 0, 0),
            "left",
        )
        attack.hitbox = Hitbox(pygame.Rect(90, 90, 60, 60), Damage(12))
        player_health = player.health
        enemy_health = enemy.health

        self.assertTrue(combat._try_counter(attack))
        self.assertEqual(player.health, player_health)
        self.assertLess(enemy.health, enemy_health)
        self.assertEqual(combat.counter_remaining, 0)

    def test_suffering_strike_heals_from_weapon_damage(self) -> None:
        player = Player(100, 100)
        enemy = Enemy(150, 100)
        player.health = 50
        player.mask_manager.advance_story(SHRINE_PROGRESS)
        player.mask_manager.advance_story(WRAITH_PROGRESS)
        player.mask_manager.acquire(MaskType.TENGU)
        player.mask_manager.acquire(MaskType.SUFFERING)
        player.mask_manager.equipped = MaskType.SUFFERING
        combat = RealtimeCombat(player, enemy)
        attack = AttackInstance(
            AttackDefinition("Life-draining strike", AttackKind.MASK, 20, 1, 2, 1, 40, 30, 0, 0),
            "right",
        )
        attack.hitbox = Hitbox(pygame.Rect(140, 90, 60, 60), Damage(20))

        self.assertTrue(combat._try_attack_hit(attack, player, enemy, combat.enemy_state))
        self.assertGreater(player.health, 50)
        self.assertEqual(enemy.health, enemy.max_health - 20)

    def test_onikage_transformation_buffs_weapon_attacks(self) -> None:
        player = Player(100, 100)
        enemy = Enemy(600, 600)
        manager = player.mask_manager
        manager.advance_story(SHRINE_PROGRESS)
        manager.advance_story(WRAITH_PROGRESS)
        manager.acquire(MaskType.TENGU)
        manager.acquire(MaskType.SUFFERING)
        manager.equipped = MaskType.ONIKAGE
        combat = RealtimeCombat(player, enemy)
        base_damage = player.weapon_inventory.definition.light_combo[0].damage

        self.assertTrue(combat.activate_mask_ability((300, 136)))
        self.assertTrue(combat.transformation_active)
        self.assertGreater(combat.transformation_damage_multiplier, 1.0)
        combat.player_attack = None
        combat.player_cooldown = 0
        self.assertTrue(combat.start_light((300, 136)))
        self.assertGreater(combat.player_attack.definition.damage, base_damage)


class MaskUpgradeAndPersistenceTests(unittest.TestCase):
    def test_upgrade_scales_mask_effect_and_is_limited_by_tokens(self) -> None:
        manager = MaskManager()
        manager.advance_story(SHRINE_PROGRESS)
        self.assertEqual(manager.level(MaskType.SHADOWS), 1)
        self.assertTrue(manager.upgrade(MaskType.SHADOWS))
        self.assertEqual(manager.level(MaskType.SHADOWS), 2)
        self.assertGreater(
            manager.mask(MaskType.SHADOWS).passive_effect(2).move_speed_multiplier,
            manager.mask(MaskType.SHADOWS).passive_effect(1).move_speed_multiplier,
        )
        self.assertEqual(manager.upgrade_tokens, 0)
        self.assertFalse(manager.upgrade(MaskType.SHADOWS))

    def test_mask_save_round_trip_preserves_progression_and_upgrade(self) -> None:
        manager = MaskManager()
        manager.advance_story(SHRINE_PROGRESS)
        manager.advance_story(WRAITH_PROGRESS)
        manager.upgrade(MaskType.SHADOWS)
        manager.equipped = MaskType.WRATH

        restored = MaskManager.from_dict(manager.to_dict())
        self.assertEqual(restored.owned, manager.owned)
        self.assertEqual(restored.equipped, MaskType.WRATH)
        self.assertEqual(restored.level(MaskType.SHADOWS), 2)
        self.assertEqual(restored.progression, manager.progression)
        self.assertEqual(restored.upgrade_tokens, manager.upgrade_tokens)

    def test_json_save_preserves_masks_and_upgrade_levels(self) -> None:
        manager = MaskManager()
        manager.advance_story(SHRINE_PROGRESS)
        manager.advance_story(WRAITH_PROGRESS)
        manager.acquire(MaskType.TENGU)
        manager.upgrade(MaskType.SHADOWS)
        manager.equipped = MaskType.TENGU

        with tempfile.TemporaryDirectory() as directory:
            save_manager = SaveManager(Path(directory) / "mask-save.json")
            save_manager.save(SaveData(mask_manager=manager.to_dict()))
            loaded = save_manager.load()

        self.assertIsNotNone(loaded)
        restored = MaskManager.from_dict(loaded.mask_manager)
        self.assertEqual(restored.owned, manager.owned)
        self.assertEqual(restored.level(MaskType.SHADOWS), 2)
        self.assertEqual(restored.equipped, MaskType.TENGU)


if __name__ == "__main__":
    unittest.main()
