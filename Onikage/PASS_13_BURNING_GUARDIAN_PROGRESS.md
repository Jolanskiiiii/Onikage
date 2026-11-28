# Pass 13 — Burning Village Guardian Progression

## Implemented

- A Burning Village victory against the Ashen Oni is now handled as a regional guardian victory, not as the ordinary village Wraith milestone.
- The victory records `ashen_oni` in campaign progress and awards the Mask of Wrath through the existing guardian-gated mask API.
- The campaign progression model unlocks the Drowned Temple entry in the campaign record after Ashen Oni is defeated.
- Loading a save while in the Burning Village now checks the saved guardian record and keeps the Ashen Oni defeated, removing its collision obstacle.
- Ordinary Wraith victories retain their existing Odachi and village milestone rewards.

## Validation

- All project Python files passed `compileall` syntax compilation.
- Runtime/unit tests could not be executed in this environment because Pygame 2.6.1 is unavailable and package installation cannot reach the package index.
- This pass does not implement the Drowned Temple map or the remaining three guardian chapters. Those remain outstanding work; the campaign record's unlock is not a claim that those areas are playable.
