# ONIKAGE Pass 19 — Final Integration QA

## Scope
This pass adds a Pygame-independent regression suite for the campaign model. It verifies the five guardian progression chain, region unlock order, all three ending choices, ending eligibility, and idempotent guardian victory recording.

## Run the checks
From the project root:

```powershell
py -3.13 -m unittest discover -s tests -p "test_campaign_standalone.py" -v
py -3.13 -m compileall -q main.py onikage tests
py -3.13 -m unittest discover -s tests -v
```

The first two commands do not require Pygame for campaign logic and syntax compilation. The full suite and actual game still require the project's Pygame dependency installed locally.

## Important limitation
This QA pass does not claim that all chapters have been playtested end-to-end. The actual Pygame renderer, collisions, boss combat, transitions, and save/load must still be verified on the Windows development machine with Pygame 2.6.1 installed.
