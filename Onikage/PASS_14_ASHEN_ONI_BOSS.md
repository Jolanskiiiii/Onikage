# Pass 14 — Ashen Oni Boss Encounter

## Gameplay changes

- The Ashen Oni now has a guardian-specific attack instead of using the ordinary Wraith Claw.
- Its first phase uses **Cinder Cleave**, with a wider reach and heavier knockback than the village Wraith.
- At 50% health, the boss enters an enraged second phase. The transition is announced in the combat message.
- The enraged phase uses **Infernal Sweep**: faster startup, a wider hit area, greater damage, stronger knockback, and a shorter cooldown.
- The guardian's engagement distance is larger than a normal enemy's so the encounter can begin at a fair distance.
- Ordinary Wraith combat remains unchanged.

## Validation

- Python `compileall` passes for the full project.
- Added unit tests for the Ashen Oni's first-phase attack and the half-health phase transition.
- Pygame runtime tests were not run in this environment because Pygame is not installed here.

## Still outstanding

This pass improves the first guardian encounter only. It does not claim the remaining campaign regions are complete.
