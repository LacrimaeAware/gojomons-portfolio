[← Project](README.md)

# Source and media notes

## Recorded material

| Material | Source |
| --- | --- |
| Main-menu animation | Main-menu scene, recorded September 11, 2026. |
| Showcase preview | Showcase homepage, September 17, 2026 |
| Combat experiment | September 10, 2026 game snapshot; Godot 4.5.1 |
| Battle clip | Staged two-versus-two encounter in the live battle system |

The battle clip illustrates combat presentation. The balance dataset contains separate one-versus-one simulations.

## Follow the data

| File | Purpose |
| --- | --- |
| [Battle outcomes](data/battle-outcomes.json) | Individual scenarios, side orientations, outcomes and turn counts |
| [Analysis script](experiments/analyze_balance.py) | Calculates the selected setting, group scores and uncertainty intervals |
| [Balance summary](data/balance-summary.json) | Reported results |

The experiment uses `BattleSimulator` with `apply_effects=true`, calling the shared `CombatResolver` and post-turn manager.
