import pygame

from onikage.enemy import Enemy
from onikage.player import Player


class BattleSystem:
    """Resolves player commands and enemy turns for one encounter."""

    COMMANDS = ("Attack", "Defend", "Spirit Slash", "Use Ration")

    def __init__(self, player: Player, enemy: Enemy) -> None:
        self.player = player
        self.enemy = enemy
        self.selected_command = 0
        self.defending = False
        self.finished = False
        self.result: str | None = None
        self.experience_awarded = False
        self.message = f"A {enemy.name} blocks the forest path!"

    def move_selection(self, direction: int) -> None:
        if self.finished:
            return
        self.selected_command = (
            self.selected_command + direction
        ) % len(self.COMMANDS)

    def choose_command(self, command: int | None = None) -> None:
        if self.finished:
            return

        selected = self.selected_command if command is None else command
        if not 0 <= selected < len(self.COMMANDS):
            raise ValueError(f"Unknown battle command index: {selected}.")

        if selected == 0:
            damage = 20 + self.player.level * 2
            self.enemy.health = max(0, self.enemy.health - damage)
            self.message = f"You strike with your katana for {damage} damage."
        elif selected == 1:
            self.defending = True
            self.message = "You take a guarded stance and brace for the counterattack."
        elif selected == 2:
            if self.player.stamina < 25:
                self.message = "Not enough stamina for Spirit Slash. Choose another action."
                return
            self.player.stamina -= 25
            damage = 36 + self.player.level * 3
            self.enemy.health = max(0, self.enemy.health - damage)
            self.message = f"Your blade flashes with spirit light: {damage} damage!"
        else:
            if self.player.rations <= 0:
                self.message = "Your travel pack is empty. Choose another action."
                return
            if self.player.health >= self.player.max_health:
                self.message = "Your health is already full. Save the ration for later."
                return
            self.player.rations -= 1
            healing = min(35, self.player.max_health - self.player.health)
            self.player.health += healing
            self.message = f"You eat a travel ration and recover {healing} health."

        if self.enemy.health <= 0:
            self.finished = True
            self.result = "victory"
            self.message = f"The {self.enemy.name} fades into the mist. Victory!"
            return

        self._enemy_turn()

    def _enemy_turn(self) -> None:
        damage = self.enemy.attack_power
        if self.defending:
            damage = max(1, damage // 2)
            self.defending = False
            self.message += f" The wraith strikes your guard for {damage} damage."
        else:
            self.message += f" The wraith claws at you for {damage} damage."

        self.player.health = max(0, self.player.health - damage)
        if self.player.health <= 0:
            self.finished = True
            self.result = "defeat"
            self.message = "The wraith overwhelms you. Press Enter to retreat."
