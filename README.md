[![Gojomons: current main menu, recorded in Godot](media/main-menu-preview.webp?v=20260911-current)](https://lacrimaeaware.github.io/gojomons-portfolio/)

Gojomons is a creature-building roguelike autobattler I am developing in Godot. Build a team, choose a route, combine moves with equipment, and find out whether the plan survives the next fight.

## Explore the visual showcase

**[Open the book →](https://lacrimaeaware.github.io/gojomons-portfolio/)** Game footage introduces the world and combat. The Balance and Tools chapters cover mechanic tests, simulation results and reviews in playable scenes.

## Combat rules and testing

Moves, creature abilities, held items and team relics can trigger during the same fight. Live play and automated tests use the same combat rules.

| Development question | Approach |
| --- | --- |
| How can effects interact without firing twice or in the wrong order? | One combat resolver owns the state changes; signals let presentation and diagnostic systems respond. **[Architecture →](ARCHITECTURE.md)** |
| Which choices reward a stronger strategy, and which are broadly overpowered? | Compare simulated outcomes under different decision policies, then inspect species and matchup patterns. **[Balance showcase →](https://lacrimaeaware.github.io/gojomons-portfolio/balance/)** |
| How can I check a change quickly in its actual context? | Launch specific encounters, inspect the scene and attach review notes. **[Development tools →](https://lacrimaeaware.github.io/gojomons-portfolio/tools/)** |

### Single-type stat experiment

Gojomons already gives single-type creatures a **7% stat allowance**. The experiment compared seven stat adjustments on the same training matchups, then checked the selected setting on fresh matchups.

The group average supports keeping the allowance in this test. Species-level matchups and equipment synergies are further questions; the [interactive balance chapter](https://lacrimaeaware.github.io/gojomons-portfolio/balance/) shows the policy and species comparisons.

**[Read the experiment →](METHODS.md)** for the controls, selection procedure and uncertainty. **[Source and media notes →](PROVENANCE.md)** identify the recorded data and footage.

<details>
<summary>Analysis code</summary>

```sh
python experiments/analyze_balance.py
python -m unittest discover -s tests
```

</details>
