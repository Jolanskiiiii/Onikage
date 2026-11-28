import math

import pygame

from onikage.art.audio.sfx import GameAudio
from onikage.art.fonts.ui import create_ui_fonts
from onikage.art.ui.panels import draw_frame, item_icon
from onikage.game_state import GameManager, GameState
from onikage.combat import RealtimeCombat
from onikage.campaign import CampaignProgress, LORE_FRAGMENTS
from onikage.dialogue import DialogueSystem
from onikage.main_menu import MainMenu
from onikage.masks import (
    SHRINE_PROGRESS,
    WRAITH_PROGRESS,
    MaskAbilityKind,
    MaskManager,
    MaskType,
    all_mask_types,
    create_mask,
)
from onikage.player import Player
from onikage.quests import Quest, QuestLog, QuestStatus
from onikage.save_data import SaveData, SaveManager
from onikage.village import VillageWorld
from onikage.burning_village import BurningVillageWorld
from onikage.drowned_temple import DrownedTempleWorld
from onikage.cedar_forest import CedarForestWorld
from onikage.kurogane_castle import KuroganeCastleWorld
from onikage.realm_between_worlds import RealmBetweenWorlds
from onikage.weapons import (
    WEAPON_DEFINITIONS,
    WEAPON_ORDER,
    WeaponInventory,
    WeaponType,
)


class Game:
    """Owns the Pygame window and controls the current screen."""

    SCREEN_SIZE = (1280, 720)
    TARGET_FPS = 60
    AUTOSAVE_INTERVAL_SECONDS = 30.0

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("ONIKAGE: The Curse of the Fallen Samurai")
        self.screen = pygame.display.set_mode(self.SCREEN_SIZE)
        self.overlay_surface = pygame.Surface(self.SCREEN_SIZE, pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        self.menu = MainMenu()
        self.state_manager = GameManager()
        self.running = True
        self.fullscreen = False
        self.world: VillageWorld | None = None
        self.player: Player | None = None
        self.camera = pygame.Vector2()
        self.dialogue = DialogueSystem()
        self.combat: RealtimeCombat | None = None
        self.audio = GameAudio()
        self.quest_log = QuestLog()
        self.notice = ""
        self.notice_time = 0.0
        self.visual_time = 0.0
        self._slash_seen_attack = None
        self._slash_effect_started = 0.0
        self._slash_effect_mask = None
        self._slash_effect_direction = "down"
        self._slash_effect_combo = 1
        self._slash_effect_heavy = False
        self._minimap_cache_key = None
        self._minimap_base = None
        self._minimap_mask = None
        self._minimap_scale_data = None
        self.save_manager = SaveManager()
        self.campaign = CampaignProgress()
        self._autosave_elapsed = 0.0
        saved_game = self.save_manager.load()
        self.menu.set_continue_available(
            saved_game is not None,
            "Continue your journey" if saved_game is not None else None,
        )

        self.title_font, self.body_font, self.small_font = create_ui_fonts()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(self.TARGET_FPS) / 1000.0
            self._handle_events()
            self.menu.update(dt)
            self._update(dt)
            self._draw()
            pygame.display.flip()

        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._save_progress()
                self.running = False
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self._toggle_fullscreen()
                continue

            state = self.state_manager.current_state
            if state == GameState.MENU:
                action = self.menu.handle_event(event)
                if action == "resume":
                    self.state_manager.transition_to(GameState.EXPLORATION)
                elif action == "new_game":
                    self._start_new_game()
                elif action == "continue":
                    self._continue_game()
                elif action == "settings":
                    self.state_manager.transition_to(GameState.SETTINGS)
                elif action == "exit":
                    self._save_progress()
                    self.running = False
            elif state == GameState.SETTINGS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state_manager.transition_to(GameState.MENU)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    result = self.menu.handle_settings_click(event.pos)
                    if result == "back":
                        self.state_manager.transition_to(GameState.MENU)
                    elif result == "fullscreen":
                        self._toggle_fullscreen()
            elif state == GameState.EXPLORATION:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.player is not None:
                            self.player.mask_manager.cancel_charge()
                        self._save_progress()
                        self.menu.set_resume_available(True)
                        self.state_manager.transition_to(GameState.MENU)
                    elif event.key == pygame.K_i:
                        self.audio.play_ui(opening=True)
                        self.state_manager.transition_to(GameState.INVENTORY)
                    elif event.key == pygame.K_j:
                        self.audio.play_ui(opening=True)
                        self.state_manager.transition_to(GameState.QUEST_LOG)
                    elif event.key in (pygame.K_h, pygame.K_c, pygame.K_x) and "nameless_one" in self.campaign.defeated_guardians and self.campaign.ending is None:
                        ending = {pygame.K_h: "humanity", pygame.K_c: "curse", pygame.K_x: "exile"}[event.key]
                        self.campaign.choose_ending(ending)
                        self.notice = {"humanity": "Ending: Humanity — the masks are sealed, and Akihiro chooses mercy.", "curse": "Ending: Curse — Akihiro claims the masks and becomes their new keeper.", "exile": "Ending: Exile — Akihiro walks beyond the known world, carrying the curse away."}[ending]
                        self.notice_time = 7.0
                        self._save_progress()
                    elif event.key == pygame.K_e:
                        self._interact()
                    elif event.key == pygame.K_c:
                        self._start_battle()
                    elif event.key == pygame.K_v:
                        self._cycle_mask(1)
                    elif event.key == pygame.K_u:
                        self._upgrade_equipped_mask()
                    elif event.key == pygame.K_q:
                        self._use_mask_ability()
                    elif pygame.K_1 <= event.key <= pygame.K_4:
                        self._select_weapon_slot(event.key - pygame.K_1 + 1)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                    combat = self._combat_for_mouse_attack(event.pos)
                    if combat is not None:
                        aim_point = pygame.Vector2(event.pos) + self.camera
                        if event.button == 1:
                            started = combat.start_light(aim_point)
                        else:
                            started = combat.start_heavy(aim_point)
                        if started:
                            self.audio.play_combat_attack(heavy=event.button == 3)
                elif event.type == pygame.MOUSEWHEEL and event.y:
                    self._cycle_weapon(event.y)
                elif event.type == pygame.KEYUP and event.key == pygame.K_q:
                    if self.combat is not None and self.player is not None:
                        aim_point = pygame.Vector2(pygame.mouse.get_pos()) + self.camera
                        if self.player.mask_manager.charging:
                            started = self.combat.release_mask_charge(aim_point)
                            if started:
                                self.audio.play_combat_attack(heavy=True)
            elif state == GameState.INVENTORY:
                if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE,
                    pygame.K_i,
                ):
                    self.audio.play_ui(opening=False)
                    self.state_manager.transition_to(GameState.EXPLORATION)
            elif state == GameState.QUEST_LOG:
                if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE,
                    pygame.K_j,
                ):
                    self.audio.play_ui(opening=False)
                    self.state_manager.transition_to(GameState.EXPLORATION)
            elif state == GameState.QUEST_OFFER:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    quest = self.quest_log.first_available()
                    if quest is not None:
                        self.quest_log.accept(quest.quest_id)
                        self.notice = f"Quest accepted: {quest.title}"
                        self.notice_time = 4.0
                    self.state_manager.transition_to(GameState.EXPLORATION)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state_manager.transition_to(GameState.EXPLORATION)
            elif state == GameState.DIALOGUE:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.dialogue.active = False
                    self.state_manager.transition_to(GameState.EXPLORATION)
                elif event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    pygame.K_e,
                ):
                    if not self.dialogue.advance():
                        if self.quest_log.first_available() is not None:
                            self.state_manager.transition_to(GameState.QUEST_OFFER)
                        else:
                            self.state_manager.transition_to(GameState.EXPLORATION)

    def _start_battle(self) -> None:
        if self.player is None or self.world is None:
            return
        if self.combat is not None and not self.combat.finished:
            return
        enemy = self.world.find_enemy(self.player.interaction_point())
        if enemy is None:
            self.notice = "No enemy nearby. Follow the lantern path north."
            self.notice_time = 3.0
            return
        self.combat = RealtimeCombat(self.player, enemy)
        self.notice = f"A {enemy.name} blocks the way."
        self.notice_time = 2.5

    def _combat_for_mouse_attack(
        self,
        screen_position: tuple[int, int],
    ) -> RealtimeCombat | None:
        if self.player is None or self.world is None:
            return None
        if self.combat is not None and not self.combat.finished:
            return self.combat

        enemy = self.world.wraith
        if enemy.health <= 0:
            return None
        aim_point = pygame.Vector2(screen_position) + self.camera
        close_to_enemy = pygame.Vector2(self.player.rect.center).distance_to(
            enemy.rect.center
        ) <= 180
        clicked_enemy = enemy.interaction_area.collidepoint(aim_point)
        if not (close_to_enemy or clicked_enemy):
            return None
        self.combat = RealtimeCombat(self.player, enemy)
        return self.combat

    def _resolve_combat(self) -> None:
        if self.combat is None or not self.combat.finished:
            return
        if self.combat.result == "victory" and not self.combat.experience_awarded:
            reward = self.combat.enemy.experience_reward
            self.player.experience += reward
            self.combat.experience_awarded = True
            if self.world is not None:
                self.world.obstacles = [
                    obstacle
                    for obstacle in self.world.obstacles
                    if obstacle is not self.combat.enemy.rect
                ]
            self.combat.enemy.set_animation("death")
            self.notice = f"Victory! You gained {reward} experience."

            # Regional guardians must advance the five-mask campaign rather
            # than being treated as the village Wraith milestone. The Burning
            # Village reuses the existing encounter/combat pipeline, but its
            # victory has its own persistent story reward.
            guardian_rewards = {
                "Ashen Oni": ("ashen_oni", MaskType.WRATH, "The Drowned Temple"),
                "Weeping Bride": ("weeping_bride", MaskType.GRIEF, "The Whispering Cedar Forest"),
                "Hollow Stalker": ("hollow_stalker", MaskType.FEAR, "Fallen Kurogane Castle"),
                "Fallen Shogun": ("fallen_shogun", MaskType.PRIDE, "Realm Between Worlds"),
                "Nameless One": ("nameless_one", MaskType.DECEPTION, "The final choice"),
            }
            guardian = guardian_rewards.get(self.combat.enemy.name)
            if guardian is not None:
                guardian_id, mask_type, next_region = guardian
                first_victory = self.campaign.record_guardian_victory(guardian_id)
                acquired_mask = self.player.mask_manager.defeat_guardian(mask_type)
                if first_victory:
                    self.notice += f" {self.combat.enemy.name} is defeated."
                if acquired_mask:
                    mask = create_mask(mask_type)
                    self.notice += f" {mask.display_name} acquired: {mask.ability.name} unlocked."
                if first_victory:
                    self.notice += f" {next_region} has been revealed in your campaign record."
            else:
                acquired_odachi = self.player.weapon_inventory.acquire(WeaponType.ODACHI)
                acquired_masks = self.player.mask_manager.advance_story(WRAITH_PROGRESS)
                if acquired_odachi:
                    self.notice += " Odachi acquired."
                if acquired_masks:
                    names = ", ".join(create_mask(mask).display_name for mask in acquired_masks)
                    self.notice += f" {names} mask discovered."
            self.notice_time = 5.5
            self._save_progress()
        elif self.combat.result == "defeat":
            self.player.health = max(1, self.player.max_health // 2)
            self.notice = "You retreat to the village and recover. Rest before trying again."
            self.notice_time = 4.0
        self.combat = None

    def _start_new_game(self) -> None:
        self.world = VillageWorld()
        self.campaign = CampaignProgress()
        self.player = Player(755, 580)
        self.combat = None
        self.player.direction = "right"
        self.camera.update(self._camera_target())
        self.notice = ""
        self.notice_time = 0.0
        self.dialogue.active = False
        self.quest_log = QuestLog()
        self.quest_log.add(
            Quest(
                quest_id="village_shrine_prayer",
                title="A Prayer for the Village",
                giver="Hana, Village Keeper",
                description="The villagers are frightened by strange lights in the forest.",
                objective="Visit the village shrine and offer a prayer.",
            )
        )
        self.quest_log.add(
            Quest(
                quest_id="names_on_stone",
                title="The Names on the Stone",
                giver="Hana, Village Keeper",
                description="A memorial tablet near the old well has been buried beneath fallen leaves. Hana asks you to restore the names before the spirits forget them.",
                objective="Find the memorial stone in the eastern garden and pay your respects.",
            )
        )
        self.quest_log.add(
            Quest(
                quest_id="merchants_lost_ledger",
                title="The Merchant's Lost Ledger",
                giver="Hana, Village Keeper",
                description="A travelling merchant left his ledger beside the southern market cart. Without it, he cannot remember which families still need supplies.",
                objective="Search the southern market cart and return the ledger to the village notice board.",
            )
        )
        self.state_manager.transition_to(GameState.EXPLORATION)
        self._autosave_elapsed = 0.0
        self._save_progress()

    def _continue_game(self) -> None:
        save = self.save_manager.load()
        if save is None:
            self.menu.set_continue_available(False)
            self.notice = "No saved journey is available."
            self.notice_time = 3.0
            return

        self.campaign = CampaignProgress.from_dict(save.campaign)
        # Backfill lore for older saves created before the chronicle was added.
        if "burning_village" in self.campaign.unlocked_regions:
            self.campaign.unlock_lore("prologue")
        for guardian, key in (
            ("ashen_oni", "wrath"), ("weeping_bride", "grief"),
            ("hollow_stalker", "fear"), ("fallen_shogun", "pride"),
            ("nameless_one", "deception"),
        ):
            if guardian in self.campaign.defeated_guardians:
                self.campaign.unlock_lore(key)
        if self.campaign.ending:
            self.campaign.unlock_lore(f"{self.campaign.ending}_ending")
        if self.campaign.current_region == "burning_village":
            self.world = BurningVillageWorld()
        elif self.campaign.current_region == "drowned_temple":
            self.world = DrownedTempleWorld()
        elif self.campaign.current_region == "cedar_forest":
            self.world = CedarForestWorld()
        elif self.campaign.current_region == "kurogane_castle":
            self.world = KuroganeCastleWorld()
        elif self.campaign.current_region == "realm_between_worlds":
            self.world = RealmBetweenWorlds()
        else:
            self.world = VillageWorld()
        self.player = Player(save.player_x, save.player_y)
        self.player.direction = save.direction
        self.player.health = save.health
        self.player.stamina = save.stamina
        self.player.level = save.level
        self.player.experience = save.experience
        self.player.rations = save.rations
        self.player.weapon_inventory = WeaponInventory.from_dict(save.weapon_inventory)
        self.player.mask_manager = MaskManager.from_dict(save.mask_manager)
        self.world.wraith.health = save.wraith_health
        guardian_for_region = {
            "burning_village": "ashen_oni",
            "drowned_temple": "weeping_bride",
            "cedar_forest": "hollow_stalker",
            "kurogane_castle": "fallen_shogun",
            "realm_between_worlds": "nameless_one",
        }.get(self.campaign.current_region)
        if guardian_for_region and guardian_for_region in self.campaign.defeated_guardians:
            # Keep completed regional guardians defeated after loading a save.
            self.world.wraith.health = 0
            self.world.obstacles = [
                obstacle for obstacle in self.world.obstacles
                if obstacle is not self.world.wraith.rect
            ]
            self.world.wraith.set_animation("death")
        if "village_shrine_prayer" in save.completed_quest_ids:
            self.player.mask_manager.advance_story(SHRINE_PROGRESS)
        if self.world.wraith.health <= 0:
            self.player.mask_manager.advance_story(WRAITH_PROGRESS)
        self.world.weapon_pickups = [
            pickup
            for pickup in self.world.weapon_pickups
            if pickup.weapon_type not in self.player.weapon_inventory.owned
        ]
        if self.world.wraith.health <= 0:
            self.world.obstacles = [
                obstacle
                for obstacle in self.world.obstacles
                if obstacle is not self.world.wraith.rect
            ]
        self.world.mask_pickups = [
            pickup
            for pickup in self.world.mask_pickups
            if pickup.mask_type not in self.player.mask_manager.owned
        ]

        self.quest_log = QuestLog()
        self.quest_log.add(
            Quest(
                quest_id="village_shrine_prayer",
                title="A Prayer for the Village",
                giver="Hana, Village Keeper",
                description="The villagers are frightened by strange lights in the forest.",
                objective="Visit the village shrine and offer a prayer.",
            )
        )
        self.quest_log.add(
            Quest(
                quest_id="names_on_stone",
                title="The Names on the Stone",
                giver="Hana, Village Keeper",
                description="A memorial tablet near the old well has been buried beneath fallen leaves. Hana asks you to restore the names before the spirits forget them.",
                objective="Find the memorial stone in the eastern garden and pay your respects.",
            )
        )
        self.quest_log.add(
            Quest(
                quest_id="merchants_lost_ledger",
                title="The Merchant's Lost Ledger",
                giver="Hana, Village Keeper",
                description="A travelling merchant left his ledger beside the southern market cart. Without it, he cannot remember which families still need supplies.",
                objective="Search the southern market cart and return the ledger to the village notice board.",
            )
        )
        quest = self.quest_log.get("village_shrine_prayer")
        if quest.quest_id in save.active_quest_ids or quest.quest_id in save.completed_quest_ids:
            self.quest_log.accept(quest.quest_id)
        if quest.quest_id in save.completed_quest_ids:
            self.quest_log.complete(quest.quest_id)
        for side_id in ("names_on_stone", "merchants_lost_ledger"):
            side = self.quest_log.get(side_id)
            if side_id in save.active_quest_ids or side_id in save.completed_quest_ids:
                self.quest_log.accept(side_id)
            if side_id in save.completed_quest_ids:
                self.quest_log.complete(side_id)

        self.combat = None
        self.dialogue.active = False
        self.notice = "Journey continued."
        self.notice_time = 2.5
        self.camera.update(self._camera_target())
        self.menu.set_resume_available(True)
        self.state_manager.transition_to(GameState.EXPLORATION)
        self._autosave_elapsed = 0.0
        self._save_progress()

    def _save_progress(self) -> bool:
        """Persist the current safe gameplay snapshot without crashing the game."""
        if self.player is None or self.world is None:
            return False
        try:
            self.save_manager.save(
                SaveData(
                    player_x=self.player.position.x,
                    player_y=self.player.position.y,
                    direction=self.player.direction,
                    health=self.player.health,
                    stamina=self.player.stamina,
                    level=self.player.level,
                    experience=self.player.experience,
                    rations=self.player.rations,
                    weapon_inventory=self.player.weapon_inventory.to_dict(),
                    mask_manager=self.player.mask_manager.to_dict(),
                    active_quest_ids=[
                        quest.quest_id
                        for quest in self.quest_log.quests
                        if quest.status == QuestStatus.ACTIVE
                    ],
                    completed_quest_ids=[
                        quest.quest_id
                        for quest in self.quest_log.quests
                        if quest.status == QuestStatus.COMPLETED
                    ],
                    wraith_health=self.world.wraith.health,
                    campaign=getattr(self, "campaign", CampaignProgress()).to_dict(),
                )
            )
        except (OSError, TypeError, ValueError) as exc:
            self.notice = "Unable to save your journey. Check available disk space and permissions."
            self.notice_time = 4.0
            return False
        self.menu.set_continue_available(True, "Continue your journey")
        return True

    def _acquire_weapon(self, weapon: WeaponType) -> bool:
        if self.player is None:
            return False
        acquired = self.player.weapon_inventory.acquire(weapon)
        if acquired:
            self._save_progress()
        return acquired

    def _select_weapon_slot(self, slot: int) -> None:
        if self.player is None:
            return
        weapon = self.player.weapon_inventory.weapon_for_slot(slot)
        if weapon is None:
            self.notice = f"Weapon slot {slot} is locked. Find or earn that weapon first."
            self.notice_time = 2.5
            return
        self._equip_weapon(weapon)

    def _cycle_weapon(self, direction: int) -> None:
        if self.player is None:
            return
        self._equip_weapon(self.player.weapon_inventory.next_owned(direction))

    def _equip_weapon(self, weapon: WeaponType) -> bool:
        if self.player is None:
            return False
        if self.combat is not None:
            if self.combat.player_attack is not None:
                self.notice = "Finish the current attack before switching weapons."
                self.notice_time = 2.0
                return False
            equipped = self.combat.switch_weapon(weapon)
        else:
            equipped = self.player.weapon_inventory.equip(weapon)
        if not equipped:
            self.notice = "That weapon is not available yet."
            self.notice_time = 2.0
            return False
        self.audio.play_ui(opening=True)
        self.notice = f"Equipped {WEAPON_DEFINITIONS[weapon].display_name}."
        self.notice_time = 1.8
        self._save_progress()
        return True

    def _cycle_mask(self, direction: int) -> None:
        if self.player is None:
            return
        if self.combat is not None:
            selected = self.combat.cycle_mask(direction)
        else:
            selected = self.player.mask_manager.cycle(direction)
        if selected is None:
            self.notice = "No mask is ready to switch to."
            self.notice_time = 1.8
            return
        self.audio.play_ui(opening=True)
        self.notice = f"Mask transition: {create_mask(selected).display_name}."
        self.notice_time = 2.0
        self._save_progress()

    def _use_mask_ability(self) -> None:
        if self.player is None or self.combat is None:
            self.notice = "Cursed mask abilities can be invoked during an encounter."
            self.notice_time = 2.0
            return
        mask = self.player.mask_manager.mask()
        if mask is None:
            self.notice = "No cursed mask is equipped."
            self.notice_time = 2.0
            return
        if mask.ability.kind == MaskAbilityKind.CHARGED_SLASH:
            if self.combat.begin_mask_charge():
                self.notice = "Hold Q, then release to unleash the charged slash."
                self.notice_time = 2.0
            else:
                self.notice = "The Wrath mask is transitioning, cooling down, or short on energy."
                self.notice_time = 2.0
            return
        aim_point = pygame.Vector2(pygame.mouse.get_pos()) + self.camera
        if self.combat.activate_mask_ability(aim_point, self.world.obstacles if self.world else []):
            self.audio.play_combat_attack(heavy=mask.ability.kind == MaskAbilityKind.HEAVENLY_JUDGMENT)
            self.notice = self.combat.message
            self.notice_time = 2.0
        else:
            self.notice = self.combat.message
            self.notice_time = 2.0

    def _upgrade_equipped_mask(self) -> None:
        if self.player is None or not self.player.mask_manager.upgrade():
            self.notice = "An equipped mask and an upgrade seal are required."
            self.notice_time = 2.0
            return
        mask = self.player.mask_manager.mask()
        self.notice = f"{mask.display_name} upgraded to level {self.player.mask_manager.level()}."
        self.notice_time = 2.5
        self._save_progress()

    def _update(self, dt: float) -> None:
        self.visual_time += dt
        if self.notice_time > 0:
            self.notice_time = max(0.0, self.notice_time - dt)
        if self.state_manager.current_state != GameState.EXPLORATION:
            return
        if self.player is None or self.world is None:
            return

        if self.combat is not None:
            self.combat.update(dt, self.world.obstacles)
            attack = self.combat.player_attack
            if attack is not None and attack.state.name == "ACTIVE" and id(attack) != self._slash_seen_attack:
                self._slash_seen_attack = id(attack)
                self._slash_effect_started = self.visual_time
                self._slash_effect_direction = attack.direction
                current_mask = self.player.mask_manager.mask()
                self._slash_effect_mask = current_mask.mask_type if current_mask else None
                self._slash_effect_combo = max(1, self.combat.combo.step)
                self._slash_effect_heavy = attack.definition.kind.name in ("HEAVY", "MASK")
            enemy = self.combat.enemy
            if enemy.health <= 0:
                enemy.set_animation("death")
            elif self.combat.enemy_state.hit_reaction_remaining > 0:
                enemy.set_animation("hurt")
            elif self.combat.enemy_attack is not None:
                enemy.set_animation("attack")
            else:
                enemy.set_animation("idle")
            delta = pygame.Vector2(self.player.rect.center) - pygame.Vector2(enemy.rect.center)
            if abs(delta.x) > abs(delta.y):
                enemy.direction = "right" if delta.x > 0 else "left"
            else:
                enemy.direction = "down" if delta.y > 0 else "up"
            if self.combat.hit_stop_active:
                return
            self._resolve_combat()
        else:
            self.player.mask_manager.update(dt)

        self.world.update(dt)
        previous_position = self.player.position.copy()
        self.player.update(
            dt,
            pygame.key.get_pressed(),
            self.world.obstacles,
            movement_locked=self.combat.movement_locked if self.combat else False,
        )
        self.audio.update_footsteps(dt, self.player.position != previous_position)
        self._keep_player_in_world()
        target = self._camera_target()
        easing = 1.0 - 0.001 ** dt
        self.camera += (target - self.camera) * easing

        self._update_autosave(dt)

    def _update_autosave(self, dt: float) -> None:
        """Accumulate play time and save every interval outside active combat."""
        if self.state_manager.current_state != GameState.EXPLORATION:
            return
        if self.combat is not None:
            self._autosave_elapsed = 0.0
            return
        self._autosave_elapsed += max(0.0, dt)
        if self._autosave_elapsed >= self.AUTOSAVE_INTERVAL_SECONDS:
            self._autosave_elapsed = 0.0
            self._save_progress()

    def _camera_target(self) -> pygame.Vector2:
        if self.player is None or self.world is None:
            return self.camera.copy()
        target = pygame.Vector2(
            self.player.rect.centerx - self.SCREEN_SIZE[0] / 2,
            self.player.rect.centery - self.SCREEN_SIZE[1] / 2,
        )
        target.x = max(0.0, min(target.x, self.world.WORLD_SIZE[0] - self.SCREEN_SIZE[0]))
        target.y = max(0.0, min(target.y, self.world.WORLD_SIZE[1] - self.SCREEN_SIZE[1]))
        return target

    def _keep_player_in_world(self) -> None:
        if self.player is None or self.world is None:
            return
        self.player.rect.clamp_ip(pygame.Rect(0, 0, *self.world.WORLD_SIZE))
        self.player.position.update(self.player.rect.topleft)

    def _interact(self) -> None:
        if self.player is None or self.world is None:
            return
        interaction_point = self.player.interaction_point()
        if isinstance(self.world, (BurningVillageWorld, DrownedTempleWorld, CedarForestWorld, KuroganeCastleWorld, RealmBetweenWorlds)) and self.world.is_at_return_gate(interaction_point):
            if isinstance(self.world, RealmBetweenWorlds):
                self.world = KuroganeCastleWorld()
                self.campaign.travel_to("kurogane_castle")
                self.player.rect.topleft = (1640, 580)
                self.notice = "You returned to Fallen Kurogane Castle."
            elif isinstance(self.world, KuroganeCastleWorld):
                self.world = CedarForestWorld()
                self.campaign.travel_to("cedar_forest")
                self.player.rect.topleft = (1640, 580)
                self.notice = "You returned to the Whispering Cedar Forest."
            elif isinstance(self.world, CedarForestWorld):
                self.world = DrownedTempleWorld()
                self.campaign.travel_to("drowned_temple")
                self.player.rect.topleft = (1640, 580)
                self.notice = "You returned to the Drowned Temple."
            elif isinstance(self.world, DrownedTempleWorld):
                self.world = BurningVillageWorld()
                self.campaign.travel_to("burning_village")
                self.player.rect.topleft = (1640, 580)
                self.notice = "You returned to the Burning Village."
            else:
                self.world = VillageWorld()
                self.campaign.travel_to("kagehama_village")
                self.player.rect.topleft = (1640, 580)
                self.notice = "You returned to Kagehama Village."
            self.player.position.update(self.player.rect.topleft)
            self.camera.update(self._camera_target())
            self.notice_time = 3.0
            self._save_progress()
            return
        # The scorched pass is a broad, visible roadside entrance at the east
        # edge. Use the player's body footprint rather than a single facing
        # point: this prevents the gate from being missed when standing beside it.
        burning_gate = pygame.Rect(1600, 505, 192, 240)
        player_footprint = self.player.rect.inflate(42, 34)
        if not isinstance(self.world, (BurningVillageWorld, DrownedTempleWorld, CedarForestWorld, KuroganeCastleWorld, RealmBetweenWorlds)) and player_footprint.colliderect(burning_gate):
            if "burning_village" not in self.campaign.unlocked_regions:
                self.notice = "The scorched pass remains sealed. Complete the village shrine prayer first."
                self.notice_time = 3.0
                return
            self.campaign.travel_to("burning_village")
            self.world = BurningVillageWorld()
            self.player.rect.topleft = BurningVillageWorld.ENTRY_POINT
            self.player.position.update(self.player.rect.topleft)
            self.camera.update(self._camera_target())
            self.notice = "The Burning Village — Ash falls across the ruined road."
            self.notice_time = 4.0
            self._save_progress()
            return
        drowned_gate = pygame.Rect(1600, 505, 192, 240)
        if isinstance(self.world, BurningVillageWorld) and not isinstance(self.world, DrownedTempleWorld) and player_footprint.colliderect(drowned_gate):
            if "drowned_temple" not in self.campaign.unlocked_regions:
                self.notice = "The flooded temple path remains sealed. Defeat the Ashen Oni first."
                self.notice_time = 3.0
                return
            self.campaign.travel_to("drowned_temple")
            self.world = DrownedTempleWorld()
            self.player.rect.topleft = DrownedTempleWorld.ENTRY_POINT
            self.player.position.update(self.player.rect.topleft)
            self.camera.update(self._camera_target())
            self.notice = "The Drowned Temple — cold water stirs beneath the stone causeway."
            self.notice_time = 4.0
            self._save_progress()
            return
        cedar_gate = pygame.Rect(1600, 505, 192, 240)
        if isinstance(self.world, DrownedTempleWorld) and player_footprint.colliderect(cedar_gate):
            if "cedar_forest" not in self.campaign.unlocked_regions:
                self.notice = "The cedar trail remains sealed. Defeat the Weeping Bride first."
                self.notice_time = 3.0
                return
            self.campaign.travel_to("cedar_forest")
            self.world = CedarForestWorld()
            self.player.rect.topleft = CedarForestWorld.ENTRY_POINT
            self.player.position.update(self.player.rect.topleft)
            self.camera.update(self._camera_target())
            self.notice = "The Whispering Cedar Forest — something moves between the ancient trunks."
            self.notice_time = 4.0
            self._save_progress()
            return
        castle_gate = pygame.Rect(1600, 505, 192, 240)
        if isinstance(self.world, CedarForestWorld) and player_footprint.colliderect(castle_gate):
            if "kurogane_castle" not in self.campaign.unlocked_regions:
                self.notice = "The castle bridge is sealed. Defeat the Hollow Stalker first."
                self.notice_time = 3.0
                return
            self.campaign.travel_to("kurogane_castle")
            self.world = KuroganeCastleWorld()
            self.player.rect.topleft = KuroganeCastleWorld.ENTRY_POINT
            self.player.position.update(self.player.rect.topleft)
            self.camera.update(self._camera_target())
            self.notice = "Fallen Kurogane Castle — the Shogun waits beyond the broken walls."
            self.notice_time = 4.0
            self._save_progress()
            return
        if isinstance(self.world, KuroganeCastleWorld) and player_footprint.colliderect(castle_gate):
            if "realm_between_worlds" not in self.campaign.unlocked_regions:
                self.notice = "The final rift remains sealed. Defeat the Fallen Shogun first."
                self.notice_time = 3.0
                return
            self.campaign.travel_to("realm_between_worlds")
            self.world = RealmBetweenWorlds()
            self.player.rect.topleft = RealmBetweenWorlds.ENTRY_POINT
            self.player.position.update(self.player.rect.topleft)
            self.camera.update(self._camera_target())
            self.notice = "The Realm Between Worlds — the Nameless One awaits."
            self.notice_time = 4.0
            self._save_progress()
            return
        enemy = self.world.find_enemy(interaction_point)
        if enemy is not None:
            if self.combat is None or self.combat.finished:
                self.combat = RealtimeCombat(self.player, enemy)
            return
        pickup = self.world.find_weapon_pickup(self.player.interaction_point())
        if pickup is not None:
            self.world.weapon_pickups.remove(pickup)
            if self._acquire_weapon(pickup.weapon_type):
                weapon_name = WEAPON_DEFINITIONS[pickup.weapon_type].display_name
                self.notice = f"Found {weapon_name}. Press its number key or use the mouse wheel to equip it."
            else:
                self.notice = f"You already own {WEAPON_DEFINITIONS[pickup.weapon_type].display_name}."
            self.notice_time = 3.5
            return
        mask_pickup = self.world.find_mask_pickup(self.player.interaction_point())
        if mask_pickup is not None:
            if not self.player.mask_manager.can_acquire(mask_pickup.mask_type):
                self.notice = "The mask's seal has not yielded to your journey yet."
                self.notice_time = 2.5
                return
            previous_masks = set(self.player.mask_manager.owned)
            if self.player.mask_manager.acquire(mask_pickup.mask_type):
                self.world.mask_pickups.remove(mask_pickup)
                newly_acquired = self.player.mask_manager.owned - previous_masks
                names = ", ".join(create_mask(mask).display_name for mask in newly_acquired)
                self.notice = f"{names} mask acquired."
                self.notice_time = 3.0
                self._save_progress()
            return
        villager = self.world.find_villager(self.player.interaction_point())
        if villager is not None:
            self.dialogue.start(villager.name, villager.lines)
            self.state_manager.transition_to(GameState.DIALOGUE)
            return
        message = self.world.interact(self.player.interaction_point())
        # Optional Kagehama errands have concrete world-space destinations.
        if message and hasattr(self.world, "quest_sites"):
            point = self.player.interaction_point()
            for quest_id, site in self.world.quest_sites.items():
                quest_state = next((q for q in self.quest_log.quests if q.quest_id == quest_id), None)
                if quest_state is not None and quest_state.status == QuestStatus.ACTIVE and pygame.Vector2(point).distance_to(site[0]) <= 58:
                    self.quest_log.complete(quest_id)
                    message = f"Quest complete: {quest_state.title}. {site[1]}"
                    self._save_progress()
                    break
        if (
            message
            and self.world.is_near_shrine(self.player.interaction_point())
            and any(
                quest.status == QuestStatus.ACTIVE
                and quest.quest_id == "village_shrine_prayer"
                for quest in self.quest_log.quests
            )
        ):
            self.quest_log.complete("village_shrine_prayer")
            message = "Quest complete: A Prayer for the Village. The shrine glows softly."
            self.campaign.complete_prologue()
            if self._acquire_weapon(WeaponType.DUAL_BLADES):
                message += " Dual Blades acquired."
            acquired_masks = self.player.mask_manager.advance_story(SHRINE_PROGRESS)
            if acquired_masks:
                names = ", ".join(create_mask(mask).display_name for mask in acquired_masks)
                message += f" {names} mask discovered."
            self._save_progress()
        if message:
            self.notice = message
            self.notice_time = 5.0
        else:
            self.notice = "Nothing nearby to interact with."
            self.notice_time = 2.0

    def _toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode(self.SCREEN_SIZE, flags)

    def _draw(self) -> None:
        state = self.state_manager.current_state
        if state == GameState.MENU:
            self.menu.draw(self.screen)
        elif state == GameState.SETTINGS:
            self.menu.draw(self.screen)
            self._draw_settings()
        elif state in (
            GameState.EXPLORATION,
            GameState.INVENTORY,
            GameState.DIALOGUE,
            GameState.QUEST_OFFER,
            GameState.QUEST_LOG,
        ):
            self._draw_exploration()
            if state == GameState.INVENTORY:
                self._draw_inventory()
            elif state == GameState.DIALOGUE:
                self.dialogue.draw(
                    self.screen,
                    self.body_font,
                    self.body_font,
                    self.small_font,
                )
            elif state == GameState.QUEST_OFFER:
                self._draw_quest_offer()
            elif state == GameState.QUEST_LOG:
                self._draw_quest_log()

    def _draw_settings(self) -> None:
        self.menu.draw_settings_panel(self.screen, self.fullscreen)

    def _draw_scrim(self, alpha: int) -> None:
        self.overlay_surface.fill((8, 8, 13, alpha))
        self.screen.blit(self.overlay_surface, (0, 0))

    def _draw_exploration(self) -> None:
        if self.player is None or self.world is None:
            self.screen.fill((12, 16, 18))
            return

        camera = self.camera
        self.world.draw(self.screen, camera, self.player.rect.bottom)
        self.world.draw_mask_pickups(
            self.screen,
            camera,
            self.player.rect.bottom,
            self.player.mask_manager,
            foreground=False,
        )
        self.player.draw(
            self.screen,
            (self.player.rect.x - round(camera.x), self.player.rect.y - round(camera.y)),
        )
        self._draw_slash_effects()
        self.world.draw_foreground(self.screen, camera, self.player.rect.bottom)
        self.world.draw_mask_pickups(
            self.screen,
            camera,
            self.player.rect.bottom,
            self.player.mask_manager,
            foreground=True,
        )
        self._draw_hud()
        self._draw_minimap()
        self._draw_mask_hud()
        self._draw_realtime_combat()
        self._draw_mask_feedback()

    def _draw_minimap(self) -> None:
        """Draw a cached circular minimap; only moving markers update each frame."""
        if self.player is None or self.world is None:
            return

        world_w, world_h = self.world.WORLD_SIZE
        cols, rows = self.world.COLUMNS, self.world.ROWS
        radius, diameter = 70, 140
        center = (radius + 22, self.SCREEN_SIZE[1] - radius - 22)
        region = getattr(self.world, "REGION_ID", "kagehama")
        cache_key = (id(self.world), region, cols, rows, radius)
        palettes = {
            "burning_village": ((43, 29, 25), (156, 78, 43), (85, 53, 42)),
            "drowned_temple": ((16, 42, 48), (83, 133, 137), (31, 79, 85)),
            "cedar_forest": ((18, 39, 27), (112, 105, 75), (48, 75, 47)),
            "kurogane_castle": ((30, 31, 37), (119, 104, 94), (65, 57, 59)),
            "realm_between_worlds": ((28, 20, 45), (135, 99, 174), (65, 48, 91)),
        }
        ground, road, secondary = palettes.get(region, ((29, 48, 32), (143, 115, 84), (64, 82, 53)))

        if self._minimap_cache_key != cache_key or self._minimap_base is None:
            inner = diameter - 12
            scale = min(inner / cols, inner / rows)
            map_w, map_h = max(1, round(cols * scale)), max(1, round(rows * scale))
            offset_x, offset_y = (diameter - map_w) // 2, (diameter - map_h) // 2
            map_surface = pygame.Surface((cols, rows))
            # PixelArray is substantially faster than thousands of set_at calls.
            pixels = pygame.PixelArray(map_surface)
            for row in range(rows):
                for col in range(cols):
                    color = road if self.world._is_road(col, row) else (secondary if (col * 13 + row * 7) % 29 == 0 else ground)
                    pixels[col, row] = map_surface.map_rgb(color)
            del pixels
            scaled = pygame.transform.scale(map_surface, (map_w, map_h))
            base = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            base.fill((7, 11, 12, 245))
            base.blit(scaled, (offset_x, offset_y))

            def point(x: float, y: float) -> tuple[int, int]:
                return (round(offset_x + (x / world_w) * map_w), round(offset_y + (y / world_h) * map_h))

            for building in getattr(self.world, "buildings", []):
                mx, my = point(building.centerx, building.centery)
                pygame.draw.rect(base, (191, 151, 105), (mx - 2, my - 2, 4, 4))
            for attr, color in (("shrine_rect", (255, 218, 125)), ("villager", (245, 157, 190)), ("wraith", (196, 145, 255))):
                obj = getattr(self.world, attr, None)
                rect = obj if isinstance(obj, pygame.Rect) else getattr(obj, "rect", None)
                if rect is not None:
                    pygame.draw.circle(base, color, point(rect.centerx, rect.centery), 3)

            mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius - 2)
            pygame.draw.circle(base, (164, 139, 101, 245), (radius, radius), radius - 1, 2)
            self._minimap_cache_key = cache_key
            self._minimap_base = base
            self._minimap_mask = mask
            self._minimap_scale_data = (offset_x, offset_y, map_w, map_h)

        radar = self._minimap_base.copy()
        offset_x, offset_y, map_w, map_h = self._minimap_scale_data
        def map_point(x: float, y: float) -> tuple[int, int]:
            return (round(offset_x + (x / world_w) * map_w), round(offset_y + (y / world_h) * map_h))

        active_quest = next((q for q in self.quest_log.quests if q.status == QuestStatus.ACTIVE), None)
        if active_quest is not None:
            objective = active_quest.objective.lower()
            target = getattr(self.world, "shrine_rect", None) if "shrine" in objective else None
            if "guardian" in objective or "defeat" in objective:
                target = getattr(getattr(self.world, "wraith", None), "rect", None)
            if target is not None:
                qx, qy = map_point(target.centerx, target.centery)
                pygame.draw.circle(radar, (255, 231, 123), (qx, qy), 5, 1)
                pygame.draw.circle(radar, (255, 231, 123), (qx, qy), 2)

        player_x, player_y = map_point(self.player.rect.centerx, self.player.rect.centery)
        pygame.draw.circle(radar, (255, 248, 210), (player_x, player_y), 4)
        pygame.draw.circle(radar, (30, 24, 17), (player_x, player_y), 4, 1)
        radar.blit(self._minimap_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(radar, (center[0] - radius, center[1] - radius))
        label = self.small_font.render("MAP", True, (220, 202, 164))
        self.screen.blit(label, (center[0] - label.get_width() // 2, center[1] - radius - 17))

    def _draw_mask_hud(self) -> None:
        if self.player is None:
            return
        manager = self.player.mask_manager
        mask = manager.mask()
        if mask is None:
            return
        panel = pygame.Rect(18, 148, 310, 92)
        draw_frame(self.screen, panel, (12, 13, 17), (119, 89, 143))
        icon = pygame.transform.scale(item_icon("mask"), (46, 46))
        self.screen.blit(icon, (panel.x + 12, panel.y + 20))
        title = self.body_font.render(mask.display_name.upper(), True, (213, 192, 230))
        self.screen.blit(title, (panel.x + 70, panel.y + 10))
        self._draw_stat_bar(
            panel.x + 70,
            panel.y + 34,
            panel.width - 84,
            10,
            manager.energy / manager.max_energy,
            (128, 83, 169),
        )
        ability_state = "READY"
        if manager.charging:
            ability_state = f"CHARGING {min(100, int(manager.charge_elapsed / mask.ability.maximum_charge * 100))}%"
        elif manager.transition_remaining > 0:
            ability_state = "TRANSITION"
        elif manager.cooldowns[mask.mask_type] > 0:
            ability_state = f"COOLDOWN {manager.cooldowns[mask.mask_type]:.1f}s"
        detail = self.small_font.render(
            f"Q {mask.ability.name.upper()}   LV {manager.level()}   UPGRADE SEALS {manager.upgrade_tokens}",
            True,
            (196, 184, 207),
        )
        self.screen.blit(detail, (panel.x + 70, panel.y + 51))
        state = self.small_font.render(ability_state, True, (202, 169, 221))
        self.screen.blit(state, (panel.x + 70, panel.y + 72))

    def _draw_mask_feedback(self) -> None:
        if self.player is None:
            return
        manager = self.player.mask_manager
        mask = manager.mask()
        if mask is None:
            return
        colors = {
            MaskType.WRATH: (229, 117, 69),
            MaskType.GRIEF: (159, 169, 205),
            MaskType.FEAR: (111, 204, 207),
            MaskType.PRIDE: (210, 177, 91),
            MaskType.DECEPTION: (177, 119, 202),
        }
        color = colors[mask.mask_type]
        camera = self.camera
        center = (
            self.player.rect.centerx - round(camera.x),
            self.player.rect.centery - round(camera.y),
        )
        if self.combat is not None and self.combat.dash_trail_remaining > 0:
            origin = self.combat.dash_origin or pygame.Vector2(self.player.rect.center)
            target = self.combat.dash_target or pygame.Vector2(self.player.rect.center)
            pygame.draw.line(
                self.screen,
                (*color, 210),
                (round(origin.x - camera.x), round(origin.y - camera.y)),
                (round(target.x - camera.x), round(target.y - camera.y)),
                7,
            )
        if manager.transition_remaining > 0 or manager.charging:
            pulse = int(36 * abs(math.sin(self.visual_time * 4.2)))
            radius = 30 + pulse
            pygame.draw.ellipse(self.screen, color, pygame.Rect(center[0] - radius, center[1] - radius // 2, radius * 2, radius), 2)
        if self.combat is not None and (
            self.combat.transformation_active
            or self.combat.counter_remaining > 0
            or self.combat.mask_effect_remaining > 0
        ):
            radius = 35 if self.combat.transformation_active else 29
            pygame.draw.ellipse(
                self.screen,
                color,
                pygame.Rect(center[0] - radius, center[1] - radius // 2, radius * 2, radius),
                3,
            )

    def _draw_hud(self) -> None:
        if self.player is None:
            return
        draw_frame(self.screen, pygame.Rect(18, 18, 310, 120), (11, 13, 17))

        title = self.body_font.render(
            f"THE EXILED SAMURAI  ·  LV {self.player.level}",
            True,
            (232, 214, 178),
        )
        self.screen.blit(title, (31, 29))
        pygame.draw.line(self.screen, (84, 68, 51), (31, 57), (312, 57), 1)
        self._draw_stat_bar(31, 69, 174, 13, self.player.health / self.player.max_health, (153, 55, 55))
        self._draw_stat_bar(31, 99, 174, 9, self.player.stamina / self.player.max_stamina, (183, 142, 69))
        self.screen.blit(self.small_font.render("HP", True, (225, 209, 184)), (215, 63))
        self.screen.blit(self.small_font.render("STAMINA", True, (225, 209, 184)), (215, 92))
        weapon_slot = WEAPON_ORDER.index(self.player.weapon_inventory.equipped) + 1
        weapon_label = self.small_font.render(
            f"WEAPON {self.player.weapon_inventory.definition.display_name.upper()}  [{weapon_slot}]",
            True,
            (220, 190, 139),
        )
        self.screen.blit(weapon_label, (31, 116))

        hint = self.small_font.render("WASD MOVE   LMB/RMB ATTACK   1-4/WHEEL WEAPON   V MASK   Q ABILITY   U UPGRADE   E INTERACT", True, (231, 218, 188))
        hint_panel = pygame.Rect(
            (self.SCREEN_SIZE[0] - hint.get_width() - 34) // 2,
            self.SCREEN_SIZE[1] - 49,
            hint.get_width() + 34,
            34,
        )
        draw_frame(self.screen, hint_panel, (12, 13, 17), (94, 77, 58))
        self.screen.blit(hint, (hint_panel.x + 17, hint_panel.y + 8))

        if self.notice_time > 0:
            self._draw_notice(self.notice)

        active_quest = next(
            (
                quest
                for quest in self.quest_log.quests
                if quest.status == QuestStatus.ACTIVE
            ),
            None,
        )
        if active_quest is not None:
            quest_text = self.small_font.render(
                f"QUEST  {active_quest.objective}   [J: JOURNAL]",
                True,
                (231, 211, 170),
            )
            quest_panel = pygame.Rect(
                self.SCREEN_SIZE[0] - quest_text.get_width() - 38,
                18,
                quest_text.get_width() + 20,
                38,
            )
            draw_frame(self.screen, quest_panel, (12, 13, 17), (120, 94, 62))
            self.screen.blit(quest_text, (quest_panel.x + 10, quest_panel.y + 9))

    def _draw_stat_bar(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        ratio: float,
        color: tuple[int, int, int],
    ) -> None:
        bar = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (23, 24, 26), bar)
        fill_width = max(0, min(width, int(width * ratio)))
        if fill_width:
            pygame.draw.rect(self.screen, color, (x + 1, y + 1, max(0, fill_width - 2), height - 2))
            pygame.draw.line(self.screen, tuple(min(255, channel + 35) for channel in color), (x + 2, y + 1), (x + fill_width - 2, y + 1), 1)
        pygame.draw.rect(self.screen, (119, 105, 88), bar, 1)

    def _draw_notice(self, message: str) -> None:
        box = pygame.Rect(300, 548, 680, 110)
        draw_frame(self.screen, box, (14, 14, 18))
        words = message.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if self.body_font.size(candidate)[0] > box.width - 34 and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        for index, line in enumerate(lines[:2]):
            rendered = self.body_font.render(line, True, (230, 215, 190))
            self.screen.blit(rendered, (box.x + 17, box.y + 17 + index * 31))

    def _draw_inventory(self) -> None:
        self._draw_scrim(225)
        panel = pygame.Rect(90, 68, 1100, 584)
        draw_frame(self.screen, panel, (20, 20, 23))
        title = self.title_font.render("ARSENAL & CURSED MASKS", True, (232, 214, 178))
        self.screen.blit(title, title.get_rect(center=(640, 137)))
        subtitle = self.small_font.render(
            "WEAPON FORMS  /  SEALED SPIRITS",
            True,
            (153, 135, 108),
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(640, 150)))
        pygame.draw.line(self.screen, (92, 72, 53), (128, 174), (1152, 174), 1)
        weapons_panel = pygame.Rect(120, 190, 470, 390)
        masks_panel = pygame.Rect(610, 190, 550, 390)
        draw_frame(self.screen, weapons_panel, (24, 24, 27), (104, 83, 61))
        draw_frame(self.screen, masks_panel, (24, 24, 27), (113, 86, 130))
        inventory = self.player.weapon_inventory
        manager = self.player.mask_manager
        weapon_heading = self.body_font.render("WEAPONS", True, (220, 190, 139))
        self.screen.blit(weapon_heading, (weapons_panel.x + 18, weapons_panel.y + 14))
        mask_heading = self.body_font.render(
            f"MASKS  {len(manager.owned)}/5    UPGRADE SEALS {manager.upgrade_tokens}",
            True,
            (205, 178, 225),
        )
        self.screen.blit(mask_heading, (masks_panel.x + 18, masks_panel.y + 14))

        for slot, weapon_type in enumerate(WEAPON_ORDER, start=1):
            definition = WEAPON_DEFINITIONS[weapon_type]
            status = (
                "EQUIPPED"
                if inventory.equipped == weapon_type
                else "OWNED"
                if weapon_type in inventory.owned
                else "LOCKED"
            )
            description = (
                f"Range {definition.attack_range} · speed {definition.attack_speed:.2f} · "
                f"{len(definition.light_combo)}-hit combo"
            )
            y = weapons_panel.y + 54 + (slot - 1) * 70
            card = pygame.Rect(weapons_panel.x + 12, y, weapons_panel.width - 24, 62)
            draw_frame(self.screen, card, (30, 29, 29), (116, 92, 62))
            if weapon_type == WeaponType.KATANA:
                self.screen.blit(pygame.transform.scale(item_icon("katana"), (42, 42)), (card.x + 8, card.y + 10))
            else:
                number = pygame.Rect(card.x + 12, card.y + 14, 34, 34)
                draw_frame(self.screen, number, (34, 30, 27), (135, 102, 62))
                slot_text = self.small_font.render(str(slot), True, (216, 177, 108))
                self.screen.blit(slot_text, slot_text.get_rect(center=number.center))
            name = self.body_font.render(definition.display_name, True, (226, 204, 165))
            self.screen.blit(name, (card.x + 58, card.y + 7))
            detail = self.small_font.render(description, True, (168, 162, 151))
            self.screen.blit(detail, (card.x + 58, card.y + 34))
            badge = pygame.Rect(card.right - 90, card.y + 16, 78, 30)
            draw_frame(self.screen, badge, (34, 30, 27), (135, 102, 62))
            badge_surface = self.small_font.render(status, True, (216, 177, 108))
            self.screen.blit(badge_surface, badge_surface.get_rect(center=badge.center))

        ration_icon = pygame.transform.scale(item_icon("ration"), (40, 40))
        self.screen.blit(ration_icon, (weapons_panel.x + 20, weapons_panel.bottom - 58))
        ration_text = self.body_font.render(f"Travel Rations  x{self.player.rations}", True, (226, 204, 165))
        self.screen.blit(ration_text, (weapons_panel.x + 72, weapons_panel.bottom - 52))

        owned_masks = [mask_type for mask_type in all_mask_types() if mask_type in manager.owned]
        if not owned_masks:
            empty = self.body_font.render("No masks discovered.", True, (165, 153, 171))
            self.screen.blit(empty, empty.get_rect(center=(masks_panel.centerx, masks_panel.centery - 18)))
            hint_mask = self.small_font.render("Story discoveries will reveal sealed masks.", True, (143, 132, 150))
            self.screen.blit(hint_mask, hint_mask.get_rect(center=(masks_panel.centerx, masks_panel.centery + 16)))
        for index, mask_type in enumerate(owned_masks):
            mask = create_mask(mask_type)
            level = manager.level(mask_type)
            y = masks_panel.y + 54 + index * 64
            card = pygame.Rect(masks_panel.x + 12, y, masks_panel.width - 24, 58)
            draw_frame(self.screen, card, (31, 29, 34), (132, 100, 151))
            icon = pygame.transform.scale(item_icon("mask"), (42, 42))
            self.screen.blit(icon, (card.x + 8, card.y + 8))
            title_color = (222, 194, 237) if manager.equipped == mask_type else (207, 194, 213)
            mask_name = self.body_font.render(f"{mask.display_name}  ·  LV {level}", True, title_color)
            self.screen.blit(mask_name, (card.x + 60, card.y + 5))
            mask_detail = self.small_font.render(
                f"{mask.ability.name}  /  {mask.description}",
                True,
                (166, 157, 174),
            )
            self.screen.blit(mask_detail, (card.x + 60, card.y + 31))
            if manager.equipped == mask_type:
                badge = self.small_font.render("EQUIPPED", True, (223, 186, 239))
                self.screen.blit(badge, (card.right - badge.get_width() - 12, card.y + 5))

        hint = self.small_font.render("V switch mask  ·  Q ability  ·  U upgrade  ·  I or ESC to return", True, (181, 169, 147))
        self.screen.blit(hint, hint.get_rect(center=(640, 587)))

    def _draw_quest_offer(self) -> None:
        quest = self.quest_log.first_available()
        if quest is None:
            return
        self._draw_scrim(215)
        panel = pygame.Rect(190, 150, 900, 420)
        draw_frame(self.screen, panel, (21, 20, 23))
        title = self.title_font.render("A NEW REQUEST", True, (232, 214, 178))
        self.screen.blit(title, title.get_rect(center=(640, 203)))
        pygame.draw.line(self.screen, (92, 72, 53), (232, 239), (1048, 239), 1)
        quest_icon = item_icon("shrine")
        self.screen.blit(quest_icon, (255, 290))
        quest_title = self.body_font.render(quest.title, True, (220, 184, 124))
        self.screen.blit(quest_title, (330, 275))
        self._draw_wrapped_text(
            quest.description,
            self.small_font,
            (330, 314),
            690,
            (194, 187, 172),
        )
        objective = self.small_font.render(
            f"Objective: {quest.objective}",
            True,
            (194, 187, 172),
        )
        self.screen.blit(objective, (330, 382))
        pygame.draw.line(self.screen, (73, 62, 49), (330, 418), (1025, 418), 1)
        controls = self.small_font.render(
            "ENTER  ACCEPT       ESC  DECLINE",
            True,
            (229, 205, 164),
        )
        self.screen.blit(controls, controls.get_rect(center=(640, 500)))

    def _draw_quest_log(self) -> None:
        self._draw_scrim(225)
        panel = pygame.Rect(150, 95, 980, 550)
        draw_frame(self.screen, panel, (20, 20, 23))
        title = self.title_font.render("QUEST JOURNAL", True, (232, 214, 178))
        self.screen.blit(title, title.get_rect(center=(640, 149)))
        subtitle = self.small_font.render(
            "VILLAGE RECORDS  /  NORTHERN PROVINCE",
            True,
            (153, 135, 108),
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(640, 179)))
        pygame.draw.line(self.screen, (92, 72, 53), (190, 203), (1090, 203), 1)
        list_panel = pygame.Rect(190, 221, 294, 350)
        detail_panel = pygame.Rect(506, 221, 584, 350)
        draw_frame(self.screen, list_panel, (25, 25, 28), (116, 92, 62))
        draw_frame(self.screen, detail_panel, (25, 25, 28), (116, 92, 62))
        section = self.small_font.render("KNOWN REQUESTS", True, (183, 155, 111))
        self.screen.blit(section, (list_panel.x + 18, list_panel.y + 17))

        if not self.quest_log.quests:
            empty = self.body_font.render("No quests discovered.", True, (184, 176, 160))
            self.screen.blit(empty, empty.get_rect(center=detail_panel.center))
        else:
            for index, quest in enumerate(self.quest_log.quests[:3]):
                y = list_panel.y + 54 + index * 86
                entry = pygame.Rect(list_panel.x + 12, y, list_panel.width - 24, 72)
                draw_frame(self.screen, entry, (37, 34, 31), (135, 102, 62))
                status = quest.status.name.replace("_", " ")
                status_color = (
                    (177, 139, 86)
                    if quest.status == QuestStatus.ACTIVE
                    else (133, 153, 118)
                    if quest.status == QuestStatus.COMPLETED
                    else (157, 145, 123)
                )
                status_surface = self.small_font.render(status, True, status_color)
                self.screen.blit(status_surface, (entry.x + 11, entry.y + 9))
                title_surface = self.small_font.render(
                    quest.title,
                    True,
                    (226, 204, 165),
                )
                self.screen.blit(title_surface, (entry.x + 11, entry.y + 37))

            quest = next((q for q in self.quest_log.quests if q.status == QuestStatus.ACTIVE), None)
            if quest is None:
                quest = next((q for q in self.quest_log.quests if q.status == QuestStatus.AVAILABLE), self.quest_log.quests[-1])
            self.screen.blit(item_icon("shrine"), (detail_panel.x + 20, detail_panel.y + 22))
            quest_title = self.body_font.render(quest.title, True, (220, 184, 124))
            self.screen.blit(quest_title, (detail_panel.x + 88, detail_panel.y + 31))
            status = quest.status.name.replace("_", " ")
            status_surface = self.small_font.render(status, True, (183, 155, 111))
            self.screen.blit(status_surface, (detail_panel.x + 88, detail_panel.y + 62))
            pygame.draw.line(
                self.screen,
                (73, 62, 49),
                (detail_panel.x + 22, detail_panel.y + 102),
                (detail_panel.right - 22, detail_panel.y + 102),
                1,
            )
            self._draw_wrapped_text(
                quest.description,
                self.small_font,
                (detail_panel.x + 24, detail_panel.y + 126),
                detail_panel.width - 48,
                (194, 187, 172),
            )
            objective_title = self.small_font.render(
                "CURRENT OBJECTIVE",
                True,
                (183, 155, 111),
            )
            self.screen.blit(objective_title, (detail_panel.x + 24, detail_panel.y + 205))
            self._draw_wrapped_text(
                quest.objective,
                self.body_font,
                (detail_panel.x + 24, detail_panel.y + 229),
                detail_panel.width - 48,
                (220, 211, 190),
            )
            # The campaign chronicle reveals one lore entry per story milestone.
            lore_key = self.campaign.lore_unlocked[-1] if self.campaign.lore_unlocked else None
            if lore_key:
                lore = LORE_FRAGMENTS[lore_key]
                lore_label = self.small_font.render(
                    f"CHRONICLE  /  {lore['region'].upper()}",
                    True,
                    (191, 151, 103),
                )
                self.screen.blit(lore_label, (detail_panel.x + 24, detail_panel.y + 278))
                self._draw_wrapped_text(
                    lore["text"],
                    self.small_font,
                    (detail_panel.x + 24, detail_panel.y + 302),
                    detail_panel.width - 48,
                    (190, 183, 169),
                )
            else:
                lore_label = self.small_font.render(
                    "CHRONICLE  /  No fragments discovered yet",
                    True,
                    (130, 119, 103),
                )
                self.screen.blit(lore_label, (detail_panel.x + 24, detail_panel.y + 290))
        hint = self.small_font.render("Press J or ESC to return to the village", True, (181, 169, 147))
        self.screen.blit(hint, hint.get_rect(center=(640, 608)))

    def _draw_slash_effects(self) -> None:
        """Render short, mask-themed slash trails when a player hit becomes active."""
        if self.player is None:
            return
        age = self.visual_time - self._slash_effect_started
        duration = 0.24 if self._slash_effect_heavy else 0.18
        if age < 0 or age >= duration:
            return

        palettes = {
            MaskType.WRATH: ((255, 111, 45), (255, 205, 91)),
            MaskType.GRIEF: ((91, 211, 220), (210, 250, 245)),
            MaskType.FEAR: ((105, 204, 119), (195, 244, 153)),
            MaskType.PRIDE: ((226, 183, 83), (255, 239, 174)),
            MaskType.DECEPTION: ((174, 111, 238), (235, 194, 255)),
            None: ((205, 220, 225), (255, 255, 255)),
        }
        primary, highlight = palettes.get(self._slash_effect_mask, palettes[None])
        progress = age / duration
        alpha_width = max(1, int(6 * (1.0 - progress)))
        origin = pygame.Vector2(
            self.player.rect.centerx - round(self.camera.x),
            self.player.rect.centery - round(self.camera.y) - 5,
        )
        vectors = {
            "up": pygame.Vector2(0, -1), "down": pygame.Vector2(0, 1),
            "left": pygame.Vector2(-1, 0), "right": pygame.Vector2(1, 0),
        }
        forward = vectors.get(self._slash_effect_direction, pygame.Vector2(0, 1))
        side = pygame.Vector2(-forward.y, forward.x)
        reach = 43 if not self._slash_effect_heavy else 59
        sweep = 29 + 12 * math.sin(progress * math.pi)
        center = origin + forward * 17
        start = center - side * sweep - forward * 5
        end = center + side * sweep + forward * 5

        def glow_line(a, b, color, width):
            pygame.draw.line(self.screen, color, a, b, width)
            pygame.draw.circle(self.screen, color, a, max(1, width // 2))
            pygame.draw.circle(self.screen, color, b, max(1, width // 2))

        # Each mask has its own visual language, not just a different color.
        mask = self._slash_effect_mask
        if mask == MaskType.WRATH:
            # Jagged flame cleave with ember sparks.
            points = [start, center - side * 12 + forward * 12,
                      center + side * 2 - forward * 8, end]
            pygame.draw.lines(self.screen, primary, False, points, alpha_width + 2)
            glow_line(start + forward * 4, end + forward * 4, highlight, 2)
            for i in range(4):
                t = (i + 1) / 5
                point = start.lerp(end, t) + forward * math.sin(self.visual_time * 28 + i) * 8
                pygame.draw.circle(self.screen, highlight, (int(point.x), int(point.y)), 2)
        elif mask == MaskType.GRIEF:
            # Flowing water crescent with a trailing second ripple.
            rect = pygame.Rect(0, 0, int(sweep * 2 + 12), int(reach * 1.25))
            rect.center = (int(center.x), int(center.y))
            pygame.draw.arc(self.screen, primary, rect, math.pi * 0.12, math.pi * 0.88, alpha_width + 2)
            pygame.draw.arc(self.screen, highlight, rect.inflate(-12, -10), math.pi * 0.16, math.pi * 0.84, 2)
            glow_line(start + forward * 7, end + forward * 7, (119, 225, 229), 2)
        elif mask == MaskType.FEAR:
            # Broken shadow streaks that snap across the target.
            for offset in (-13, 0, 13):
                a = origin + forward * 5 + side * offset
                b = a + forward * reach + side * (offset * -0.65)
                glow_line(a, b, primary if offset else highlight, 2)
        elif mask == MaskType.PRIDE:
            # Precise golden cross-cut, with a sharp central glint.
            glow_line(start, end, primary, alpha_width + 2)
            glow_line(center - forward * 12, center + forward * 24, highlight, 2)
            pygame.draw.circle(self.screen, highlight, (int(center.x), int(center.y)), 4, 1)
        elif mask == MaskType.DECEPTION:
            # Twin offset violet cuts that cross and leave an afterimage.
            glow_line(start + forward * 7, end - forward * 7, primary, alpha_width + 1)
            glow_line(start - forward * 5, end + forward * 5, highlight, 2)
            glow_line(start + side * 7, end + side * 7, (124, 83, 184), 1)
        else:
            # Unmasked katana: clean steel arc.
            glow_line(start, end, primary, alpha_width + 1)
            glow_line(start + forward * 5, end + forward * 5, highlight, 1)

    def _draw_realtime_combat(self) -> None:
        if self.combat is None or self.player is None:
            return
        camera = self.camera
        hitbox = self.combat.visible_hitbox
        if hitbox is not None:
            visible = hitbox.move(-round(camera.x), -round(camera.y))
            pygame.draw.line(
                self.screen,
                (205, 230, 219),
                (self.player.rect.centerx - round(camera.x), self.player.rect.bottom - round(camera.y) - 5),
                visible.center,
                3,
            )
            pygame.draw.rect(self.screen, (175, 220, 206), visible, 2, border_radius=5)

        enemy = self.combat.enemy
        decoy = self.combat.phantom_decoy
        if decoy is not None:
            decoy_rect = decoy.rect.move(-round(camera.x), -round(camera.y))
            pulse = int(28 * abs(math.sin(self.visual_time * 7.0)))
            pygame.draw.ellipse(self.screen, (177, 137, 220), decoy_rect.inflate(12 + pulse, 10 + pulse), 2)
            pygame.draw.ellipse(self.screen, (112, 91, 151), decoy_rect, 1)
        panel = pygame.Rect(self.SCREEN_SIZE[0] - 333, 18, 315, 108)
        draw_frame(self.screen, panel, (12, 13, 17), (138, 82, 65))
        label = self.small_font.render(enemy.name.upper(), True, (230, 211, 177))
        self.screen.blit(label, (panel.x + 13, panel.y + 10))
        self._draw_stat_bar(
            panel.x + 13,
            panel.y + 35,
            panel.width - 26,
            12,
            enemy.health / max(1, enemy.max_health),
            (157, 55, 55),
        )
        phase = "READY"
        if self.combat.player_attack is not None:
            phase = self.combat.player_attack.state.name
        detail = self.small_font.render(
            f"{enemy.health}/{enemy.max_health} HP    COMBO {self.combat.combo.step}/3    {phase}",
            True,
            (197, 184, 162),
        )
        self.screen.blit(detail, (panel.x + 13, panel.y + 58))
        message = self.small_font.render(
            self.combat.message,
            True,
            (224, 202, 164),
        )
        self.screen.blit(message, (panel.x + 13, panel.y + 82))

        enemy_rect = enemy.rect.move(-round(camera.x), -round(camera.y))
        if self.combat.enemy_state.hit_reaction_remaining > 0:
            pygame.draw.ellipse(
                self.screen,
                (226, 107, 84),
                enemy_rect.inflate(12, 10),
                2,
            )
        elif self.combat.enemy_attack is not None:
            attack_state = self.combat.enemy_attack.state
            telegraph_color = (212, 151, 83) if attack_state.name == "STARTUP" else (225, 96, 78)
            pygame.draw.ellipse(self.screen, telegraph_color, enemy_rect.inflate(15, 13), 2)
            if attack_state.name == "ACTIVE":
                pygame.draw.line(
                    self.screen,
                    (234, 133, 95),
                    enemy_rect.center,
                    (
                        (self.combat.phantom_decoy.rect.centerx if self.combat.phantom_decoy else self.player.rect.centerx) - round(camera.x),
                        (self.combat.phantom_decoy.rect.centery if self.combat.phantom_decoy else self.player.rect.centery) - round(camera.y),
                    ),
                    4,
                )

        if self.combat.player_state.hit_reaction_remaining > 0:
            player_rect = self.player.rect.move(-round(camera.x), -round(camera.y))
            pygame.draw.ellipse(
                self.screen,
                (226, 107, 84),
                player_rect.inflate(10, 8),
                2,
            )

    def _draw_wrapped_text(
        self,
        text: str,
        font: pygame.font.Font,
        position: tuple[int, int],
        max_width: int,
        color: tuple[int, int, int],
    ) -> None:
        lines: list[str] = []
        current = ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] > max_width and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        for index, line in enumerate(lines[:2]):
            rendered = font.render(line, True, color)
            self.screen.blit(rendered, (position[0], position[1] + index * 28))
        else:
            journal_hint = self.small_font.render("J  QUEST JOURNAL", True, (208, 190, 151))
            journal_panel = pygame.Rect(self.SCREEN_SIZE[0] - journal_hint.get_width() - 38, 18, journal_hint.get_width() + 20, 38)
            draw_frame(self.screen, journal_panel, (12, 13, 17), (100, 82, 61))
            self.screen.blit(journal_hint, (journal_panel.x + 10, journal_panel.y + 9))
