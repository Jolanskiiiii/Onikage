# ONIKAGE: The Curse of the Fallen Samurai

A traditional top-down 2D pixel-art samurai adventure built with Python 3.13 and Pygame 2.6.

## Run

Install Pygame, then start the game from this folder:

```powershell
py -3.13 -m pip install pygame==2.6.1
py -3.13 main.py
```

## Controls

- **WASD** or **Arrow keys**: Move
- **Shift**: Sprint
- **E**: Interact
- **Left mouse button**: Light attack (three-hit combo)
- **Right mouse button**: Heavy attack (committed strike)
- **1–4** or **mouse wheel**: Select/cycle owned weapons
- **V**: Switch between acquired masks
- **Q**: Use the equipped mask ability (hold/release for Wrath)
- **U**: Upgrade the equipped mask when an upgrade seal is available
- **C**: Engage a nearby enemy
- **I**: Inventory
- **J**: Quest journal
- **F11**: Toggle fullscreen

Akihiro starts with the Katana. The Yari is found through village exploration, Dual Blades are earned by completing the existing shrine quest, and the Odachi is awarded for defeating the existing wraith encounter. Weapon unlocks and the equipped weapon are saved automatically.

Cursed Masks are discovered only as the existing story progresses: the shrine quest reveals Shadows and opens the Tengu cache, the wraith reveals Wrath and opens the Suffering relic, and Onikage awakens after the four lesser masks are collected. Mask energy, upgrades, ownership, and equipment are saved automatically.

See [PROGRESS_REPORT.md](PROGRESS_REPORT.md) for gameplay details and project status.

## Asset licenses

The bundled DotGothic16 font is licensed under the SIL Open Font License; see
[`onikage/assets/fonts/OFL.txt`](onikage/assets/fonts/OFL.txt).
The selected Kenney RPG Audio effects are CC0; see
[`onikage/assets/audio/LICENSE.txt`](onikage/assets/audio/LICENSE.txt).


## Visual direction

ONIKAGE uses a traditional 2D top-down perspective. The current art is palette-driven procedural pixel art; the latest visual pass adds small character, enemy, terrain, roof, and tree details while preserving existing sprite dimensions and gameplay systems. External sprite sheets can be integrated later after their tile size, palette, and license are checked.


## Campaign development note

The Burning Village chapter is now connected as an explorable top-down area after
completing the Kagehama shrine quest. Approach the eastern scorched-pass gate
and press **E** to enter; use the return gate in the Burning Village to go back.
This is an early playable environment pass: its visual palette, ember/fire dressing,
entry/return travel, and Ashen Oni encounter placeholder are integrated. The
Ashen Oni currently reuses the existing Wraith sprite and combat behavior; a
dedicated guardian sprite, bespoke boss phases, and mask reward sequence remain
unfinished.
