import unittest

import pygame

from onikage.combat import (
    AttackDefinition,
    AttackInstance,
    AttackKind,
    CombatState,
    ComboTracker,
    Damage,
    Health,
    Hitbox,
    Hurtbox,
    RealtimeCombat,
    top_down_attack_direction,
)
from onikage.enemy import Enemy
from onikage.player import Player


class FakeKeys:
    def __init__(self, pressed: set[int] | None = None) -> None:
        self.pressed = pressed or set()

    def __getitem__(self, key: int) -> bool:
        return key in self.pressed


class HealthAndHitboxTests(unittest.TestCase):
    def test_damage_is_clamped_and_health_can_be_restored(self) -> None:
        health = Health(10, 8)
        self.assertEqual(health.apply_damage(3), 3)
        self.assertEqual(health.current, 5)
        self.assertEqual(health.apply_damage(99), 5)
        self.assertEqual(health.current, 0)
        self.assertEqual(health.heal(7), 7)
        self.assertEqual(health.current, 7)

    def test_hitbox_only_hits_each_target_once_by_default(self) -> None:
        hitbox = Hitbox(pygame.Rect(0, 0, 20, 20), Damage(5))
        target = Hurtbox(pygame.Rect(10, 10, 10, 10))
        identity = object()
        self.assertTrue(hitbox.try_hit(target, identity))
        self.assertFalse(hitbox.try_hit(target, identity))

    def test_hitbox_can_explicitly_hit_target_more_than_once(self) -> None:
        hitbox = Hitbox(
            pygame.Rect(0, 0, 20, 20), Damage(5), can_hit_multiple_times=True
        )
        target = Hurtbox(pygame.Rect(10, 10, 10, 10))
        identity = object()
        self.assertTrue(hitbox.try_hit(target, identity))
        self.assertTrue(hitbox.try_hit(target, identity))


class AttackTimingTests(unittest.TestCase):
    def test_attack_moves_through_startup_active_and_recovery_frames(self) -> None:
        definition = AttackDefinition(
            "Test Cut", AttackKind.LIGHT, 5, 3, 2, 4, 30, 20, 0, 0
        )
        attack = AttackInstance(definition, "right")
        self.assertEqual(attack.state, CombatState.STARTUP)
        attack.advance(3 / 60)
        self.assertEqual(attack.state, CombatState.ACTIVE)
        attack.advance(2 / 60)
        self.assertEqual(attack.state, CombatState.RECOVERY)
        attack.advance(4 / 60)
        self.assertTrue(attack.finished)
        self.assertEqual(attack.state, CombatState.IDLE)

    def test_three_hit_combo_resets_after_timing_window(self) -> None:
        combo = ComboTracker(combo_window=0.5)
        self.assertEqual(combo.next_step(0.0), 1)
        self.assertEqual(combo.next_step(0.3), 2)
        self.assertEqual(combo.next_step(0.6), 3)
        self.assertEqual(combo.next_step(1.2), 1)

    def test_mouse_direction_uses_direct_top_down_screen_axes(self) -> None:
        self.assertEqual(top_down_attack_direction((100, 100), (200, 100)), "right")
        self.assertEqual(top_down_attack_direction((100, 100), (200, 200)), "down-right")
        self.assertEqual(top_down_attack_direction((100, 100), (100, 200)), "down")


class RealtimeCombatTests(unittest.TestCase):
    def test_active_light_attack_hits_enemy_once(self) -> None:
        player = Player(100, 100)
        enemy = Enemy(150, 100)
        combat = RealtimeCombat(player, enemy)
        combat.target_assist.enabled = False
        self.assertTrue(combat.start_light((300, 136)))
        combat.update(5 / 60)
        self.assertEqual(enemy.health, enemy.max_health - 13)
        combat.update(1 / 60)
        self.assertEqual(enemy.health, enemy.max_health - 13)

    def test_light_attack_allows_movement_and_heavy_active_frames_commit(self) -> None:
        keys = FakeKeys({pygame.K_d})
        player = Player(100, 100)
        enemy = Enemy(500, 500)
        combat = RealtimeCombat(player, enemy)

        self.assertTrue(combat.start_light((300, 136)))
        combat.update(5 / 60)
        self.assertFalse(combat.movement_locked)
        light_start = player.position.copy()
        player.update(0.1, keys, [], movement_locked=combat.movement_locked)
        self.assertNotEqual(player.position, light_start)

        player.position.update(100, 100)
        player.rect.topleft = (100, 100)
        combat.player_attack = None
        combat.player_cooldown = 0
        self.assertTrue(combat.start_heavy((300, 136)))
        combat.update(0.1)
        combat.update(0.1)
        combat.update(1 / 60)
        self.assertTrue(combat.movement_locked)
        heavy_start = player.position.copy()
        player.update(0.1, keys, [], movement_locked=combat.movement_locked)
        self.assertEqual(player.position, heavy_start)


if __name__ == "__main__":
    unittest.main()

class AshenOniBossTests(unittest.TestCase):
    def test_ashen_oni_uses_guardian_attack_and_expanded_engage_range(self) -> None:
        player = Player(100, 100)
        enemy = Enemy(230, 100, name="Ashen Oni", max_health=190, attack_power=19)
        combat = RealtimeCombat(player, enemy)
        combat.enemy_cooldown = 0
        combat._advance_enemy_attack(1 / 60)
        self.assertIsNotNone(combat.enemy_attack)
        self.assertEqual(combat.enemy_attack.definition.name, "Cinder Cleave")

    def test_ashen_oni_enters_enraged_phase_below_half_health(self) -> None:
        player = Player(100, 100)
        enemy = Enemy(150, 100, name="Ashen Oni", max_health=190, attack_power=19)
        combat = RealtimeCombat(player, enemy)
        enemy.health = 94
        combat.update(1 / 60)
        self.assertEqual(combat.enemy_phase, 2)
        self.assertIn("cursed flame", combat.message)
        combat.enemy_cooldown = 0
        combat._advance_enemy_attack(1 / 60)
        self.assertIsNotNone(combat.enemy_attack)
        self.assertEqual(combat.enemy_attack.definition.name, "Infernal Sweep")
