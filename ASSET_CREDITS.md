# ONIKAGE Asset Credits

This file records existing assets and pack samples whose files and licensing evidence were inspected. Feudal Japan props are integrated into the starting village. The other three packs remain preview-only.

## Used

| Asset | Creator | Source | License | Attribution / distribution notes |
|---|---|---|---|---|
| DotGothic16 font | The DotGothic16 Project Authors | [Google Fonts specimen](https://fonts.google.com/specimen/DotGothic16); upstream project: [fontworks-fonts/DotGothic16](https://github.com/fontworks-fonts/DotGothic16) | SIL Open Font License 1.1; the license text is bundled at `onikage/assets/fonts/OFL.txt` | Keep the OFL with the font. The font may be bundled with software under OFL conditions; do not sell the font by itself. |
| Selected RPG Audio sound effects | Kenney Vleugels (Kenney.nl) | [Kenney RPG Audio](https://kenney.nl/assets/rpg-audio); archive inspected at `Downloads/kenney_rpg-audio.zip` | CC0 as stated in the archive's `License.txt`, copied to `onikage/assets/audio/LICENSE.txt` | Attribution is not mandatory under the included notice; credit is appreciated. |
| Existing Pygame-drawn art | ONIKAGE project code | `onikage/art/` and related game modules | Project-authored code; no third-party sprite pack identified | Includes the village ground/road/stream tiles, house details, sakura variations, bamboo groves, and bridge added in the village overhaul. These are original code-drawn assets, not imported pack content. |
| Feudal Japan Props Vol.1 | PixelKensei Archive | [Official itch.io listing](https://pixelkensei.itch.io/feudal-japan-props-vol1-free-pixel-art-assets); original archive is in Downloads | Included README states CC0 1.0; copied to `onikage/assets/artpacks/feudal_japan/README_LICENSE.txt` | Eight individual 32x32 props are copied under `onikage/assets/artpacks/feudal_japan/props/`. The village uses the torii, stone lantern, offering box, sake barrel, bamboo, paper lantern, katana stand, and wooden fence. At runtime, border-connected backdrop colors are masked to transparency because the supplied PNG pixels are opaque; originals are preserved unchanged. Attribution is optional/appreciated; raw resale and falsely claiming authorship are prohibited by the README. |

## Preview-only packs — not integrated into gameplay

The original archives remain in Downloads. Curated preview copies are under `onikage/assets/artpacks/`; no original project art was overwritten.

- Japanese Village & Villagers (itch.io): no archive found; exact creator/product page and terms needed.
- Pixel Crawler Free Pack (Exterior 0.1): Anokolisa; [creator page](https://anokolisa.itch.io/) (exact product URL unconfirmed). Preview copies: Body_A idle/walk/slice/hit sheets and dungeon/floor tilesheets. Bundled Terms permit use in functional commercial projects and prohibit raw asset sale or marketing the assets as a final product; not CC0. Terms are copied to `onikage/assets/artpacks/pixel_crawler/Terms.txt`.
- Ninja Adventure Asset Pack: Pixel-Boy and AAA; [official listing](https://pixel-boy.itch.io/ninja-adventure-asset-pack). Preview copies: Samurai spritesheet, idle/walk/attack sheets, dungeon/house tilesheets. Bundled LICENSE/README state CC0; attribution optional. Both notices are copied under `onikage/assets/artpacks/ninja_adventure/`.
- 0x72 16x16 Dungeon Tileset: Robert (0x72); [official listing](https://0x72.itch.io/16x16-dungeon-tileset) states CC0; no license was bundled in the archive. Preview copies: atlas, JSON metadata, selected named tile images. Source/license evidence is documented in `onikage/assets/artpacks/0x72_dungeon/SOURCE_AND_LICENSE.md`.
- Any additional candidate pack: record its creator, canonical source URL, exact license text, attribution requirements, modifications, and files here before integration.

The preview-only packs are not used in game rendering or gameplay. Feudal Japan props do not replace the game UI, character sprites, or environmental tiles.
