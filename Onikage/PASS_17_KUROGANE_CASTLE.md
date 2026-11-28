# ONIKAGE Pass 17 — Fallen Kurogane Castle

## Implemented
- Added `KuroganeCastleWorld`, a new top-down ruined castle region with a dark stone palette, broken wall/rubble collision, keep silhouette, drifting ash, and a distinct chapter label.
- Added the Fallen Shogun guardian using the existing combat encounter pipeline, with 340 health, 29 attack power, and 260 experience reward.
- Added travel from Whispering Cedar Forest into Kurogane Castle and a return route to the Cedar Forest.
- Added save/continue region restoration and defeated-guardian restoration for Kurogane Castle.
- Added the Pride Mask reward and Realm Between Worlds unlock through campaign progression.
- Added source-level regression tests for the new chapter integration.

## Validation
- Python compileall passed for the project source.
- Pygame runtime and visual tests were not run in this environment because Pygame is unavailable here. Run the project's test suite on the Windows development machine.

## Controls
Use the existing E interaction at the eastern chapter gate to enter after defeating Hollow Stalker. Use the western return gate to return to the Cedar Forest.
