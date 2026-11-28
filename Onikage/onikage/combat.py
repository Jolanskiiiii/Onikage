"""Composable real-time melee combat primitives and encounter simulation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from typing import TYPE_CHECKING, Protocol

import pygame

from onikage.directions import DIRECTION_VECTORS, direction_name
from onikage.masks import MaskAbilityKind, MaskManager, MaskType

if TYPE_CHECKING:
    from onikage.masks import MaskManager as MaskManagerType
    from onikage.weapons import WeaponInventory, WeaponType


class Health:
    """Clamped health pool shared by player and enemy combatants."""

    def __init__(self, maximum: int, current: int | None = None) -> None:
        if maximum <= 0:
            raise ValueError("Maximum health must be positive.")
        self.maximum = maximum
        self.current = maximum if current is None else max(0, min(maximum, current))

    def apply_damage(self, damage: int) -> int:
        if damage < 0:
            raise ValueError("Damage cannot be negative.")
        applied = min(self.current, damage)
        self.current -= applied
        return applied

    def heal(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("Healing cannot be negative.")
        restored = min(self.maximum - self.current, amount)
        self.current += restored
        return restored


@dataclass(frozen=True)
class Damage:
    amount: int
    knockback: float = 0.0
    stun_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.amount < 0 or self.knockback < 0 or self.stun_seconds < 0:
            raise ValueError("Damage and reaction values cannot be negative.")


class HitboxShape(Enum):
    RECTANGLE = auto()
    WIDE = auto()
    THRUST = auto()
    ARC = auto()


@dataclass
class Hurtbox:
    rect: pygame.Rect


@dataclass
class Hitbox:
    """An active attack area that records targets already struck."""

    rect: pygame.Rect
    damage: Damage
    can_hit_multiple_times: bool = False
    shape: HitboxShape = HitboxShape.RECTANGLE
    hit_targets: set[int] = field(default_factory=set)

    def try_hit(self, target: Hurtbox, target_identity: object) -> bool:
        identity = id(target_identity)
        if not self.rect.colliderect(target.rect):
            return False
        if not self.can_hit_multiple_times and identity in self.hit_targets:
            return False
        self.hit_targets.add(identity)
        return True


class CombatState(Enum):
    IDLE = auto()
    STARTUP = auto()
    ACTIVE = auto()
    RECOVERY = auto()
    STUNNED = auto()


class AttackKind(Enum):
    LIGHT = auto()
    HEAVY = auto()
    ENEMY = auto()
    MASK = auto()


@dataclass(frozen=True)
class AttackDefinition:
    name: str
    kind: AttackKind
    damage: int
    startup_frames: int
    active_frames: int
    recovery_frames: int
    reach: int
    width: int
    knockback: float
    stun_seconds: float
    cooldown_frames: int = 0
    stamina_cost: float = 0.0
    free_movement: bool = True
    can_hit_multiple_times: bool = False
    hitbox_shape: HitboxShape = HitboxShape.RECTANGLE

    def __post_init__(self) -> None:
        if min(self.startup_frames, self.active_frames, self.recovery_frames) < 0:
            raise ValueError("Attack frame counts cannot be negative.")
        if self.active_frames == 0:
            raise ValueError("An attack must have at least one active frame.")


@dataclass
class AttackInstance:
    definition: AttackDefinition
    direction: str
    elapsed_frames: float = 0.0
    speed_multiplier: float = 1.0
    hitbox: Hitbox | None = None

    @property
    def state(self) -> CombatState:
        frame = self.elapsed_frames
        if frame < self.definition.startup_frames:
            return CombatState.STARTUP
        if frame < self.definition.startup_frames + self.definition.active_frames:
            return CombatState.ACTIVE
        if frame < self.total_frames:
            return CombatState.RECOVERY
        return CombatState.IDLE

    @property
    def total_frames(self) -> int:
        return (
            self.definition.startup_frames
            + self.definition.active_frames
            + self.definition.recovery_frames
        )

    @property
    def finished(self) -> bool:
        return self.elapsed_frames >= self.total_frames

    def advance(self, dt: float, frames_per_second: int = 60) -> None:
        self.elapsed_frames = min(
            float(self.total_frames),
            self.elapsed_frames
            + max(0.0, dt) * frames_per_second * max(0.01, self.speed_multiplier),
        )


@dataclass
class CombatantState:
    state: CombatState = CombatState.IDLE
    stun_remaining: float = 0.0
    invulnerability_remaining: float = 0.0
    knockback_velocity: pygame.Vector2 = field(default_factory=pygame.Vector2)
    hit_reaction_remaining: float = 0.0

    def receive(self, damage: Damage, direction: pygame.Vector2) -> None:
        self.stun_remaining = max(self.stun_remaining, damage.stun_seconds)
        self.hit_reaction_remaining = max(self.hit_reaction_remaining, 0.16)
        if direction.length_squared() > 0 and damage.knockback:
            self.knockback_velocity = direction.normalize() * damage.knockback
        if damage.stun_seconds:
            self.state = CombatState.STUNNED


@dataclass
class PhantomDecoy:
    """Temporary illusion target that can absorb enemy attacks."""

    rect: pygame.Rect
    vitality: Health
    remaining: float

    @property
    def health(self) -> int:
        return self.vitality.current

    @property
    def max_health(self) -> int:
        return self.vitality.maximum


class Combatant(Protocol):
    rect: pygame.Rect
    health: int
    max_health: int
    vitality: Health


class PlayerCombatant(Combatant, Protocol):
    stamina: float
    direction: str
    weapon_inventory: WeaponInventory
    mask_manager: MaskManagerType


class ComboTracker:
    """Tracks a three-step light chain using a configurable input window."""

    def __init__(self, max_steps: int = 3, combo_window: float = 0.78) -> None:
        if max_steps < 1 or combo_window <= 0:
            raise ValueError("Combo steps and timing window must be positive.")
        self.max_steps = max_steps
        self.combo_window = combo_window
        self.step = 0
        self.last_attack_time: float | None = None

    def next_step(self, now: float) -> int:
        if self.last_attack_time is None or now - self.last_attack_time > self.combo_window:
            self.step = 0
        self.step = self.step % self.max_steps + 1
        self.last_attack_time = now
        return self.step

    def reset(self) -> None:
        self.step = 0
        self.last_attack_time = None


ENEMY_ATTACK = AttackDefinition(
    "Wraith Claw", AttackKind.ENEMY, 12, 23, 6, 37, 58, 42, 190, 0.28,
    cooldown_frames=22, free_movement=False,
)

# The Ashen Oni is a regional guardian, not a renamed ordinary Wraith. Its
# second phase starts below half health and uses a quicker, wider flame sweep.
ASHEN_ONI_ATTACK = AttackDefinition(
    "Cinder Cleave", AttackKind.ENEMY, 17, 27, 8, 35, 76, 54, 245, 0.34,
    cooldown_frames=26, free_movement=False,
)
ASHEN_ONI_ENRAGED_ATTACK = AttackDefinition(
    "Infernal Sweep", AttackKind.ENEMY, 23, 17, 11, 27, 104, 78, 315, 0.48,
    cooldown_frames=16, free_movement=False,
)


_TOP_DOWN_DIRECTION_VECTORS = DIRECTION_VECTORS
_ATTACK_SPACE_VECTORS = DIRECTION_VECTORS


def top_down_attack_direction(
    origin: pygame.Vector2 | tuple[float, float],
    aim_point: pygame.Vector2 | tuple[float, float],
) -> str:
    """Convert a mouse position directly into a top-down screen direction."""
    delta = pygame.Vector2(aim_point) - pygame.Vector2(origin)
    if delta.length_squared() == 0:
        return "down"
    return direction_name(delta.x, delta.y)


def make_hitbox(
    attacker_rect: pygame.Rect,
    direction: str,
    definition: AttackDefinition,
) -> Hitbox:
    """Build the forward-facing melee box used during an attack's active frames."""
    vector = _ATTACK_SPACE_VECTORS.get(direction, _ATTACK_SPACE_VECTORS["down"])
    center = pygame.Vector2(attacker_rect.center) + vector * (
        max(attacker_rect.size) / 2 + definition.reach * 0.6
    )
    reach = float(definition.reach)
    breadth = float(definition.width)
    if definition.hitbox_shape == HitboxShape.WIDE:
        breadth *= 1.65
    elif definition.hitbox_shape == HitboxShape.THRUST:
        reach *= 1.2
        breadth = max(14.0, breadth * 0.55)
    elif definition.hitbox_shape == HitboxShape.ARC:
        reach *= 1.08
        breadth = max(breadth, reach * 0.9)

    if abs(vector.x) > 0.2 and abs(vector.y) > 0.2:
        width = max(breadth, reach * 0.82)
        height = width
    elif abs(vector.x) >= abs(vector.y):
        width, height = reach, breadth
    else:
        width, height = breadth, reach
    rect = pygame.Rect(0, 0, round(width), round(height))
    rect.center = (round(center.x), round(center.y))
    return Hitbox(
        rect,
        Damage(definition.damage, definition.knockback, definition.stun_seconds),
        definition.can_hit_multiple_times,
        definition.hitbox_shape,
    )


@dataclass
class TargetAssist:
    enabled: bool = True
    radius: float = 132.0
    cone_degrees: float = 52.0

    def direction_for(
        self,
        aimed_direction: str,
        origin: pygame.Vector2,
        target: pygame.Vector2,
    ) -> str:
        if not self.enabled:
            return aimed_direction
        screen_delta = target - origin
        if screen_delta.length_squared() == 0 or screen_delta.length() > self.radius:
            return aimed_direction
        to_target = screen_delta
        aim = _TOP_DOWN_DIRECTION_VECTORS.get(
            aimed_direction,
            _TOP_DOWN_DIRECTION_VECTORS["down"],
        )
        if aim.normalize().dot(to_target.normalize()) < math.cos(math.radians(self.cone_degrees)):
            return aimed_direction
        return direction_name(to_target.x, to_target.y)


class RealtimeCombat:
    """Real-time player-versus-enemy encounter, updated alongside exploration."""

    FRAMES_PER_SECOND = 60
    ENEMY_ENGAGE_RANGE = 104.0
    HIT_STOP_SECONDS = 0.055

    def __init__(
        self,
        player: PlayerCombatant,
        enemy: Combatant,
        target_assist: TargetAssist | None = None,
    ) -> None:
        self.player = player
        self.enemy = enemy
        self.player_state = CombatantState()
        self.enemy_state = CombatantState()
        self.player_attack: AttackInstance | None = None
        self.enemy_attack: AttackInstance | None = None
        self.mask_manager = player.mask_manager
        self.weapon_inventory = player.weapon_inventory
        self.combo = ComboTracker(
            max_steps=len(self.weapon_inventory.definition.light_combo),
            combo_window=self.weapon_inventory.definition.combo_window,
        )
        self.target_assist = target_assist or TargetAssist()
        self.elapsed = 0.0
        self.hit_stop_remaining = 0.0
        self.hit_stop_active = False
        self.counter_remaining = 0.0
        self.counter_damage_multiplier = 1.0
        self.transformation_remaining = 0.0
        self.transformation_damage_multiplier = 1.0
        self.transformation_speed_multiplier = 1.0
        self.spirit_veil_remaining = 0.0
        self.phantom_decoy: PhantomDecoy | None = None
        self.phantom_decoy_state = CombatantState()
        self.mask_effect_remaining = 0.0
        self.dash_trail_remaining = 0.0
        self.dash_origin: pygame.Vector2 | None = None
        self.dash_target: pygame.Vector2 | None = None
        self.player_cooldown = 0.0
        self.enemy_cooldown = 27.0
        self.enemy_phase = 1
        self.message = f"A {enemy.name} blocks the way."
        self.finished = False
        self.result: str | None = None
        self.experience_awarded = False

    @property
    def movement_locked(self) -> bool:
        if self.player_state.state == CombatState.STUNNED:
            return True
        return (
            self.player_attack is not None
            and self.player_attack.state == CombatState.ACTIVE
            and not self.player_attack.definition.free_movement
        )

    @property
    def visible_hitbox(self) -> pygame.Rect | None:
        if self.player_attack is not None and self.player_attack.state == CombatState.ACTIVE:
            return self.player_attack.hitbox.rect if self.player_attack.hitbox else None
        return None

    @property
    def weapon(self):
        return self.weapon_inventory.definition

    @property
    def transformation_active(self) -> bool:
        return self.transformation_remaining > 0

    def switch_weapon(self, weapon: WeaponType | str) -> bool:
        """Equip an owned weapon only between attacks; cooldown time is retained."""
        if (
            self.finished
            or self.player_attack is not None
            or self.player_state.stun_remaining > 0
            or not self.weapon_inventory.equip(weapon)
        ):
            return False
        definition = self.weapon_inventory.definition
        self.combo = ComboTracker(
            max_steps=len(definition.light_combo),
            combo_window=definition.combo_window,
        )
        return True

    def switch_mask(self, mask_type: MaskType | str) -> bool:
        if self.finished or self.player_attack is not None or self.mask_manager.charging:
            return False
        return self.mask_manager.equip(mask_type)

    def cycle_mask(self, direction: int) -> MaskType | None:
        if self.finished or self.player_attack is not None or self.mask_manager.charging:
            return None
        return self.mask_manager.cycle(direction)

    def start_light(self, aim_point: pygame.Vector2 | tuple[float, float]) -> bool:
        if (
            self.finished
            or self.player_attack is not None
            or self.player_cooldown > 0
            or self.player_state.stun_remaining > 0
            or self.mask_manager.transition_remaining > 0
            or self.mask_manager.charging
        ):
            return False
        weapon = self.weapon
        if self.player.stamina < weapon.light_stamina_cost:
            self.message = f"Not enough stamina for {weapon.display_name}."
            return False
        self.player.stamina -= weapon.light_stamina_cost
        step = self.combo.next_step(self.elapsed)
        base_attack = weapon.light_combo[step - 1]
        mask = self.mask_manager.mask()
        passive = mask.passive_effect(self.mask_manager.level()) if mask else None
        damage_multiplier = passive.damage_multiplier if passive else 1.0
        damage_multiplier *= self.transformation_damage_multiplier
        definition = replace(
            base_attack,
            damage=max(1, round(base_attack.damage * damage_multiplier)),
            reach=weapon.attack_range,
            stamina_cost=weapon.light_stamina_cost,
            hitbox_shape=weapon.hitbox_shape,
        )
        direction = self._aim_direction(aim_point)
        self.player_attack = AttackInstance(
            definition,
            direction,
            speed_multiplier=weapon.attack_speed * self.transformation_speed_multiplier,
        )
        self.message = f"{definition.name} — combo {step}/3."
        return True

    def start_heavy(self, aim_point: pygame.Vector2 | tuple[float, float]) -> bool:
        if (
            self.finished
            or self.player_attack is not None
            or self.player_cooldown > 0
            or self.player_state.stun_remaining > 0
            or self.mask_manager.transition_remaining > 0
            or self.mask_manager.charging
        ):
            return False
        weapon = self.weapon
        if self.player.stamina < weapon.heavy_stamina_cost:
            self.message = "Not enough stamina for a heavy strike."
            return False
        self.player.stamina -= weapon.heavy_stamina_cost
        mask = self.mask_manager.mask()
        passive = mask.passive_effect(self.mask_manager.level()) if mask else None
        damage_multiplier = passive.heavy_damage_multiplier if passive else 1.0
        damage_multiplier *= self.transformation_damage_multiplier
        definition = replace(
            weapon.heavy_attack,
            damage=max(1, round(weapon.heavy_attack.damage * damage_multiplier)),
            reach=round(weapon.attack_range * 1.12),
            stamina_cost=weapon.heavy_stamina_cost,
            hitbox_shape=weapon.heavy_hitbox_shape,
        )
        self.player_attack = AttackInstance(
            definition,
            self._aim_direction(aim_point),
            speed_multiplier=weapon.attack_speed * self.transformation_speed_multiplier,
        )
        self.message = "You commit to a heavy strike."
        return True

    def _aim_direction(self, aim_point: pygame.Vector2 | tuple[float, float]) -> str:
        origin = pygame.Vector2(self.player.rect.centerx, self.player.rect.bottom)
        direction = top_down_attack_direction(origin, aim_point)
        direction = self.target_assist.direction_for(
            direction,
            origin,
            pygame.Vector2(self.enemy.rect.center),
        )
        self.player.direction = direction
        return direction

    def begin_mask_charge(self) -> bool:
        mask = self.mask_manager.mask()
        if (
            self.finished
            or self.player_attack is not None
            or self.player_state.stun_remaining > 0
            or self.mask_manager.transition_remaining > 0
            or mask is None
            or mask.ability.kind != MaskAbilityKind.CHARGED_SLASH
        ):
            return False
        started = self.mask_manager.begin_charge()
        if started:
            self.message = "Hold Q to charge the Wrath slash; release to strike."
        return started

    def release_mask_charge(
        self,
        aim_point: pygame.Vector2 | tuple[float, float],
    ) -> bool:
        mask = self.mask_manager.mask()
        if (
            self.finished
            or self.player_state.stun_remaining > 0
            or self.mask_manager.transition_remaining > 0
            or mask is None
            or mask.ability.kind != MaskAbilityKind.CHARGED_SLASH
        ):
            self.mask_manager.cancel_charge()
            return False
        charge = self.mask_manager.release_charge()
        if charge is None:
            self.message = "The Wrath charge was too short or lacked energy."
            return False
        weapon = self.weapon
        level = self.mask_manager.level()
        base_multiplier, charge_bonus = mask.ability_values(level)
        passive = mask.passive_effect(level)
        damage = round(
            weapon.heavy_attack.damage
            * (base_multiplier + charge_bonus * charge)
            * passive.heavy_damage_multiplier
            * self.transformation_damage_multiplier
        )
        definition = replace(
            weapon.heavy_attack,
            name=mask.ability.name,
            kind=AttackKind.MASK,
            damage=max(1, damage),
            startup_frames=max(5, weapon.heavy_attack.startup_frames - 4),
            active_frames=max(5, weapon.heavy_attack.active_frames),
            recovery_frames=weapon.heavy_attack.recovery_frames + 6,
            reach=round(weapon.attack_range * (1.12 + 0.18 * charge)),
            hitbox_shape=weapon.heavy_hitbox_shape,
            free_movement=False,
        )
        self.player_attack = AttackInstance(
            definition,
            self._aim_direction(aim_point),
            speed_multiplier=weapon.attack_speed * self.transformation_speed_multiplier,
        )
        self.mask_effect_remaining = 0.55
        self.message = f"{mask.ability.name}! Charge {int(charge * 100)}%."
        return True

    def activate_mask_ability(
        self,
        aim_point: pygame.Vector2 | tuple[float, float],
        obstacles: list[pygame.Rect] | None = None,
    ) -> bool:
        if (
            self.finished
            or self.player_attack is not None
            or self.player_state.stun_remaining > 0
            or self.mask_manager.transition_remaining > 0
        ):
            return False
        mask = self.mask_manager.mask()
        if mask is None or mask.ability.kind == MaskAbilityKind.CHARGED_SLASH:
            return False
        activated = self.mask_manager.activate()
        if activated is None:
            self.message = "The mask is cooling down or lacks energy."
            return False

        level = self.mask_manager.level()
        primary, secondary = mask.ability_values(level)
        self.mask_effect_remaining = 0.45
        if mask.ability.kind == MaskAbilityKind.SHADOW_STEP:
            direction = top_down_attack_direction(
                pygame.Vector2(self.player.rect.center),
                aim_point,
            )
            vector = _ATTACK_SPACE_VECTORS.get(direction, _ATTACK_SPACE_VECTORS["down"])
            start = pygame.Vector2(self.player.rect.center)
            self.player.direction = direction
            displacement = vector * primary
            collision_list = obstacles or []
            if hasattr(self.player, "_move_axis"):
                self.player._move_axis(displacement.x, 0, collision_list)
                self.player._move_axis(displacement.y, 1, collision_list)
            else:
                self.player.rect.move_ip(round(displacement.x), round(displacement.y))
            if hasattr(self.player, "position"):
                self.player.position.update(self.player.rect.topleft)
            self.player_state.invulnerability_remaining = max(
                self.player_state.invulnerability_remaining,
                secondary,
            )
            self.dash_origin = start
            self.dash_target = pygame.Vector2(self.player.rect.center)
            self.dash_trail_remaining = 0.3
            self.message = f"{mask.ability.name}!"
        elif mask.ability.kind == MaskAbilityKind.SPIRIT_VEIL:
            self.spirit_veil_remaining = primary
            self.player_state.invulnerability_remaining = max(
                self.player_state.invulnerability_remaining, primary
            )
            self.mask_effect_remaining = primary
            self.message = f"{mask.ability.name}! Akihiro is protected by a spirit veil."
        elif mask.ability.kind == MaskAbilityKind.HEAVENLY_JUDGMENT:
            passive = mask.passive_effect(level)
            self.counter_remaining = primary + passive.counter_window_bonus
            self.counter_damage_multiplier = secondary
            self.message = "Heavenly Judgment ready — meet the enemy's strike."
        elif mask.ability.kind == MaskAbilityKind.PHANTOM_DOUBLE:
            direction = top_down_attack_direction(
                pygame.Vector2(self.player.rect.center), aim_point
            )
            vector = _ATTACK_SPACE_VECTORS.get(direction, _ATTACK_SPACE_VECTORS["down"])
            decoy_rect = self.player.rect.copy()
            decoy_rect.center = (
                round(self.player.rect.centerx - vector.x * 24),
                round(self.player.rect.centery - vector.y * 24),
            )
            for obstacle in obstacles or []:
                if decoy_rect.colliderect(obstacle):
                    decoy_rect.center = self.player.rect.center
                    break
            self.phantom_decoy = PhantomDecoy(
                decoy_rect,
                Health(max(1, round(secondary))),
                primary,
            )
            self.phantom_decoy_state = CombatantState()
            self.mask_effect_remaining = primary
            self.message = "Phantom Double! The illusion draws hostile attention."
        return True

    def update(self, dt: float, obstacles: list[pygame.Rect] | None = None) -> None:
        dt = max(0.0, min(dt, 0.1))
        self.hit_stop_active = False
        if self.finished:
            return
        if self.hit_stop_remaining > 0:
            self.hit_stop_remaining = max(0.0, self.hit_stop_remaining - dt)
            self.hit_stop_active = True
            return

        self.mask_manager.update(dt)
        self.counter_remaining = max(0.0, self.counter_remaining - dt)
        self.transformation_remaining = max(0.0, self.transformation_remaining - dt)
        self.spirit_veil_remaining = max(0.0, self.spirit_veil_remaining - dt)
        if self.phantom_decoy is not None:
            self.phantom_decoy.remaining = max(0.0, self.phantom_decoy.remaining - dt)
            if self.phantom_decoy.remaining <= 0 or self.phantom_decoy.health <= 0:
                self.phantom_decoy = None
        self.mask_effect_remaining = max(0.0, self.mask_effect_remaining - dt)
        self.dash_trail_remaining = max(0.0, self.dash_trail_remaining - dt)
        if self.transformation_remaining <= 0:
            self.transformation_damage_multiplier = 1.0
            self.transformation_speed_multiplier = 1.0
        self.elapsed += dt
        if self.enemy.name == "Ashen Oni":
            phase = 2 if self.enemy.health <= self.enemy.max_health * 0.5 else 1
            if phase != self.enemy_phase:
                self.enemy_phase = phase
                self.message = (
                    "The Ashen Oni erupts in cursed flame! Its attacks grow faster and wider."
                    if phase == 2 else "The Ashen Oni gathers its cinders."
                )
        self.player_cooldown = max(0.0, self.player_cooldown - dt)
        self.enemy_cooldown = max(0.0, self.enemy_cooldown - dt * self.FRAMES_PER_SECOND)
        self._update_combatant_state(self.player_state, dt)
        self._update_combatant_state(self.enemy_state, dt)
        self._advance_knockback(self.player, self.player_state, dt, obstacles or [])
        self._advance_knockback(self.enemy, self.enemy_state, dt, obstacles or [])

        self._advance_player_attack(dt)
        if not self.finished:
            self._advance_enemy_attack(dt)
        self._check_result()

    @staticmethod
    def _update_combatant_state(state: CombatantState, dt: float) -> None:
        state.hit_reaction_remaining = max(0.0, state.hit_reaction_remaining - dt)
        state.invulnerability_remaining = max(0.0, state.invulnerability_remaining - dt)
        if state.stun_remaining > 0:
            state.stun_remaining = max(0.0, state.stun_remaining - dt)
            state.state = CombatState.STUNNED if state.stun_remaining > 0 else CombatState.IDLE

    @staticmethod
    def _advance_knockback(
        actor: Combatant,
        state: CombatantState,
        dt: float,
        obstacles: list[pygame.Rect],
    ) -> None:
        velocity = state.knockback_velocity
        if velocity.length_squared() == 0 or dt == 0:
            return
        for axis in (0, 1):
            amount = velocity[axis] * dt
            if not amount:
                continue
            actor.rect[axis] += round(amount)
            for obstacle in obstacles:
                if obstacle is actor.rect or not actor.rect.colliderect(obstacle):
                    continue
                if axis == 0:
                    actor.rect.right = obstacle.left if amount > 0 else obstacle.right
                else:
                    actor.rect.bottom = obstacle.top if amount > 0 else obstacle.bottom
        velocity *= max(0.0, 1.0 - dt * 9.0)
        if velocity.length_squared() < 36:
            velocity.update(0, 0)
        if hasattr(actor, "position"):
            actor.position.update(actor.rect.topleft)
        if hasattr(actor, "sprite_position"):
            actor.sprite_position = (actor.rect.x - 4, actor.rect.y - 23)

    def _advance_player_attack(self, dt: float) -> None:
        attack = self.player_attack
        if attack is None:
            return
        attack.advance(dt, self.FRAMES_PER_SECOND)
        self.player_state.state = attack.state
        if attack.state == CombatState.ACTIVE:
            self._try_attack_hit(attack, self.player, self.enemy, self.enemy_state)
        if attack.finished:
            self.player_cooldown = max(
                self.player_cooldown,
                attack.definition.cooldown_frames
                / (self.FRAMES_PER_SECOND * attack.speed_multiplier),
            )
            self.player_attack = None
            if self.player_state.stun_remaining <= 0:
                self.player_state.state = CombatState.IDLE

    def _advance_enemy_attack(self, dt: float) -> None:
        decoy = self.phantom_decoy
        target = decoy if decoy is not None else self.player
        target_state = self.phantom_decoy_state if decoy is not None else self.player_state
        attack = self.enemy_attack
        if attack is None:
            if self.enemy_cooldown > 0 or self.enemy_state.stun_remaining > 0:
                return
            distance = pygame.Vector2(target.rect.center).distance_to(self.enemy.rect.center)
            is_oni = self.enemy.name == "Ashen Oni"
            attack_definition = ENEMY_ATTACK
            engage_range = self.ENEMY_ENGAGE_RANGE
            if is_oni:
                attack_definition = (
                    ASHEN_ONI_ENRAGED_ATTACK if self.enemy_phase == 2
                    else ASHEN_ONI_ATTACK
                )
                engage_range = 154.0
            if distance > engage_range:
                return
            direction = top_down_attack_direction(self.enemy.rect.center, target.rect.center)
            self.enemy_attack = AttackInstance(attack_definition, direction)
            attack = self.enemy_attack

        attack.advance(dt, self.FRAMES_PER_SECOND)
        self.enemy_state.state = attack.state
        if attack.state == CombatState.ACTIVE:
            if target is self.player and self.counter_remaining > 0 and self._try_counter(attack):
                return
            self._try_attack_hit(attack, self.enemy, target, target_state)
        if attack.finished:
            self.enemy_cooldown = attack.definition.cooldown_frames
            self.enemy_attack = None
            if self.enemy_state.stun_remaining <= 0:
                self.enemy_state.state = CombatState.IDLE

    def _try_counter(self, attack: AttackInstance) -> bool:
        if attack.hitbox is None:
            attack.hitbox = make_hitbox(self.enemy.rect, attack.direction, attack.definition)
        else:
            attack.hitbox.rect = make_hitbox(
                self.enemy.rect,
                attack.direction,
                attack.definition,
            ).rect
        if not attack.hitbox.rect.colliderect(self.player.rect):
            return False
        mask = self.mask_manager.mask()
        if mask is None or mask.ability.kind != MaskAbilityKind.HEAVENLY_JUDGMENT:
            return False
        self.counter_remaining = 0.0
        attack.hitbox.try_hit(Hurtbox(self.player.rect), self.player)
        damage = max(
            1,
            round(self.weapon.heavy_attack.damage * self.counter_damage_multiplier),
        )
        self.enemy.vitality.apply_damage(damage)
        away = pygame.Vector2(self.enemy.rect.center) - pygame.Vector2(self.player.rect.center)
        self.enemy_state.receive(Damage(damage, 225.0, 0.32), away)
        self.enemy_state.invulnerability_remaining = 0.2
        self.player_state.invulnerability_remaining = max(
            self.player_state.invulnerability_remaining,
            0.45,
        )
        self.enemy_attack = None
        self.enemy_cooldown = ENEMY_ATTACK.cooldown_frames
        self.mask_manager.energy = min(self.mask_manager.max_energy, self.mask_manager.energy + 8.0)
        self.hit_stop_remaining = self.HIT_STOP_SECONDS
        self.mask_effect_remaining = 0.35
        self.message = f"Heavenly Judgment! {damage} damage returned."
        return True

    def _try_attack_hit(
        self,
        attack: AttackInstance,
        attacker: Combatant,
        target: Combatant,
        target_state: CombatantState,
    ) -> bool:
        if target_state.invulnerability_remaining > 0 or target.health <= 0:
            return False
        if attack.hitbox is None:
            attack.hitbox = make_hitbox(attacker.rect, attack.direction, attack.definition)
        else:
            attack.hitbox.rect = make_hitbox(
                attacker.rect, attack.direction, attack.definition
            ).rect
        if not attack.hitbox.try_hit(Hurtbox(target.rect), target):
            return False

        applied = target.vitality.apply_damage(attack.hitbox.damage.amount)
        if applied <= 0:
            return False
        direction = _ATTACK_SPACE_VECTORS.get(
            attack.direction,
            _ATTACK_SPACE_VECTORS["down"],
        ).copy()
        if attacker is self.enemy:
            direction = pygame.Vector2(target.rect.center) - pygame.Vector2(attacker.rect.center)
        target_state.receive(attack.hitbox.damage, direction)
        if target is self.player and self.mask_manager.charging:
            self.mask_manager.cancel_charge()
        target_state.invulnerability_remaining = 0.24 if target is self.enemy else 0.58
        if target_state.state == CombatState.STUNNED:
            if target is self.enemy:
                self.enemy_attack = None
            elif target is self.player:
                self.player_attack = None
        self.hit_stop_remaining = self.HIT_STOP_SECONDS
        self.message = f"{attack.definition.name} hits for {applied} damage."
        if attacker is self.player:
            mask = self.mask_manager.mask()
            if mask is not None:
                passive = mask.passive_effect(self.mask_manager.level())
                heal_ratio = passive.passive_lifesteal
                if heal_ratio > 0:
                    restored = self.player.vitality.heal(max(1, round(applied * heal_ratio)))
                    if restored:
                        self.message += f" Restored {restored} health."
        return True

    def _check_result(self) -> None:
        if self.enemy.health <= 0:
            self.finished = True
            self.result = "victory"
            self.message = f"The {self.enemy.name} fades into the mist."
        elif self.player.health <= 0:
            self.finished = True
            self.result = "defeat"
            self.message = "The wraith overwhelms you. You retreat to recover."
