# ONIKAGE: The Curse of the Five Masks

## Project progress

**Current milestone:** Milestone 1 complete; the next milestone is the campaign foundation and prologue.

**Development environment:** Python 3.13.17 and Pygame 2.6.1.

## Baseline gap analysis

| Area | Working foundation | Remaining gap |
|---|---|---|
| Startup and UI | Animated title screen, New Game, Settings, Exit, fullscreen, shared framed UI | Continue was disabled; campaign menus and the complete item/equipment interface are not implemented |
| Exploration | Controllable samurai, collision, camera, village, cedar forest, signs, shrine, Hana | Only two small maps; no five-region campaign, chapter gates, or full cast |
| Story and quests | Three Hana dialogue lines, one accept/complete shrine quest | No prologue, seven-chapter story, dialogue choices, major character arcs, or optional quest chain |
| Combat and growth | Four turn-based commands, one wraith type, basic XP and player stats | No mask abilities, equipment, meaningful leveling, varied enemies, or eight boss encounters |
| Inventory and persistence | Rations, katana, simple journal, travel-pack screen, and versioned saves for the current two-map slice | No functional equipment/inventory management or campaign chapter, mask, and ending state |
| Art and audio | Cohesive palette-driven procedural sprites, tile sets, fog, fireflies, UI, bundled font and licensed sound effects | Not yet a complete high-detail asset set; most environments and characters are still drawn by procedural primitives; music and broader audio are missing |
| Quality | Focused save/resume tests now run automatically | Full campaign regression coverage and a measured five-hour playthrough remain |

## Development roadmap

The main-story target is **approximately five hours**; that estimate will need playtesting and balancing before it can be claimed as achieved. Build outward from the existing game in small, testable milestones:

1. **Campaign persistence and Continue — complete.** Validated, versioned saves cover player progress, map, quest states, and both existing wraiths; Continue, F5 save, and autosave points use the existing menu and loop.
2. **Campaign foundation and prologue.** Add explicit campaign/chapter state and data-driven dialogue choices; write and implement Akihiro's opening, Hana's role, the disgrace and the first mask mystery.
3. **Five regions and mask mechanics.** Expand the world model and transitions for the haunted village, cedar forest, drowned temple, snowbound Kuroyama Pass, and fallen capital; implement the five collectible masks with distinct, testable abilities and story consequences.
4. **RPG systems and encounter framework.** Make inventory and equipment interactive, define meaningful level/stat progression, and build reusable enemy and boss mechanics before authoring all eight major encounters.
5. **Seven chapters, side quests, and endings.** Deliver the full Akihiro/Jin/Lord Masanori/Yurei narrative, optional quests, and the three conditional endings: The Last Guardian, The Forgotten Dawn, and The New Onikage.
6. **Visual and audio production.** Replace placeholder-scale procedural presentation incrementally with original or properly licensed, cohesive region, character, enemy, mask, UI, and effects assets; add music and the remaining audio only with clear licensing.
7. **Regression and playtest pass.** Automate campaign/save/combat/quest/ending tests, verify Python 3.13.17 and Pygame 2.6.1, fix regressions, and measure/balance the main-story playtime.

**Completed:** Existing-game inventory and gap analysis; roadmap; Milestone 1 implementation and save/resume tests (6 passing).
**In progress:** None; Milestone 1 is complete and verified.
**Remaining:** Milestones 2–7. No unimplemented campaign feature is considered complete.

### Provisional campaign structure

The chapter/region assignment and pacing below are design targets, not implemented content. Five mask guardians plus Jin, Lord Masanori, and the final Onikage encounter account for eight major bosses.

| Story segment | Region and major beat | Mask / major encounter | Target |
|---|---|---|---:|
| Prologue | Akihiro returns to the haunted village in disgrace; Hana reveals the shrine's warning and Yurei's connection to the masks | Establish the mystery | 25 min |
| Chapter 1 | Haunted village: investigate the first awakening and the truth behind Akihiro's exile | Wrath guardian — boss 1 | 40 min |
| Chapter 2 | Cedar forest: follow spirit fires; Jin becomes a rival or uneasy ally | Fear guardian — boss 2 | 40 min |
| Chapter 3 | Drowned temple: recover the account of the five masks and the loss that binds Akihiro to Yurei | Grief guardian — boss 3 | 40 min |
| Chapter 4 | Snowbound Kuroyama Pass: face the samurai code that Lord Masanori exploited | Pride guardian — boss 4 | 40 min |
| Chapter 5 | Fallen capital: expose the court's cover-up and the mask's final deception | Deception guardian — boss 5; Jin duel — boss 6 | 40 min |
| Chapter 6 | Return across the regions; confront Masanori and decide how to use the gathered masks | Lord Masanori — boss 7 | 35 min |
| Chapter 7 | Blood-moon climax: face the Onikage and determine Yurei's fate | Final encounter — boss 8; unlock one of three endings | 40 min |

This pacing totals roughly five hours before optional quests; playtests will determine the actual runtime. Side quests should deepen Hana, Jin, and the region stories without blocking the main route.

**Visual pass 1:** The samurai and starting village now use a consistent, cached pixel-art style. Existing gameplay and the main menu remain unchanged.

**Visual pass 2:** Dialogue, quest, inventory, and battle screens now share a framed pixel-art UI; the wraith and battle samurai reuse cached sprites.

**Visual pass 3:** Procedural assets are organized by category under `onikage/art/`; village effects, village props, battle environments, and font setup now have dedicated modules.

**Licensed asset pass:** The game UI now bundles DotGothic16, a Japanese-capable pixel font under the SIL Open Font License. Kenney's CC0 RPG Audio pack supplies footsteps, interface sounds, and battle effects. The pack's generic medieval tiles were reviewed but not used because they conflict with the Japanese village's visual style.

## What works

- The existing main menu is preserved. New Game enters the village; Settings, Exit, and F11 fullscreen remain available.
- The player has four facing directions and three cached frames per direction, with a two-step walk cycle and a pixel-art katana.
- The player can walk in four directions, sprint, and collide with village scenery.
- The game can save and resume the current campaign slice from the title menu. **F5** saves during exploration; returning to the title screen, closing the window, changing maps, and completing a quest or battle autosave.
- Movement, inventory/journal panels, and successful battle actions have sound effects.
- A camera follows the player through a tile-based village with houses, roads, trees, a shrine, mist, and a notice sign.
- Ambient fireflies drift through the village, and the mist overlay is reused instead of allocated every frame.
- Press **E** near the sign to read it. Talk to Hana to hear dialogue and accept or decline her shrine request.
- Complete “A Prayer for the Village” by interacting with the shrine. Press **J** to open the quest journal.
- Press **I** to see the travel pack.
- A wraith encounter can be started by facing the wraith and pressing **E** or **C**.
- Battle commands: **1 Attack**, **2 Defend**, **3 Spirit Slash**, **4 Use Ration**. Arrow keys or **W/S** change the selected command; **Enter** confirms. Press Enter after victory or defeat to return to the village.
- Victory grants experience. Defeat returns the player to the village with some health restored.
- A cedar forest map is reachable through the northern village road, with bidirectional travel and a forest altar encounter area.

## Run the game

In the VS Code terminal, run:

```powershell
& 'C:\Users\olmoj\AppData\Local\Python\pythoncore-3.13-64\python.exe' 'C:\Users\olmoj\OneDrive\Desktop\Onikage\main.py'
```

## Code layout

- `main.py` starts the game.
- `onikage/game.py` runs the main loop, handles input, and draws screens.
- `onikage/game_state.py` manages screen transitions.
- `onikage/save_data.py` validates and atomically persists versioned campaign saves.
- `onikage/main_menu.py` contains the existing main menu; it has not been redesigned.
- `onikage/player.py` defines the player and movement.
- `onikage/village.py` defines the starting village and its interactable objects.
- `onikage/art/characters/player_sprite.py` builds the cached directional samurai frames.
- `onikage/art/enemies/wraith_sprite.py` builds the animated wraith frames.
- `onikage/art/environments/battlefield.py` draws the layered combat backdrop.
- `onikage/art/environments/village.py` draws houses and cedar trees.
- `onikage/art/objects/village.py` draws village props.
- `onikage/art/effects/village_atmosphere.py` draws reusable mist and firefly effects.
- `onikage/art/tiles/village.py` builds the cached village ground tiles.
- `onikage/art/ui/panels.py` contains reusable interface frames, portraits, and item icons.
- `onikage/art/fonts/ui.py` loads the bundled DotGothic16 font for the game interface.
- `onikage/art/audio/sfx.py` loads and plays the bundled sound effects.
- `onikage/assets/fonts/` contains DotGothic16 and its SIL Open Font License.
- `onikage/assets/audio/` contains selected Kenney RPG Audio effects and its CC0 license.
- `onikage/npc.py` defines village characters.
- `onikage/dialogue.py` presents NPC conversations.
- `onikage/quests.py` tracks quest status.
- `onikage/enemy.py` defines the village wraith.
- `onikage/combat.py` resolves turn-based battle commands.
- `onikage/forest.py` defines the first cedar forest map, obstacles, altar, atmosphere, and forest wraith.

## Verification

Verified with Python 3.13.17 and Pygame 2.6.1. `python -m unittest discover -s tests -v` passes six save/resume tests, including malformed data, menu navigation through Continue, forest-state restoration, and a headless resumed-game draw. `python -m compileall -q main.py onikage tests` and `git diff --check` pass. The existing project history also records earlier headless rendering and regression checks for the original gameplay slice.

## Asset sources and licenses

- [DotGothic16](https://fonts.google.com/specimen/DotGothic16) by the DotGothic16 Project Authors, bundled under SIL Open Font License 1.1. The license is in `onikage/assets/fonts/OFL.txt`.
- [RPG Audio](https://kenney.nl/assets/rpg-audio) by Kenney, selected sound effects bundled under CC0. The license is in `onikage/assets/audio/LICENSE.txt`.
- No external sprite sheets were added: the reviewed generic RPG pack did not fit the game's Japanese village art direction.

## Not implemented yet

- Five collectible masks and their abilities/consequences.
- More NPCs, enemies, quests, bosses, and battle skills.
- Persistent leveling/stat progression beyond the current experience reward.
- A fully interactive equipment and inventory system.
- External sprite sheets and final assets for the remaining characters, enemies, UI, audio, and music.
- Background music and additional ambient sound effects.
- Main-story playtime has not been measured.
