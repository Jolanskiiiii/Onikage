# ONIKAGE Pass 18 — Realm Between Worlds

## Implemented
- Added `onikage/realm_between_worlds.py`, a top-down final-region world with a distinct void palette, rift motes, black-stone fragments, navigable central route, and return gate.
- Added the Nameless One as the final guardian (420 HP, 34 attack power, 400 XP reward).
- Added castle-to-realm travel after the Fallen Shogun unlocks the final region, and return travel to Kurogane Castle.
- Added continue-game restoration for the final region and defeated Nameless One.
- Added the Deception Mask reward for the Nameless One.
- Added three ending selections after the final guardian is defeated: press H for Humanity, C for Curse, or X for Exile. The selected ending is persisted in campaign save data.
- Added four campaign/chapter regression tests.

## Validation
- `python -m compileall -q main.py onikage tests` passed.
- `python -m unittest tests.test_realm_between_worlds_chapter -v` passed (4 tests).
- Full suite attempted; 11 test modules could not import because Pygame is not installed in this build environment. No claim of full runtime validation is made.

## Important
Run the game on the Windows development machine with Pygame installed and test the final-region entrance, boss encounter, save/continue, and ending selection.
