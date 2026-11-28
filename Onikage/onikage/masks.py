"""Five cursed masks, story-gated acquisition, abilities, and persistent state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MaskType(str, Enum):
    WRATH = "wrath"
    GRIEF = "grief"
    FEAR = "fear"
    PRIDE = "pride"
    DECEPTION = "deception"

    # Enum-name aliases keep older integrations source-compatible. Legacy save
    # string values are translated explicitly in MaskManager.from_dict().
    SHADOWS = "grief"
    TENGU = "fear"
    SUFFERING = "pride"
    ONIKAGE = "deception"


class MaskAbilityKind(str, Enum):
    CHARGED_SLASH = "charged_slash"
    SPIRIT_VEIL = "spirit_veil"
    SHADOW_STEP = "shadow_step"
    HEAVENLY_JUDGMENT = "heavenly_judgment"
    PHANTOM_DOUBLE = "phantom_double"

    # Compatibility aliases for code that imported the previous ability names.
    SHADOW_DASH = "shadow_step"
    COUNTER = "heavenly_judgment"
    LIFE_DRAIN = "spirit_veil"
    TRANSFORMATION = "phantom_double"


SHRINE_PROGRESS = "shrine_quest_completed"
WRAITH_PROGRESS = "wraith_defeated"
_MASK_ORDER = tuple(MaskType)
_LEGACY_MASK_IDS = {
    "wrath": MaskType.WRATH,
    "grief": MaskType.GRIEF,
    "fear": MaskType.FEAR,
    "pride": MaskType.PRIDE,
    "deception": MaskType.DECEPTION,
    "shadows": MaskType.GRIEF,
    "tengu": MaskType.FEAR,
    "suffering": MaskType.PRIDE,
    "onikage": MaskType.DECEPTION,
}
_GUARDIAN_FLAGS = {
    MaskType.WRATH: "guardian_defeated:wrath",
    MaskType.GRIEF: "guardian_defeated:grief",
    MaskType.FEAR: "guardian_defeated:fear",
    MaskType.PRIDE: "guardian_defeated:pride",
    MaskType.DECEPTION: "guardian_defeated:deception",
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
    mask_type: MaskType
    display_name: str
    description: str
    region: str
    guardian: str
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
    display_name = "Mask of Wrath"
    description = "Anger becomes flame: charge a devastating inferno-infused strike."
    region = "Burning Village"
    guardian = "Ashen Oni"
    ability = MaskAbility(MaskAbilityKind.CHARGED_SLASH, "Inferno Slash", 42, 11,
                          primary_value=1.45, secondary_value=0.55,
                          minimum_charge=0.35, maximum_charge=1.2)

    def passive_effect(self, level: int) -> PassiveEffect:
        return PassiveEffect(heavy_damage_multiplier=1.10 + 0.04 * (level - 1))

    def ability_values(self, level: int) -> tuple[float, float]:
        return self.ability.primary_value + 0.12 * (level - 1), self.ability.secondary_value + 0.08 * (level - 1)


class GriefMask(CursedMask):
    mask_type = MaskType.GRIEF
    display_name = "Mask of Grief"
    description = "A veil of sorrow briefly shields its bearer from harm."
    region = "Drowned Temple"
    guardian = "Weeping Bride"
    ability = MaskAbility(MaskAbilityKind.SPIRIT_VEIL, "Spirit Veil", 34, 12,
                          duration_seconds=0.9, primary_value=0.9, secondary_value=0.15)

    def passive_effect(self, level: int) -> PassiveEffect:
        return PassiveEffect(energy_regen_bonus=1.0 + 0.35 * (level - 1))

    def ability_values(self, level: int) -> tuple[float, float]:
        return self.ability.primary_value + 0.18 * (level - 1), min(0.45, self.ability.secondary_value + 0.05 * (level - 1))


class FearMask(CursedMask):
    mask_type = MaskType.FEAR
    display_name = "Mask of Fear"
    description = "Move through darkness in a swift, evasive shadow step."
    region = "Whispering Cedar Forest"
    guardian = "Hollow Stalker"
    ability = MaskAbility(MaskAbilityKind.SHADOW_STEP, "Shadow Step", 32, 7.5,
                          duration_seconds=0.25, primary_value=122, secondary_value=0.25)

    def passive_effect(self, level: int) -> PassiveEffect:
        return PassiveEffect(move_speed_multiplier=1.08 + 0.025 * (level - 1), energy_regen_bonus=0.4)

    def ability_values(self, level: int) -> tuple[float, float]:
        return self.ability.primary_value + 18 * (level - 1), self.ability.secondary_value + 0.04 * (level - 1)


class PrideMask(CursedMask):
    mask_type = MaskType.PRIDE
    display_name = "Mask of Pride"
    description = "Meet an enemy's attack and answer with heavenly judgment."
    region = "Fallen Kurogane Castle"
    guardian = "Fallen Shogun"
    ability = MaskAbility(MaskAbilityKind.HEAVENLY_JUDGMENT, "Heavenly Judgment", 30, 9,
                          duration_seconds=0.72, primary_value=0.72, secondary_value=1.55)

    def passive_effect(self, level: int) -> PassiveEffect:
        return PassiveEffect(counter_window_bonus=0.10 + 0.045 * (level - 1))

    def ability_values(self, level: int) -> tuple[float, float]:
        return self.ability.primary_value + 0.10 * (level - 1), self.ability.secondary_value + 0.18 * (level - 1)


class DeceptionMask(CursedMask):
    mask_type = MaskType.DECEPTION
    display_name = "Mask of Deception"
    description = "Create a phantom double to draw hostile attention."
    region = "Realm Between Worlds"
    guardian = "Nameless One"
    ability = MaskAbility(MaskAbilityKind.PHANTOM_DOUBLE, "Phantom Double", 48, 17,
                          duration_seconds=4.5, primary_value=4.5, secondary_value=2.0)

    def passive_effect(self, level: int) -> PassiveEffect:
        return PassiveEffect(energy_regen_bonus=0.7 + 0.25 * (level - 1))

    def ability_values(self, level: int) -> tuple[float, float]:
        return self.ability.primary_value + 0.75 * (level - 1), self.ability.secondary_value + (level - 1)


MASK_CLASSES: dict[MaskType, type[CursedMask]] = {
    MaskType.WRATH: WrathMask,
    MaskType.GRIEF: GriefMask,
    MaskType.FEAR: FearMask,
    MaskType.PRIDE: PrideMask,
    MaskType.DECEPTION: DeceptionMask,
}


def create_mask(mask_type: MaskType | str) -> CursedMask:
    return MASK_CLASSES[MaskType(mask_type)]()


class MaskManager:
    """Owns story-gated mask acquisition, switching, energy, and upgrades."""

    def __init__(self, max_energy: float = 100.0, energy_regen_per_second: float = 7.0,
                 switch_cooldown_seconds: float = 1.2, transition_seconds: float = 0.24) -> None:
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
        return None if selected is None else create_mask(selected)

    def level(self, mask_type: MaskType | None = None) -> int:
        selected = self.equipped if mask_type is None else MaskType(mask_type)
        return 0 if selected is None else self.levels.get(selected, 1)

    def can_acquire(self, mask_type: MaskType | str) -> bool:
        selected = MaskType(mask_type)
        return selected not in self.owned and _GUARDIAN_FLAGS[selected] in self.progression

    def acquire(self, mask_type: MaskType | str) -> bool:
        selected = MaskType(mask_type)
        if not self.can_acquire(selected):
            return False
        self.owned.add(selected)
        self.levels[selected] = 1
        if self.equipped is None:
            self.equipped = selected
        return True

    def defeat_guardian(self, mask_type: MaskType | str) -> bool:
        """Record a guardian victory and award that guardian's corresponding mask."""
        selected = MaskType(mask_type)
        flag = _GUARDIAN_FLAGS[selected]
        if flag in self.progression:
            return False
        self.progression.add(flag)
        self.upgrade_tokens += 1
        return self.acquire(selected)

    def advance_story(self, progression_flag: str) -> tuple[MaskType, ...]:
        """Record village milestones without awarding regional guardian masks."""
        if progression_flag not in (SHRINE_PROGRESS, WRAITH_PROGRESS):
            raise ValueError(f"Unknown mask progression flag: {progression_flag}.")
        if progression_flag in self.progression:
            return ()
        self.progression.add(progression_flag)
        self.upgrade_tokens += 1
        return ()

    def equip(self, mask_type: MaskType | str) -> bool:
        selected = MaskType(mask_type)
        if selected not in self.owned or selected == self.equipped or self.charging or self.switch_cooldown_remaining > 0 or self.transition_remaining > 0:
            return False
        self.equipped = selected
        self.switch_cooldown_remaining = self.switch_cooldown_seconds
        self.transition_remaining = self.transition_seconds
        return True

    def cycle(self, direction: int) -> MaskType | None:
        owned = [mask for mask in _MASK_ORDER if mask in self.owned]
        if len(owned) < 2 or direction == 0:
            return None
        index = owned.index(self.equipped) if self.equipped in owned else 0
        selected = owned[(index + (1 if direction > 0 else -1)) % len(owned)]
        return selected if self.equip(selected) else None

    def grant_upgrade_tokens(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("Upgrade token count cannot be negative.")
        self.upgrade_tokens += count

    def upgrade(self, mask_type: MaskType | None = None) -> bool:
        selected = self.equipped if mask_type is None else MaskType(mask_type)
        if selected is None or selected not in self.owned or self.upgrade_tokens <= 0:
            return False
        level = self.levels.get(selected, 1)
        if level >= create_mask(selected).max_upgrade_level:
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
        mask = self.mask()
        regen = self.energy_regen_per_second + (mask.passive_effect(self.level()).energy_regen_bonus if mask else 0.0)
        self.energy = min(self.max_energy, self.energy + regen * dt)
        if self.charging:
            self.charge_elapsed = min(3.0, self.charge_elapsed + dt)

    def can_activate(self) -> bool:
        mask = self.mask()
        return bool(mask and self.equipped in self.owned and not self.charging
                    and self.transition_remaining <= 0 and self.cooldowns[self.equipped] <= 0
                    and self.energy >= mask.energy_cost(self.level()))

    def activate(self) -> CursedMask | None:
        mask = self.mask()
        if mask is None or mask.ability.kind == MaskAbilityKind.CHARGED_SLASH or not self.can_activate():
            return None
        selected = self.equipped
        assert selected is not None
        self.energy -= mask.energy_cost(self.level(selected))
        self.cooldowns[selected] = mask.cooldown(self.level(selected))
        return mask

    def begin_charge(self) -> bool:
        mask = self.mask()
        if mask is None or mask.ability.kind != MaskAbilityKind.CHARGED_SLASH or not self.can_activate():
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
        selected = self.equipped
        assert selected is not None
        level = self.level(selected)
        fraction = min(1.0, charge / mask.ability.maximum_charge)
        cost = mask.energy_cost(level) * (0.72 + 0.28 * fraction)
        if self.energy < cost:
            return None
        self.energy -= cost
        self.cooldowns[selected] = mask.cooldown(level)
        return fraction

    def cancel_charge(self) -> None:
        self.charging = False
        self.charge_elapsed = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"owned": [mask.value for mask in _MASK_ORDER if mask in self.owned],
                "equipped": self.equipped.value if self.equipped else None,
                "levels": {mask.value: self.levels.get(mask, 1) for mask in self.owned},
                "progression": sorted(self.progression), "upgrade_tokens": self.upgrade_tokens,
                "energy": self.energy}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MaskManager:
        manager = cls()
        raw_progression = data.get("progression", [])
        if isinstance(raw_progression, list):
            manager.progression = {flag for flag in raw_progression if isinstance(flag, str)}
        raw_owned = data.get("owned", [])
        levels = data.get("levels", {})
        if not isinstance(levels, dict):
            levels = {}
        migrated_levels: dict[MaskType, int] = {}
        if isinstance(levels, dict):
            for raw_id, raw_level in levels.items():
                selected = _LEGACY_MASK_IDS.get(raw_id)
                if selected is not None:
                    try:
                        migrated_levels[selected] = max(1, min(3, int(raw_level)))
                    except (TypeError, ValueError):
                        migrated_levels[selected] = 1
        if isinstance(raw_owned, list):
            for raw_mask in raw_owned:
                selected = _LEGACY_MASK_IDS.get(raw_mask) if isinstance(raw_mask, str) else None
                if selected is None:
                    try:
                        selected = MaskType(raw_mask)
                    except (TypeError, ValueError):
                        continue
                # Existing ownership is grandfathered during migration; new
                # acquisitions remain guardian-gated through can_acquire().
                manager.owned.add(selected)
                manager.levels[selected] = migrated_levels.get(selected, 1)
        equipped_raw = data.get("equipped")
        equipped = _LEGACY_MASK_IDS.get(equipped_raw) if isinstance(equipped_raw, str) else None
        if equipped is None:
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
