"""Cursed mask definitions, progression gates, abilities, and persistent state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MaskType(str, Enum):
    WRATH = "wrath"
    SHADOWS = "shadows"
    TENGU = "tengu"
    SUFFERING = "suffering"
    ONIKAGE = "onikage"


class MaskAbilityKind(str, Enum):
    CHARGED_SLASH = "charged_slash"
    SHADOW_DASH = "shadow_dash"
    COUNTER = "counter"
    LIFE_DRAIN = "life_drain"
    TRANSFORMATION = "transformation"


SHRINE_PROGRESS = "shrine_quest_completed"
WRAITH_PROGRESS = "wraith_defeated"
_MASK_ORDER = tuple(MaskType)
_LESSER_MASKS = {
    MaskType.WRATH,
    MaskType.SHADOWS,
    MaskType.TENGU,
    MaskType.SUFFERING,
}
_REQUIREMENTS = {
    MaskType.WRATH: {WRAITH_PROGRESS},
    MaskType.SHADOWS: {SHRINE_PROGRESS},
    MaskType.TENGU: {SHRINE_PROGRESS},
    MaskType.SUFFERING: {SHRINE_PROGRESS, WRAITH_PROGRESS},
    MaskType.ONIKAGE: {SHRINE_PROGRESS, WRAITH_PROGRESS},
}


@dataclass(frozen=True)
class PassiveEffect:
    damage_multiplier: float = 1.0
    heavy_damage_multiplier: float = 1.0
    move_speed_multiplier: float = 1.0
    energy_regen_bonus: float = 0.0
    counter_window_bonus: float = 0.0
    passive_lifesteal: float = 0.0


@dataclass(frozen=True)
class MaskAbility:
    kind: MaskAbilityKind
    name: str
    energy_cost: float
    cooldown_seconds: float
    duration_seconds: float = 0.0
    primary_value: float = 0.0
    secondary_value: float = 0.0
    minimum_charge: float = 0.0
    maximum_charge: float = 0.0


class CursedMask:
    """Base class for mask identity, passive bonuses, ability tuning, and upgrades."""

    mask_type: MaskType
    display_name: str
    description: str
    ability: MaskAbility
    max_upgrade_level = 3

    def energy_cost(self, level: int) -> float:
        return max(5.0, self.ability.energy_cost * (1.0 - 0.06 * (level - 1)))

    def cooldown(self, level: int) -> float:
        return max(1.0, self.ability.cooldown_seconds - 0.5 * (level - 1))

    def passive_effect(self, level: int) -> PassiveEffect:
        return PassiveEffect()

    def ability_values(self, level: int) -> tuple[float, float]:
        return self.ability.primary_value, self.ability.secondary_value


class WrathMask(CursedMask):
    mask_type = MaskType.WRATH
    display_name = "Wrath"
    description = "The old warrior's fury sharpens heavy weapon blows."
    ability = MaskAbility(
        MaskAbilityKind.CHARGED_SLASH,
        "Devastating Slash",
        42,
        11,
        primary_value=1.35,
        secondary_value=0.50,
        minimum_charge=0.35,
        maximum_charge=1.2,
    )

    def passive_effect(self, level: int) -> PassiveEffect:
        return PassiveEffect(heavy_damage_multiplier=1.10 + 0.04 * (level - 1))

    def ability_values(self, level: int) -> tuple[float, float]:
        return self.ability.primary_value + 0.12 * (level - 1), self.ability.secondary_value + 0.08 * (level - 1)


class ShadowsMask(CursedMask):
    mask_type = MaskType.SHADOWS
    display_name = "Shadows"
    description = "A quiet veil quickens movement and restores mask energy."
    ability = MaskAbility(
        MaskAbilityKind.SHADOW_DASH,
        "Shadow Dash",
        32,
        7.5,
        duration_seconds=0.22,
        primary_value=122,
        secondary_value=0.22,
    )

    def passive_effect(self, level: int) -> PassiveEffect:
        return PassiveEffect(
            move_speed_multiplier=1.10 + 0.025 * (level - 1),
            energy_regen_bonus=1.2 + 0.4 * (level - 1),
        )

    def ability_values(self, level: int) -> tuple[float, float]:
        return self.ability.primary_value + 18 * (level - 1), self.ability.secondary_value + 0.04 * (level - 1)


class TenguMask(CursedMask):
    mask_type = MaskType.TENGU
    display_name = "Tengu"
    description = "A watchful spirit makes a timed counter more forgiving."
    ability = MaskAbility(
        MaskAbilityKind.COUNTER,
        "Tengu Counter",
        28,
        8.5,
        duration_seconds=0.68,
        primary_value=0.68,
        secondary_value=1.22,
    )

    def passive_effect(self, level: int) -> PassiveEffect:
        return PassiveEffect(counter_window_bonus=0.12 + 0.04 * (level - 1))

    def ability_values(self, level: int) -> tuple[float, float]:
        return self.ability.primary_value + 0.10 * (level - 1), self.ability.secondary_value + 0.12 * (level - 1)


class SufferingMask(CursedMask):
    mask_type = MaskType.SUFFERING
    display_name = "Suffering"
    description = "A hungry spirit returns a little vitality with each weapon hit."
    ability = MaskAbility(
        MaskAbilityKind.LIFE_DRAIN,
        "Life-Draining Strike",
        38,
        9.5,
        duration_seconds=3.0,
        primary_value=1.25,
        secondary_value=0.52,
    )

    def passive_effect(self, level: int) -> PassiveEffect:
        return PassiveEffect(passive_lifesteal=0.045 + 0.015 * (level - 1))

    def ability_values(self, level: int) -> tuple[float, float]:
        return self.ability.primary_value + 0.12 * (level - 1), min(0.78, self.ability.secondary_value + 0.06 * (level - 1))


class OnikageMask(CursedMask):
    mask_type = MaskType.ONIKAGE
    display_name = "Onikage"
    description = "The shadow of the fallen samurai briefly amplifies weapon strikes."
    ability = MaskAbility(
        MaskAbilityKind.TRANSFORMATION,
        "Onikage Transformation",
        58,
        18.0,
        duration_seconds=6.0,
        primary_value=1.22,
        secondary_value=1.10,
    )

    def passive_effect(self, level: int) -> PassiveEffect:
        return PassiveEffect(energy_regen_bonus=0.8 + 0.3 * (level - 1))

    def ability_values(self, level: int) -> tuple[float, float]:
        return self.ability.duration_seconds + 1.0 * (level - 1), self.ability.primary_value + 0.06 * (level - 1)


MASK_CLASSES: dict[MaskType, type[CursedMask]] = {
    MaskType.WRATH: WrathMask,
    MaskType.SHADOWS: ShadowsMask,
    MaskType.TENGU: TenguMask,
    MaskType.SUFFERING: SufferingMask,
    MaskType.ONIKAGE: OnikageMask,
}


def create_mask(mask_type: MaskType) -> CursedMask:
    return MASK_CLASSES[MaskType(mask_type)]()


class MaskManager:
    """Owns mask progression, switching, energy, cooldowns, and upgrade levels."""

    def __init__(
        self,
        max_energy: float = 100.0,
        energy_regen_per_second: float = 7.0,
        switch_cooldown_seconds: float = 1.2,
        transition_seconds: float = 0.24,
    ) -> None:
        if max_energy <= 0 or energy_regen_per_second < 0:
            raise ValueError("Mask energy settings are invalid.")
        if switch_cooldown_seconds < 0 or transition_seconds < 0:
            raise ValueError("Mask switching timings cannot be negative.")
        self.owned: set[MaskType] = set()
        self.equipped: MaskType | None = None
        self.levels: dict[MaskType, int] = {}
        self.progression: set[str] = set()
        self.upgrade_tokens = 0
        self.max_energy = max_energy
        self.energy = max_energy
        self.energy_regen_per_second = energy_regen_per_second
        self.switch_cooldown_seconds = switch_cooldown_seconds
        self.transition_seconds = transition_seconds
        self.switch_cooldown_remaining = 0.0
        self.transition_remaining = 0.0
        self.cooldowns: dict[MaskType, float] = {mask_type: 0.0 for mask_type in _MASK_ORDER}
        self.charging = False
        self.charge_elapsed = 0.0

    def mask(self, mask_type: MaskType | None = None) -> CursedMask | None:
        selected = self.equipped if mask_type is None else MaskType(mask_type)
        if selected is None:
            return None
        return create_mask(selected)

    def level(self, mask_type: MaskType | None = None) -> int:
        selected = self.equipped if mask_type is None else MaskType(mask_type)
        return 0 if selected is None else self.levels.get(selected, 1)

    def can_acquire(self, mask_type: MaskType | str) -> bool:
        selected = MaskType(mask_type)
        if selected in self.owned or not _REQUIREMENTS[selected].issubset(self.progression):
            return False
        if selected == MaskType.ONIKAGE:
            return _LESSER_MASKS.issubset(self.owned)
        return True

    def acquire(self, mask_type: MaskType | str) -> bool:
        selected = MaskType(mask_type)
        if not self.can_acquire(selected):
            return False
        self.owned.add(selected)
        self.levels[selected] = 1
        if self.equipped is None:
            self.equipped = selected
        self._try_unlock_onikage()
        return True

    def advance_story(self, progression_flag: str) -> tuple[MaskType, ...]:
        if progression_flag not in (SHRINE_PROGRESS, WRAITH_PROGRESS):
            raise ValueError(f"Unknown mask progression flag: {progression_flag}.")
        if progression_flag in self.progression:
            return ()
        self.progression.add(progression_flag)
        self.upgrade_tokens += 1
        rewarded: list[MaskType] = []
        for mask_type in (MaskType.SHADOWS, MaskType.WRATH):
            if self.can_acquire(mask_type) and self.acquire(mask_type):
                rewarded.append(mask_type)
        return tuple(rewarded)

    def _try_unlock_onikage(self) -> None:
        if self.can_acquire(MaskType.ONIKAGE):
            self.acquire(MaskType.ONIKAGE)

    def equip(self, mask_type: MaskType | str) -> bool:
        selected = MaskType(mask_type)
        if (
            selected not in self.owned
            or selected == self.equipped
            or self.charging
            or self.switch_cooldown_remaining > 0
            or self.transition_remaining > 0
        ):
            return False
        self.equipped = selected
        self.switch_cooldown_remaining = self.switch_cooldown_seconds
        self.transition_remaining = self.transition_seconds
        return True

    def cycle(self, direction: int) -> MaskType | None:
        owned = [mask_type for mask_type in _MASK_ORDER if mask_type in self.owned]
        if len(owned) < 2 or direction == 0:
            return None
        current_index = owned.index(self.equipped) if self.equipped in owned else 0
        selected = owned[(current_index + (1 if direction > 0 else -1)) % len(owned)]
        return selected if self.equip(selected) else None

    def grant_upgrade_tokens(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("Upgrade token count cannot be negative.")
        self.upgrade_tokens += count

    def upgrade(self, mask_type: MaskType | None = None) -> bool:
        selected = self.equipped if mask_type is None else MaskType(mask_type)
        if selected is None or selected not in self.owned or self.upgrade_tokens <= 0:
            return False
        mask = create_mask(selected)
        level = self.levels.get(selected, 1)
        if level >= mask.max_upgrade_level:
            return False
        self.levels[selected] = level + 1
        self.upgrade_tokens -= 1
        return True

    def update(self, dt: float) -> None:
        dt = max(0.0, dt)
        self.switch_cooldown_remaining = max(0.0, self.switch_cooldown_remaining - dt)
        self.transition_remaining = max(0.0, self.transition_remaining - dt)
        for mask_type in _MASK_ORDER:
            self.cooldowns[mask_type] = max(0.0, self.cooldowns[mask_type] - dt)
        regen = self.energy_regen_per_second
        mask = self.mask()
        if mask is not None:
            regen += mask.passive_effect(self.level()).energy_regen_bonus
        self.energy = min(self.max_energy, self.energy + regen * dt)
        if self.charging:
            self.charge_elapsed = min(3.0, self.charge_elapsed + dt)

    def can_activate(self) -> bool:
        mask = self.mask()
        return bool(
            mask is not None
            and self.equipped in self.owned
            and not self.charging
            and self.transition_remaining <= 0
            and self.cooldowns[self.equipped] <= 0
            and self.energy >= mask.energy_cost(self.level())
        )

    def activate(self) -> CursedMask | None:
        mask = self.mask()
        if mask is None or mask.ability.kind == MaskAbilityKind.CHARGED_SLASH or not self.can_activate():
            return None
        mask_type = self.equipped
        assert mask_type is not None
        self.energy -= mask.energy_cost(self.level(mask_type))
        self.cooldowns[mask_type] = mask.cooldown(self.level(mask_type))
        return mask

    def begin_charge(self) -> bool:
        mask = self.mask()
        if (
            mask is None
            or mask.ability.kind != MaskAbilityKind.CHARGED_SLASH
            or not self.can_activate()
        ):
            return False
        self.charging = True
        self.charge_elapsed = 0.0
        return True

    def release_charge(self) -> float | None:
        mask = self.mask()
        if mask is None or not self.charging:
            return None
        self.charging = False
        charge = self.charge_elapsed
        self.charge_elapsed = 0.0
        if charge < mask.ability.minimum_charge:
            return None
        mask_type = self.equipped
        assert mask_type is not None
        level = self.level(mask_type)
        fraction = min(1.0, charge / mask.ability.maximum_charge)
        cost = mask.energy_cost(level) * (0.72 + 0.28 * fraction)
        if self.energy < cost:
            return None
        self.energy -= cost
        self.cooldowns[mask_type] = mask.cooldown(level)
        return fraction

    def cancel_charge(self) -> None:
        self.charging = False
        self.charge_elapsed = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "owned": [mask.value for mask in _MASK_ORDER if mask in self.owned],
            "equipped": self.equipped.value if self.equipped else None,
            "levels": {mask.value: self.levels.get(mask, 1) for mask in self.owned},
            "progression": sorted(self.progression),
            "upgrade_tokens": self.upgrade_tokens,
            "energy": self.energy,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MaskManager:
        manager = cls()
        raw_progression = data.get("progression", [])
        if isinstance(raw_progression, list):
            manager.progression = {
                flag
                for flag in raw_progression
                if isinstance(flag, str) and flag in (SHRINE_PROGRESS, WRAITH_PROGRESS)
            }
        raw_owned = data.get("owned", [])
        levels = data.get("levels", {})
        if not isinstance(levels, dict):
            levels = {}
        if isinstance(raw_owned, list):
            for raw_mask in raw_owned:
                try:
                    mask_type = MaskType(raw_mask)
                except (TypeError, ValueError):
                    continue
                if not _REQUIREMENTS[mask_type].issubset(manager.progression):
                    continue
                if mask_type == MaskType.ONIKAGE and not _LESSER_MASKS.issubset(manager.owned):
                    continue
                manager.owned.add(mask_type)
                try:
                    manager.levels[mask_type] = max(1, min(3, int(levels.get(mask_type.value, 1))))
                except (TypeError, ValueError):
                    manager.levels[mask_type] = 1
        equipped_raw = data.get("equipped")
        try:
            equipped = MaskType(equipped_raw)
        except (TypeError, ValueError):
            equipped = None
        manager.equipped = equipped if equipped in manager.owned else None
        try:
            manager.upgrade_tokens = max(0, int(data.get("upgrade_tokens", 0)))
            manager.energy = max(0.0, min(manager.max_energy, float(data.get("energy", manager.max_energy))))
        except (TypeError, ValueError):
            manager.upgrade_tokens = 0
            manager.energy = manager.max_energy
        return manager


def all_mask_types() -> tuple[MaskType, ...]:
    return _MASK_ORDER
