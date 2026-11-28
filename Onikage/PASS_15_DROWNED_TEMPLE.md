# ONIKAGE Pass 15 — Drowned Temple

## Implemented
- New `DrownedTempleWorld` chapter environment.
- Cool flooded-stone palette, blocked water channels, animated water lines, and low drifting mist.
- Weeping Bride guardian uses the established realtime combat pipeline with a chapter-specific health, damage, and XP profile.
- Ashen Oni victory unlocks the temple through campaign progression; entering the temple requires that unlock.
- Weeping Bride victory records `weeping_bride`, awards the Grief Mask (Spirit Veil), and unlocks the Cedar Forest in campaign data.
- Return gate leads to the Burning Village.
- Continue/save reconstructs the correct chapter and keeps a defeated Weeping Bride defeated.

## Controls
Use the existing movement and interaction controls. Approach the eastern flooded pass in the Burning Village and press E to enter after defeating the Ashen Oni.

## Validation
`python -m py_compile onikage/*.py main.py` passed in the build environment. Pygame is not installed in that environment, so in-game rendering, collision behavior, and the full test suite require validation on the Windows machine with Python 3.13 and Pygame 2.6.1.

## Not complete yet
Cedar Forest, Fallen Kurogane Castle, Realm Between Worlds, final guardian and ending scenes remain outstanding. Do not describe the five-mask campaign as finished yet.
