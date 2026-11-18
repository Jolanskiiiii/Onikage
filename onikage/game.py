import math

import pygame

from onikage.art.characters.player_sprite import battle_player_frame
from onikage.art.audio.sfx import GameAudio
from onikage.art.environments.battlefield import draw_battlefield
from onikage.art.enemies.wraith_sprite import battle_wraith_frame
from onikage.art.fonts.ui import create_ui_fonts
from onikage.art.ui.panels import draw_frame, item_icon
from onikage.game_state import GameManager, GameState
from onikage.combat import BattleSystem
from onikage.dialogue import DialogueSystem
from onikage.main_menu import MainMenu
from onikage.player import Player
from onikage.quests import Quest, QuestLog, QuestStatus
from onikage.village import VillageWorld


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
        self.battle: BattleSystem | None = None
        self.audio = GameAudio()
        self.quest_log = QuestLog()
        self.notice = ""
        self.notice_time = 0.0
        self.visual_time = 0.0

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
                if action == "new_game":
                    self._start_new_game()
                elif action == "settings":
                    self.state_manager.transition_to(GameState.SETTINGS)
                elif action == "exit":
                    self.running = False
            elif state == GameState.SETTINGS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state_manager.transition_to(GameState.MENU)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.menu.back_button.collidepoint(event.pos):
                        self.state_manager.transition_to(GameState.MENU)
            elif state == GameState.EXPLORATION:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
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
            elif state == GameState.COMBAT:
                self._handle_combat_event(event)

    def _start_battle(self) -> None:
        if self.player is None or self.world is None:
            return
        enemy = self.world.find_enemy(self.player.interaction_point())
        if enemy is None:
            self.notice = "No enemy nearby. Follow the lantern path north."
            self.notice_time = 3.0
            return
        self.battle = BattleSystem(self.player, enemy)
        self.state_manager.transition_to(GameState.COMBAT)

    def _handle_combat_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN or self.battle is None:
            return

        if self.battle.finished:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.battle.result == "victory" and not self.battle.experience_awarded:
                    self.player.experience += self.battle.enemy.experience_reward
                    self.battle.experience_awarded = True
                    if self.world is not None:
                        self.world.obstacles = [
                            obstacle
                            for obstacle in self.world.obstacles
                            if obstacle != self.battle.enemy.rect
                        ]
                    self.notice = (
                        f"Victory! You gained "
                        f"{self.battle.enemy.experience_reward} experience."
                    )
                    self.notice_time = 4.0
                elif self.battle.result == "defeat" and self.player is not None:
                    self.player.health = max(1, self.player.max_health // 2)
                    self.notice = "You retreat to the village and recover. Rest before trying again."
                    self.notice_time = 4.0
                self.battle = None
                self.state_manager.transition_to(GameState.EXPLORATION)
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self.battle.move_selection(-1)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.battle.move_selection(1)
        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            self._choose_battle_command(event.key - pygame.K_1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._choose_battle_command(self.battle.selected_command)

    def _choose_battle_command(self, command: int) -> None:
        if self.battle is None:
            return

        previous_enemy_health = self.battle.enemy.health
        previous_stamina = self.battle.player.stamina
        previous_rations = self.battle.player.rations
        self.battle.choose_command(command)
        succeeded = (
            (command == 0 and self.battle.enemy.health < previous_enemy_health)
            or command == 1
            or (command == 2 and self.battle.player.stamina < previous_stamina)
            or (command == 3 and self.battle.player.rations < previous_rations)
        )
        if succeeded:
            self.audio.play_battle_action(command)

    def _start_new_game(self) -> None:
        self.world = VillageWorld()
        self.player = Player(755, 580)
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

    def _update(self, dt: float) -> None:
        self.visual_time += dt
        if self.notice_time > 0:
            self.notice_time = max(0.0, self.notice_time - dt)
        if self.state_manager.current_state != GameState.EXPLORATION:
            return
        if self.player is None or self.world is None:
            return

        self.world.update(dt)
        previous_position = self.player.position.copy()
        self.player.update(dt, pygame.key.get_pressed(), self.world.obstacles)
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
            self.battle = BattleSystem(self.player, enemy)
            self.state_manager.transition_to(GameState.COMBAT)
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
        elif state == GameState.COMBAT:
            self._draw_combat()

    def _draw_settings(self) -> None:
        self._draw_scrim(220)

        title = self.title_font.render("SETTINGS", True, (235, 220, 189))
        self.screen.blit(title, title.get_rect(center=(640, 275)))
        fullscreen_text = "ON" if self.fullscreen else "OFF"
        details = self.body_font.render(
            f"Fullscreen: {fullscreen_text}   (F11 to toggle)",
            True,
            (190, 185, 176),
        )
        self.screen.blit(details, details.get_rect(center=(640, 355)))
        self.menu.draw_back_button(self.screen, self.small_font)

    def _draw_scrim(self, alpha: int) -> None:
        self.overlay_surface.fill((8, 8, 13, alpha))
        self.screen.blit(self.overlay_surface, (0, 0))

    def _draw_exploration(self) -> None:
        if self.player is None or self.world is None:
            self.screen.fill((12, 16, 18))
            return

        camera = self.camera
        self.world.draw(self.screen, camera, self.player.rect.bottom)
        self.player.draw(
            self.screen,
            (self.player.rect.x - round(camera.x), self.player.rect.y - round(camera.y)),
        )
        self.world.draw_foreground(self.screen, camera, self.player.rect.bottom)
        self._draw_hud()

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

        hint = self.small_font.render("WASD / ARROWS MOVE   SHIFT SPRINT   E INTERACT   C BATTLE   I ITEMS   J QUESTS", True, (231, 218, 188))
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
        panel = pygame.Rect(180, 88, 920, 544)
        draw_frame(self.screen, panel, (20, 20, 23))
        title = self.title_font.render("TRAVEL PACK", True, (232, 214, 178))
        self.screen.blit(title, title.get_rect(center=(640, 137)))
        subtitle = self.small_font.render(
            "FIELD GEAR  /  THE ROAD NORTH",
            True,
            (153, 135, 108),
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(640, 170)))
        pygame.draw.line(self.screen, (92, 72, 53), (218, 187), (1062, 187), 1)
        entries = (
            ("Worn Katana", "A well-used blade. Still dependable.", "katana", "EQUIPPED"),
            ("Travel Rations", "Simple provisions for the road.", "ration", f"x{self.player.rations if self.player else 0}"),
            ("Supernatural Masks", "No masks discovered.", "mask", "LOCKED"),
        )
        for index, (name, description, icon_kind, badge_text) in enumerate(entries):
            y = 204 + index * 112
            card = pygame.Rect(220, y, 840, 94)
            draw_frame(self.screen, card, (27, 27, 30), (116, 92, 62))
            self.screen.blit(item_icon(icon_kind), (card.x + 17, card.y + 15))
            name_surface = self.body_font.render(name, True, (226, 204, 165))
            self.screen.blit(name_surface, (card.x + 87, card.y + 17))
            description_surface = self.small_font.render(
                description,
                True,
                (168, 162, 151),
            )
            self.screen.blit(description_surface, (card.x + 87, card.y + 53))
            badge = pygame.Rect(card.right - 136, card.y + 31, 112, 34)
            draw_frame(self.screen, badge, (34, 30, 27), (135, 102, 62))
            badge_surface = self.small_font.render(badge_text, True, (216, 177, 108))
            self.screen.blit(badge_surface, badge_surface.get_rect(center=badge.center))
        hint = self.small_font.render("Press I or ESC to return to the village", True, (181, 169, 147))
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

    def _draw_combat(self) -> None:
        if self.battle is None:
            self.screen.fill((12, 12, 18))
            return

        self._draw_combat_background()
        frame = int(self.visual_time * 2) % 3
        pygame.draw.ellipse(self.screen, (12, 15, 19), (244, 394, 145, 22))
        pygame.draw.ellipse(self.screen, (12, 15, 19), (850, 396, 157, 22))
        if self.player is not None:
            self.screen.blit(
                battle_player_frame(self.player.direction, frame),
                (252, 205),
            )
        self.screen.blit(
            battle_wraith_frame(int(self.visual_time * 2) % 2),
            (854, 205),
        )
        if "spirit light" in self.battle.message.lower():
            shimmer = int(130 + 55 * abs(math.sin(self.visual_time * 7)))
            slash = (171, 230, min(255, shimmer + 20))
            pygame.draw.line(self.screen, slash, (385, 295), (782, 214), 5)
            pygame.draw.line(self.screen, (235, 244, 217), (400, 290), (790, 211), 2)

        title = self.title_font.render("ENCOUNTER", True, (231, 214, 181))
        self.screen.blit(title, title.get_rect(center=(640, 52)))
        self._draw_battle_status(
            pygame.Rect(112, 432, 430, 94),
            "EXILED SAMURAI",
            self.player.health if self.player else 0,
            self.player.max_health if self.player else 1,
            self.player.stamina if self.player else 0,
            self.player.max_stamina if self.player else 1,
        )
        self._draw_battle_status(
            pygame.Rect(738, 432, 430, 94),
            self.battle.enemy.name.upper(),
            self.battle.enemy.health,
            self.battle.enemy.max_health,
            None,
            None,
        )

        panel = pygame.Rect(90, 541, 1100, 147)
        draw_frame(self.screen, panel, (13, 14, 19))
        self._draw_wrapped_text(
            self.battle.message,
            self.body_font,
            (panel.x + 24, panel.y + 13),
            panel.width - 48,
            (231, 218, 193),
        )

        if self.battle.finished:
            label = "VICTORY" if self.battle.result == "victory" else "DEFEAT"
            result_panel = pygame.Rect(407, 212, 466, 112)
            draw_frame(self.screen, result_panel, (28, 23, 22), (190, 146, 83))
            result = self.title_font.render(
                label,
                True,
                (232, 203, 151) if self.battle.result == "victory" else (196, 123, 108),
            )
            self.screen.blit(result, result.get_rect(center=(640, 252)))
            hint = self.small_font.render("Press Enter to return to the village", True, (209, 195, 172))
            self.screen.blit(hint, hint.get_rect(center=(640, 291)))
            return

        for index, command in enumerate(self.battle.COMMANDS):
            x = 112 + index * 268
            selected = index == self.battle.selected_command
            button = pygame.Rect(x, 614, 248, 51)
            draw_frame(
                self.screen,
                button,
                (48, 37, 31) if selected else (24, 25, 29),
                (211, 170, 105) if selected else (86, 79, 69),
            )
            pygame.draw.rect(
                self.screen,
                (111, 63, 45) if selected else (41, 42, 44),
                (button.x + 12, button.y + 11, 30, 28),
            )
            label = self.small_font.render(
                str(index + 1),
                True,
                (236, 218, 187) if selected else (173, 166, 152),
            )
            self.screen.blit(label, label.get_rect(center=(button.x + 27, button.centery)))
            command_label = self.small_font.render(
                command.upper(),
                True,
                (236, 218, 187) if selected else (173, 166, 152),
            )
            self.screen.blit(command_label, command_label.get_rect(center=(button.centerx + 20, button.centery)))

    def _draw_combat_background(self) -> None:
        draw_battlefield(self.screen, self.visual_time)

    def _draw_battle_status(
        self,
        panel: pygame.Rect,
        name: str,
        health: int,
        max_health: int,
        stamina: float | None,
        max_stamina: float | None,
    ) -> None:
        draw_frame(self.screen, panel, (13, 14, 19), (150, 117, 77))
        label = self.small_font.render(name, True, (230, 211, 177))
        self.screen.blit(label, (panel.x + 17, panel.y + 10))
        self._draw_stat_bar(
            panel.x + 16,
            panel.y + 39,
            panel.width - 32,
            13,
            max(0, health) / max(1, max_health),
            (157, 55, 55),
        )
        hp_text = self.small_font.render(f"HP  {health} / {max_health}", True, (221, 213, 197))
        self.screen.blit(hp_text, (panel.x + 16, panel.y + 61))
        if stamina is not None and max_stamina is not None:
            self._draw_stat_bar(
                panel.x + panel.width - 126,
                panel.y + 66,
                108,
                8,
                stamina / max(1, max_stamina),
                (185, 140, 66),
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
