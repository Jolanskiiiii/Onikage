"""Weapon definitions and owned/equipped weapon state."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from onikage.combat import AttackDefinition, AttackKind, HitboxShape


class WeaponType(str, Enum):
    KATANA = "katana"
    DUAL_BLADES = "dual_blades"
    YARI = "yari"
    ODACHI = "odachi"


WEAPON_ORDER = (
    WeaponType.KATANA,
    WeaponType.DUAL_BLADES,
    WeaponType.YARI,
    WeaponType.ODACHI,
)


@dataclass(frozen=True)
class WeaponDefinition:
    weapon_type: WeaponType
    display_name: str
    attack_speed: float
    attack_range: int
    light_stamina_cost: float
    heavy_stamina_cost: float
    combo_window: float
    light_combo: tuple[AttackDefinition, ...]
    heavy_attack: AttackDefinition
    hitbox_shape: HitboxShape
    heavy_hitbox_shape: HitboxShape

    def __post_init__(self) -> None:
        if self.attack_speed <= 0 or self.attack_range <= 0:
            raise ValueError("Weapon speed and range must be positive.")
        if self.light_stamina_cost < 0 or self.heavy_stamina_cost < 0:
            raise ValueError("Weapon stamina costs cannot be negative.")
        if self.combo_window <= 0 or not self.light_combo:
            raise ValueError("A weapon needs a combo and a positive combo window.")


def _light(
    name: str,
    damage: int,
    startup: int,
    active: int,
    recovery: int,
    width: int,
    knockback: float,
    stun: float,
    cooldown: int = 0,
) -> AttackDefinition:
    return AttackDefinition(
        name,
        AttackKind.LIGHT,
        damage,
        startup,
        active,
        recovery,
        48,
        width,
        knockback,
        stun,
        cooldown_frames=cooldown,
    )


def _heavy(
    name: str,
    damage: int,
    startup: int,
    active: int,
    recovery: int,
    width: int,
    stamina: float,
    knockback: float,
    stun: float,
    cooldown: int,
) -> AttackDefinition:
    return AttackDefinition(
        name,
        AttackKind.HEAVY,
        damage,
        startup,
        active,
        recovery,
        56,
        width,
        knockback,
        stun,
        cooldown_frames=cooldown,
        stamina_cost=stamina,
        free_movement=False,
    )


WEAPON_DEFINITIONS: dict[WeaponType, WeaponDefinition] = {
    WeaponType.KATANA: WeaponDefinition(
        weapon_type=WeaponType.KATANA,
        display_name="Katana",
        attack_speed=1.0,
        attack_range=54,
        light_stamina_cost=0.0,
        heavy_stamina_cost=22.0,
        combo_window=0.78,
        light_combo=(
            _light("Quick Cut", 13, 5, 5, 12, 34, 105, 0.12, 5),
            _light("Rising Cut", 16, 6, 5, 13, 38, 135, 0.17, 5),
            _light("Final Cut", 21, 8, 6, 17, 44, 205, 0.24, 8),
        ),
        heavy_attack=_heavy("Heavy Strike", 34, 13, 7, 23, 51, 22.0, 285, 0.38, 20),
        hitbox_shape=HitboxShape.ARC,
        heavy_hitbox_shape=HitboxShape.THRUST,
    ),
    WeaponType.DUAL_BLADES: WeaponDefinition(
        weapon_type=WeaponType.DUAL_BLADES,
        display_name="Dual Blades",
        attack_speed=1.34,
        attack_range=43,
        light_stamina_cost=1.5,
        heavy_stamina_cost=19.0,
        combo_window=0.92,
        light_combo=(
            _light("Twin Flick", 8, 3, 4, 7, 31, 75, 0.08, 3),
            _light("Cross Cut", 10, 4, 4, 8, 37, 95, 0.10, 3),
            _light("Spiral Cut", 12, 4, 5, 9, 43, 125, 0.12, 4),
            _light("Twin Finish", 17, 6, 5, 13, 49, 175, 0.18, 6),
        ),
        heavy_attack=_heavy("Crossing Blades", 29, 9, 6, 19, 53, 19.0, 225, 0.28, 17),
        hitbox_shape=HitboxShape.RECTANGLE,
        heavy_hitbox_shape=HitboxShape.ARC,
    ),
    WeaponType.YARI: WeaponDefinition(
        weapon_type=WeaponType.YARI,
        display_name="Yari",
        attack_speed=0.92,
        attack_range=82,
        light_stamina_cost=2.0,
        heavy_stamina_cost=25.0,
        combo_window=0.72,
        light_combo=(
            _light("Spear Jab", 12, 7, 4, 14, 25, 115, 0.12, 6),
            _light("Shaft Sweep", 16, 8, 5, 15, 55, 155, 0.16, 6),
            _light("Driving Thrust", 24, 10, 5, 20, 28, 225, 0.25, 9),
        ),
        heavy_attack=_heavy("Yari Lunge", 42, 16, 6, 28, 31, 25.0, 310, 0.42, 25),
        hitbox_shape=HitboxShape.THRUST,
        heavy_hitbox_shape=HitboxShape.THRUST,
    ),
    WeaponType.ODACHI: WeaponDefinition(
        weapon_type=WeaponType.ODACHI,
        display_name="Odachi",
        attack_speed=0.72,
        attack_range=68,
        light_stamina_cost=4.0,
        heavy_stamina_cost=32.0,
        combo_window=0.66,
        light_combo=(
            _light("Long Draw", 24, 10, 6, 21, 62, 205, 0.22, 8),
            _light("Falling Cleave", 35, 13, 7, 27, 74, 285, 0.34, 11),
        ),
        heavy_attack=_heavy("Odachi Cleave", 58, 21, 8, 36, 82, 32.0, 390, 0.52, 32),
        hitbox_shape=HitboxShape.WIDE,
        heavy_hitbox_shape=HitboxShape.WIDE,
    ),
}


@dataclass
class WeaponInventory:
    """The player's unlocked weapons and current equipment selection."""

    owned: set[WeaponType] = field(default_factory=lambda: {WeaponType.KATANA})
    equipped: WeaponType = WeaponType.KATANA

    def __post_init__(self) -> None:
        self.owned = {WeaponType(weapon) for weapon in self.owned}
        self.owned.add(WeaponType.KATANA)
        self.equipped = WeaponType(self.equipped)
        if self.equipped not in self.owned:
            self.equipped = WeaponType.KATANA

    @property
    def definition(self) -> WeaponDefinition:
        return WEAPON_DEFINITIONS[self.equipped]

    def acquire(self, weapon: WeaponType | str) -> bool:
        weapon_type = WeaponType(weapon)
        was_owned = weapon_type in self.owned
        self.owned.add(weapon_type)
        return not was_owned

    def equip(self, weapon: WeaponType | str) -> bool:
        weapon_type = WeaponType(weapon)
        if weapon_type not in self.owned:
            return False
        self.equipped = weapon_type
        return True

    def weapon_for_slot(self, slot: int) -> WeaponType | None:
        if not 1 <= slot <= len(WEAPON_ORDER):
            return None
        weapon = WEAPON_ORDER[slot - 1]
        return weapon if weapon in self.owned else None

    def next_owned(self, direction: int) -> WeaponType:
        owned = [weapon for weapon in WEAPON_ORDER if weapon in self.owned]
        current_index = owned.index(self.equipped)
        return owned[(current_index + (1 if direction >= 0 else -1)) % len(owned)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "owned": [weapon.value for weapon in WEAPON_ORDER if weapon in self.owned],
            "equipped": self.equipped.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WeaponInventory:
        raw_owned = data.get("owned", [WeaponType.KATANA.value])
        owned: set[WeaponType] = set()
        if isinstance(raw_owned, list):
            for raw_weapon in raw_owned:
                try:
                    owned.add(WeaponType(raw_weapon))
                except (TypeError, ValueError):
                    continue
        try:
            equipped = WeaponType(data.get("equipped", WeaponType.KATANA.value))
        except (TypeError, ValueError):
            equipped = WeaponType.KATANA
        if equipped not in owned:
            equipped = WeaponType.KATANA
        return cls(owned=owned, equipped=equipped)
