[← Project](README.md) · [Interactive balance showcase](https://lacrimaeaware.github.io/gojomons-portfolio/balance/)

# Testing whether a roster adjustment is needed

Creature types change which matchups and combinations are useful. Gojomons gives single-type creatures a 7% stat allowance to keep them competitive with dual-type creatures. This experiment asks whether changing that allowance improves average matchup balance.

## Decision and evidence

| Decision | Fresh-matchup result | Uncertainty |
| --- | --- | --- |
| **Retain current stats** | **49.7%** single-type battle score | **47.2–52.3%** paired-bootstrap 95% interval |

Training selected 1.00×: the existing allowance remains in place. Validation used 1,024 fresh scenarios, each fought on both sides. The result supports group-level parity for this roster and ruleset.

## Select first, validate afterward

```mermaid
flowchart TB
  A[Fixed roster: 41 single-type / 61 dual-type] --> B[256 training scenarios]
  B --> C[Test seven stat multipliers on the same scenarios]
  C --> D[Select score closest to 50%]
  D --> E[1,024 fresh validation scenarios]
  E --> F[Resample whole scenario pairs for uncertainty]
  classDef select fill:#173f4b,color:#fff,stroke:#173f4b
  classDef validate fill:#f0e3c8,color:#29251c,stroke:#8a7445
  class A,B,C,D select
  class E,F validate
```

**Teal: choose the setting. Gold: evaluate it on fresh scenarios.** Each scenario exchanges the two sides, so placement is balanced within the pair.

## What changes, and what stays fixed

| Component | Setting |
| --- | --- |
| Eligible roster | Final-stage, nonlegendary species with one or two types |
| Level and styles | Level 30; one style realization per species, roster seed 741911 |
| Active mechanics | Level-dependent moves, family abilities and subtype effects |
| Equipment and environment | No held items, relics, master bonuses or weather |
| Intervention | Multiply single-type HP, attack, defenses and speed; round to nearest integer |
| Candidate multipliers | 0.80, 0.90, 1.00, 1.10, 1.20, 1.30, 1.40, relative to current stats |
| Battle score | Win = 1; loss = 0; draw or 80-turn timeout = ½ |
| Scenario score | Mean of its two side-swapped battle scores |

One species from each group is sampled uniformly with replacement, together with a battle seed. All settings use the same training scenarios. The setting closest to 50% wins; ascending grid order breaks ties. Since the baseline won selection, the holdout contains one condition.

## Why the pairing matters

The two orientations share a matchup and seed, so they are related observations. The bootstrap resamples **whole scenarios**, keeping each pair together, rather than counting 2,048 battles as independent. It uses 4,000 resamples and a fixed analysis seed.

| Validation measure | Recorded value |
| --- | --- |
| Battles | 2,048 |
| Draws / timeouts | 34 / 0 |
| Mean battle length | 5.30 turns |
| Conservative Hoeffding 95% interval | 45.5–54.0% |

Both intervals describe matchup-and-seed sampling within this fixed roster. The intervention scales stats while the type rules stay fixed.

The stat multiplier includes current and maximum HP, Attack, Defense, Special Attack, Special Defense and Speed. It acts on effective combat stats after the existing 1.07 allowance.

## Analysis code

```sh
python experiments/analyze_balance.py
python -m unittest discover -s tests
```

[Individual outcomes](data/battle-outcomes.json) feed the [analysis script](experiments/analyze_balance.py), which regenerates the [summary](data/balance-summary.json). [Data and footage notes](PROVENANCE.md).
