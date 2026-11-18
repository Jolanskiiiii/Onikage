# ONIKAGE: The Curse of the Five Masks

A 2D pixel-art samurai adventure built with Python 3.13 and Pygame 2.6.

## Run

From this folder, install Pygame and start the game with Python 3.13:

```powershell
py -3.13 -m pip install pygame==2.6.1
py -3.13 main.py
```

If `python` reports that it was not found or opens the Microsoft Store, use the
`py -3.13` commands above instead. They select the Python 3.13 installation
without relying on the `python` command alias.

## Controls

- **WASD** or **Arrow keys**: Move
- **Shift**: Sprint
- **E**: Interact
- **C**: Start a nearby battle
- **I**: Inventory
- **J**: Quest journal
- **F5**: Save during exploration
- **F11**: Toggle fullscreen
- **1–4**: Choose a battle command
- **W/S** or **Arrow keys**: Select a battle command
- **Enter**: Confirm a battle command or continue after battle

See [PROGRESS_REPORT.md](PROGRESS_REPORT.md) for gameplay details and project status.
New Game creates a save; Continue resumes it. Returning to the title screen also saves.
The save is stored in the user's application-data folder (`%APPDATA%\ONIKAGE\save.json` on Windows).

## Asset licenses

The bundled DotGothic16 font is licensed under the SIL Open Font License; see
[`onikage/assets/fonts/OFL.txt`](onikage/assets/fonts/OFL.txt).
The selected Kenney RPG Audio effects are CC0; see
[`onikage/assets/audio/LICENSE.txt`](onikage/assets/audio/LICENSE.txt).
Feudal Japan Props Vol.1 is used for village decorations; its bundled CC0
notice is [`onikage/assets/artpacks/feudal_japan/README_LICENSE.txt`](onikage/assets/artpacks/feudal_japan/README_LICENSE.txt).

## Asset pack previews

The standalone preview shows samples from all four downloaded packs. Feudal
Japan props are also now used in the live starting village; the other three
packs remain preview-only:

The playable village has also received original dark ground textures,
connected winding dirt roads, differentiated house details, sakura and bamboo
decorations, and a wooden bridge over a collision-aligned stream. This does
not replace the game's renderer or gameplay systems.

```powershell
py -3.13 tools\asset_preview.py
```

Use **1–4** to switch between packs, **A/D** to cycle available animation
samples, **Space** to pause, and **Esc** to exit. The source and license notes
are in [`ASSET_CREDITS.md`](ASSET_CREDITS.md); compatibility details are in
[`ASSET_INVENTORY.md`](ASSET_INVENTORY.md). The player, gameplay systems, maps,
and UI are otherwise unchanged by this prop pilot.
