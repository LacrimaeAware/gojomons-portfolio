# Testing a proposed stat adjustment

The question is whether scaling single-type creatures' combat stats brings their average score against dual-type creatures closer to 50%. The intervention changes stats; it does not isolate the causal effect of having a second type.

## Matchups

The pool contains every species in the snapshot with one or two types, no legendary tag, and no further evolution condition: 41 single-type and 61 dual-type species. Each is constructed at level 30 with the game's level-dependent moves. Species can roll different combat styles; roster seed 741911 fixes one style realization per species, and the exported roster records it. Family abilities and subtype effects remain active. There are no held items, relics, master bonuses, or weather effects.

For each scenario, sample one member of each group uniformly with replacement and a battle seed. Fight twice, exchanging the sides. A scenario's score is the mean of the single-type creature's two results: win 1, loss 0, draw or 80-turn timeout 0.5. The source data records both outcomes and turn counts, so timeouts cannot disappear into a win-rate denominator.

The multiplier applies to HP, maximum HP, attack, defense, special attack, special defense, and speed, rounding each to the nearest integer. Types, moves, opponents, styles, and equipment stay fixed. These are effective combat-stat changes, not additions to the species' base-stat total. The existing constructor already applies a 1.07 multiplier to this single-type cohort. An experimental value of 1.00 preserves that allowance; it does not remove it.

## Selection and validation

The prespecified grid is 0.80, 0.90, 1.00, 1.10, 1.20, 1.30, and 1.40. Each value uses the same 256 training scenarios. Choose the multiplier whose mean score is closest to 0.5; ascending grid order breaks ties. Then evaluate that choice and the baseline on 1,024 new scenarios. Training selected the baseline, so the holdout contains a single condition.

Matching seeds couples the comparisons, but a changed action can consume a different sequence of random draws. The two trajectories need not experience identical hit/miss events. Exchanging sides controls average placement in this experiment; it does not assume that placement has no effect.

Training includes 3,584 battles and the holdout 2,048, for **5,632 recorded battles**. A separate 32-battle repeated-seed check passed. The first eight training scenarios under each of seven multipliers were also replayed in reverse parameter order, both after the complete experiment and in a fresh engine process: all outcomes and turn counts matched. Checks at 0.80 and 1.40 confirmed that scaling survives combat initialization. The harness checks for input mutation and refuses to run if the combat-effects pipeline is unavailable. An additional existing multi-target regression check passed on 600 seeds, including 98 primary misses. These checks cover specific behavior, not every possible difference between simulation and live play.

## Uncertainty and interpretation

The displayed bootstrap interval resamples whole scenarios 4,000 times with a fixed analysis seed. The two side orientations stay together. This avoids treating matched outcomes as independent. It is an approximate, pointwise 95% interval.

The summary also includes a conservative Hoeffding interval, using the scenario score's range [0,1]. For the holdout, it is **45.5–54.0%**. These intervals concern random matchup and battle-seed sampling within this fixed roster and ruleset. They do not measure uncertainty about other style realizations, campaign balance, future content, or human play. Intervals at successive sample counts in the convergence display are pointwise, not a simultaneous confidence sequence or stopping rule.

The independent holdout score is **49.7%**, with 34 draws and zero timeouts across 2,048 battles. Average battle length is **5.30 turns**. The sampled group average is close to parity under these conditions. Individual matchups can still be strongly unequal; group parity is only one design target.
