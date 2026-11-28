# Pass 32 — Enemy Variety & Kagehama Side Quests

## Enemy visual identity
- Added dedicated pixel-art guardian sprites for Ashen Oni, Weeping Bride, Hollow Stalker, Fallen Shogun, and Nameless One.
- Enemy rendering now selects a guardian-specific sprite by its canonical name; ordinary Cedar-Wood Wraiths retain the existing directional animation atlas.
- Guardian sprite images are cached after loading. Hit reaction and death presentation remain supported.

## New playable Kagehama side quests
- **The Names on the Stone** — accept the request from Hana after completing the shrine prayer, then visit the marked memorial tablet in the eastern garden.
- **The Merchant's Lost Ledger** — after completing the memorial request, speak with Hana again and search the marked southern market cart.
- Quest destinations have subtle gold markers, completion is recorded in the existing active/completed quest save fields, and the journal now focuses its detail panel on the active quest.
- The original main quest and campaign chronicle are preserved.

## Validation
- Python compileall passed.
- Campaign chronicle tests: 5 passed.
- All five guardian PNGs verified as 64x80 RGBA assets.
- Pygame runtime/rendering was not available in this build environment; test in the user's Python 3.13 + Pygame 2.6.1 environment.
