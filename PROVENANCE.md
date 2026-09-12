[← Project](README.md)

# Source and media notes

## Recorded material

| Material | Source |
| --- | --- |
| Main-menu animation | Recorded from the current main-menu scene on September 11, 2026, using Godot's movie recorder; seven-second excerpt, resized to 960 × 540 at 12 fps. No menu buttons were clicked. |
| Showcase preview | Screenshot of the public GitHub Pages homepage, September 11, 2026 |
| Combat experiment | September 10, 2026 game snapshot; Godot 4.5.1 stable, official build `f62fdbde1` |
| Battle clip | Staged two-versus-two encounter recorded in Godot at 1280 × 720 and 30 fps; an 11-second excerpt with in-game audio |

The battle clip illustrates combat presentation. The balance dataset contains separate one-versus-one simulations.

## Follow the data

| File | Purpose |
| --- | --- |
| [Battle outcomes](data/battle-outcomes.json) | Individual scenarios, side orientations, outcomes and turn counts |
| [Analysis script](experiments/analyze_balance.py) | Regenerates the selection, totals and uncertainty intervals |
| [Balance summary](data/balance-summary.json) | Reported results |
| [Source manifest](data/source-manifest.json) | Hashes identifying the experiment's combat dependencies and content |

The experiment uses `BattleSimulator` with `apply_effects=true`, calling the shared `CombatResolver` and post-turn manager. The harness requires effect collection to be active. The full game source and asset library remain private.

I develop Gojomons with AI assistance for code and prototype art. The reported balance results come from automated game simulations.
