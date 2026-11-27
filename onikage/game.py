import math

import pygame

from onikage.art.audio.sfx import GameAudio
from onikage.art.fonts.ui import create_ui_fonts
from onikage.art.ui.panels import draw_frame, item_icon
from onikage.game_state import GameManager, GameState
from onikage.combat import RealtimeCombat
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
        self.save_manager = SaveManager()
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
                        self.menu.set_resume_available(True)
                        self.state_manager.transition_to(GameState.MENU)
                    elif event.key == pygame.K_i:
                        self.audio.play_ui(opening=True)
                        self.state_manager.transition_to(GameState.INVENTORY)
                    elif event.key == pygame.K_j:
                        self.audio.play_ui(opening=True)
                        self.state_manager.transition_to(GameState.QUEST_LOG)
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
            acquired_odachi = self.player.weapon_inventory.acquire(WeaponType.ODACHI)
            acquired_masks = self.player.mask_manager.advance_story(WRAITH_PROGRESS)
            self.combat.experience_awarded = True
            if self.world is not None:
                self.world.obstacles = [
                    obstacle
                    for obstacle in self.world.obstacles
                    if obstacle is not self.combat.enemy.rect
                ]
            self.notice = f"Victory! You gained {reward} experience."
            if acquired_odachi:
                self.notice += " Odachi acquired."
            if acquired_masks:
                names = ", ".join(create_mask(mask).display_name for mask in acquired_masks)
                self.notice += f" {names} mask discovered."
            self.notice_time = 4.0
            self._save_progress()
        elif self.combat.result == "defeat":
            self.player.health = max(1, self.player.max_health // 2)
            self.notice = "You retreat to the village and recover. Rest before trying again."
            self.notice_time = 4.0
        self.combat = None

    def _start_new_game(self) -> None:
        self.world = VillageWorld()
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
        self.state_manager.transition_to(GameState.EXPLORATION)

    def _continue_game(self) -> None:
        save = self.save_manager.load()
        if save is None:
            self.menu.set_continue_available(False)
            self.notice = "No saved journey is available."
            self.notice_time = 3.0
            return

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
        quest = self.quest_log.get("village_shrine_prayer")
        if quest.quest_id in save.active_quest_ids or quest.quest_id in save.completed_quest_ids:
            self.quest_log.accept(quest.quest_id)
        if quest.quest_id in save.completed_quest_ids:
            self.quest_log.complete(quest.quest_id)

        self.combat = None
        self.dialogue.active = False
        self.notice = "Journey continued."
        self.notice_time = 2.5
        self.camera.update(self._camera_target())
        self.menu.set_resume_available(True)
        self.state_manager.transition_to(GameState.EXPLORATION)
        self._save_progress()

    def _save_progress(self) -> None:
        if self.player is None or self.world is None:
            return
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
            )
        )
        self.menu.set_continue_available(True, "Continue your journey")

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
            self.audio.play_combat_attack(heavy=mask.ability.kind == MaskAbilityKind.LIFE_DRAIN)
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
        enemy = self.world.find_enemy(self.player.interaction_point())
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
        self.world.draw_foreground(self.screen, camera, self.player.rect.bottom)
        self.world.draw_mask_pickups(
            self.screen,
            camera,
            self.player.rect.bottom,
            self.player.mask_manager,
            foreground=True,
        )
        self._draw_hud()
        self._draw_mask_hud()
        self._draw_realtime_combat()
        self._draw_mask_feedback()

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
            MaskType.SHADOWS: (159, 119, 202),
            MaskType.TENGU: (111, 204, 207),
            MaskType.SUFFERING: (117, 190, 126),
            MaskType.ONIKAGE: (195, 59, 76),
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
                f"QUEST: {active_quest.objective}",
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

            quest = self.quest_log.quests[0]
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
                "OBJECTIVE",
                True,
                (183, 155, 111),
            )
            self.screen.blit(objective_title, (detail_panel.x + 24, detail_panel.y + 220))
            self._draw_wrapped_text(
                quest.objective,
                self.body_font,
                (detail_panel.x + 24, detail_panel.y + 248),
                detail_panel.width - 48,
                (220, 211, 190),
            )
        hint = self.small_font.render("Press J or ESC to return to the village", True, (181, 169, 147))
        self.screen.blit(hint, hint.get_rect(center=(640, 608)))

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
                        self.player.rect.centerx - round(camera.x),
                        self.player.rect.centery - round(camera.y),
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
