import tempfile
import unittest
from pathlib import Path

from onikage.combat import HitboxShape, RealtimeCombat
from onikage.enemy import Enemy
from onikage.player import Player
from onikage.save_data import SaveData, SaveManager
from onikage.weapons import (
    WEAPON_DEFINITIONS,
    WEAPON_ORDER,
    WeaponInventory,
    WeaponType,
)


class WeaponStatisticsTests(unittest.TestCase):
    def test_each_weapon_has_distinct_attack_profile(self) -> None:
        profiles = [WEAPON_DEFINITIONS[weapon] for weapon in WEAPON_ORDER]
        self.assertEqual(len({profile.attack_speed for profile in profiles}), 4)
        self.assertEqual(len({profile.attack_range for profile in profiles}), 4)
        self.assertEqual(len({profile.light_stamina_cost for profile in profiles}), 4)
        self.assertEqual(len({profile.heavy_stamina_cost for profile in profiles}), 4)
        self.assertEqual([len(profile.light_combo) for profile in profiles], [3, 4, 3, 2])
        self.assertEqual(
            len({profile.heavy_attack.damage for profile in profiles}),
            4,
        )
        self.assertEqual(
            len({profile.hitbox_shape for profile in profiles}),
            4,
        )
        self.assertEqual(
            len({tuple(attack.recovery_frames for attack in profile.light_combo) for profile in profiles}),
            4,
        )


class WeaponInventoryTests(unittest.TestCase):
    def test_katana_is_the_only_starting_weapon(self) -> None:
        inventory = WeaponInventory()
        self.assertEqual(inventory.owned, {WeaponType.KATANA})
        self.assertEqual(inventory.equipped, WeaponType.KATANA)

    def test_acquisition_is_idempotent_and_assigns_quick_slots(self) -> None:
        inventory = WeaponInventory()
        self.assertTrue(inventory.acquire(WeaponType.YARI))
        self.assertFalse(inventory.acquire(WeaponType.YARI))
        self.assertEqual(inventory.weapon_for_slot(3), WeaponType.YARI)
        self.assertIsNone(inventory.weapon_for_slot(4))
        self.assertEqual(inventory.next_owned(1), WeaponType.YARI)

    def test_switching_does_not_interrupt_attacks_or_reset_cooldowns(self) -> None:
        player = Player(100, 100)
        enemy = Enemy(600, 600)
        player.weapon_inventory.acquire(WeaponType.DUAL_BLADES)
        combat = RealtimeCombat(player, enemy)

        self.assertTrue(combat.start_light((300, 136)))
        self.assertFalse(combat.switch_weapon(WeaponType.DUAL_BLADES))
        self.assertEqual(player.weapon_inventory.equipped, WeaponType.KATANA)
        self.assertIsNotNone(combat.player_attack)

        combat.player_attack = None
        combat.player_cooldown = 0.25
        self.assertTrue(combat.switch_weapon(WeaponType.DUAL_BLADES))
        self.assertAlmostEqual(combat.player_cooldown, 0.25)
        self.assertFalse(combat.start_light((300, 136)))
        combat.update(0.1)
        combat.update(0.1)
        combat.update(0.05)
        self.assertTrue(combat.start_light((300, 136)))

    def test_unowned_weapon_cannot_be_equipped(self) -> None:
        inventory = WeaponInventory()
        self.assertFalse(inventory.equip(WeaponType.ODACHI))
        self.assertEqual(inventory.equipped, WeaponType.KATANA)

    def test_equipped_weapon_profile_drives_light_and_heavy_attacks(self) -> None:
        player = Player(100, 100)
        player.weapon_inventory.acquire(WeaponType.YARI)
        player.weapon_inventory.acquire(WeaponType.ODACHI)
        player.weapon_inventory.equip(WeaponType.YARI)
        combat = RealtimeCombat(player, Enemy(600, 600))

        self.assertTrue(combat.start_light((300, 136)))
        light = combat.player_attack
        self.assertEqual(light.definition.damage, 12)
        self.assertEqual(light.definition.reach, 82)
        self.assertEqual(light.definition.hitbox_shape, HitboxShape.THRUST)
        self.assertEqual(light.speed_multiplier, 0.92)

        combat.player_attack = None
        combat.player_cooldown = 0
        self.assertTrue(combat.switch_weapon(WeaponType.ODACHI))
        stamina_before = player.stamina
        self.assertTrue(combat.start_heavy((300, 136)))
        heavy = combat.player_attack
        self.assertEqual(heavy.definition.damage, 58)
        self.assertEqual(heavy.definition.hitbox_shape, HitboxShape.WIDE)
        self.assertEqual(heavy.speed_multiplier, 0.72)
        self.assertEqual(player.stamina, stamina_before - 32)


class WeaponPersistenceTests(unittest.TestCase):
    def test_save_round_trip_preserves_owned_and_equipped_weapons(self) -> None:
        inventory = WeaponInventory()
        inventory.acquire(WeaponType.DUAL_BLADES)
        inventory.acquire(WeaponType.YARI)
        inventory.equip(WeaponType.YARI)
        save = SaveData(
            player_x=312.5,
            player_y=478.25,
            weapon_inventory=inventory.to_dict(),
        )

        with tempfile.TemporaryDirectory() as directory:
            manager = SaveManager(Path(directory) / "save.json")
            self.assertFalse(manager.exists)
            manager.save(save)
            self.assertTrue(manager.exists)
            loaded = manager.load()

        self.assertIsNotNone(loaded)
        restored = WeaponInventory.from_dict(loaded.weapon_inventory)
        self.assertEqual(
            restored.owned,
            {WeaponType.KATANA, WeaponType.DUAL_BLADES, WeaponType.YARI},
        )
        self.assertEqual(restored.equipped, WeaponType.YARI)
        self.assertEqual(loaded.player_x, 312.5)
        self.assertEqual(loaded.player_y, 478.25)

    def test_invalid_equipped_weapon_falls_back_to_starting_katana(self) -> None:
        inventory = WeaponInventory.from_dict(
            {"owned": ["yari"], "equipped": "odachi"}
        )
        self.assertIn(WeaponType.KATANA, inventory.owned)
        self.assertEqual(inventory.equipped, WeaponType.KATANA)


if __name__ == "__main__":
    unittest.main()
