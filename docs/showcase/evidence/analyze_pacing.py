"""Recompute the three July pacing experiments from their archived CSVs.

Python 3.10+, standard library only. This reads existing battle records; it never
starts Godot, modifies the source repository, or runs new battles.

Example:
  python analyze_pacing.py --data-root ./data --output ./derived
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path


# Original project-relative provenance paths are retained in the output JSON.
ORIGINAL_ARCHIVE = Path("DOCUMENTATION/design_bible/data")
MATCH_FIELDS = ("seed", "format", "team", "level", "party", "enemy", "relics")
OFFENSIVE_STYLES = {"sweeper", "berserk", "disruptor"}


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Empty data: {path}")
    for row in rows:
        for key in ("i", "seed", "team", "level", "turns", "p_alive", "e_alive"):
            row[key] = int(row[key])
        if row["timed_out"] not in {"true", "false"}:
            raise ValueError(f"Invalid timeout flag: {path}")
        row["timed_out"] = row["timed_out"] == "true"
        if row["victor"] not in {"p", "e", "draw", "timeout"}:
            raise ValueError(f"Unexpected outcome: {path}: {row['victor']}")
        if not 1 <= row["turns"] <= 120:
            raise ValueError(f"Turn count outside study cap: {path}")
        if row["timed_out"] != (row["victor"] == "timeout"):
            raise ValueError(f"Timeout/outcome disagreement: {path}")
        if row["timed_out"] and row["turns"] != 120:
            raise ValueError(f"Premature timeout: {path}")
        if any(len(row[side].split("|")) != row["team"] for side in ("party", "enemy")):
            raise ValueError(f"Roster length differs from team size: {path}")
    if len({r["i"] for r in rows}) != len(rows):
        raise ValueError(f"Duplicate case index: {path}")
    if len({r["seed"] for r in rows}) != len(rows):
        raise ValueError(f"Duplicate battle seed: {path}")
    return sorted(rows, key=lambda r: r["i"])


def quantile(values: list[int], p: float) -> float:
    """Linear interpolation between order statistics (median agrees with Python)."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def describe(rows: list[dict]) -> dict:
    turns = [r["turns"] for r in rows]
    n = len(rows)
    return {
        "battles": n,
        "mean_turns": statistics.mean(turns),
        "median_turns": statistics.median(turns),
        "p90_turns": quantile(turns, 0.9),
        "p99_turns": quantile(turns, 0.99),
        "capped_battles": sum(r["timed_out"] for r in rows),
        "over_60_turns": sum(t > 60 for t in turns),
        "player_wins": sum(r["victor"] == "p" for r in rows),
        "enemy_wins": sum(r["victor"] == "e" for r in rows),
        "draws": sum(r["victor"] == "draw" for r in rows),
    }


def pair(base: list[dict], variant: list[dict]) -> dict:
    """Pair the retained scenario identity; do not imply full input hashes exist."""
    reference = {r["i"]: r for r in base}
    if set(reference) != {r["i"] for r in variant}:
        raise ValueError("Different case sets")
    for row in variant:
        for field in MATCH_FIELDS:
            if row[field] != reference[row["i"]][field]:
                raise ValueError(f"Scenario mismatch at case {row['i']}, field {field}")
    deltas = [r["turns"] - reference[r["i"]]["turns"] for r in variant]
    changes = Counter(
        f"{reference[r['i']]['victor']}->{r['victor']}"
        for r in variant
        if reference[r["i"]]["victor"] != r["victor"]
    )
    return {
        "matched_cases": len(variant),
        "mismatched_recorded_fields": 0,
        "mean_turn_change": statistics.mean(deltas),
        "median_turn_change": statistics.median(deltas),
        "shorter": sum(d < 0 for d in deltas),
        "same_length": sum(d == 0 for d in deltas),
        "longer": sum(d > 0 for d in deltas),
        "outcome_changes": dict(sorted(changes.items())),
        "decisive_winner_reversals": sum(changes[k] for k in ("p->e", "e->p")),
        "all_outcome_changes": sum(changes.values()),
    }


def offensive_profile(rows: list[dict], style_of: dict[str, str]) -> dict:
    """Descriptive outcome of the side with more offensive-style members.

    Equal counts are excluded. Draws/timeouts score one half, correcting the old
    analysis's boolean expression that treated any non-player result as enemy win.
    This groups different creatures: it does not isolate a causal style effect.
    """
    score = 0.0
    n = 0
    tied_outcomes = 0
    for row in rows:
        counts = [sum(style_of[x] in OFFENSIVE_STYLES for x in row[s].split("|"))
                  for s in ("party", "enemy")]
        if counts[0] == counts[1]:
            continue
        n += 1
        if row["victor"] not in {"p", "e"}:
            score += 0.5
            tied_outcomes += 1
        else:
            score += (row["victor"] == "p") == (counts[0] > counts[1])
    return {"battles_with_unequal_style_counts": n,
            "score": score / n if n else None, "draws_or_timeouts": tied_outcomes}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path(__file__).parent / "data")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    data_root = args.data_root.resolve()
    output = args.output.resolve()
    if output == data_root or data_root in output.parents:
        raise ValueError("Write derived outputs outside the input data directory")
    output.mkdir(parents=True, exist_ok=True)
    style_path = data_root / "damage_feel_2026-07-27/bst_spread.json"
    style_of = {r["id"]: r["style"] for r in json.loads(style_path.read_text())}
    specs = []
    for team in (1, 3, 6):
        for code, mult in (("10", 1.0), ("125", 1.25), ("15", 1.5), ("20", 2.0)):
            specs.append(("damage", f"dm{code}_t{team}", "damage_feel_2026-07-27",
                          f"dm10_t{team}", {"damage_multiplier": mult, "shield_decay": 0.0,
                          "fatigue_enabled": True}))
    for name, mult, fatigue in (("fx_base", 1.0, True), ("fx_nofat", 1.0, False),
                               ("fx_dmg", 1.5, True), ("fx_dmg_nofat", 1.5, False)):
        specs.append(("damage_fatigue", name, "damage_fatigue_interaction_2026-07-27",
                      "fx_base", {"damage_multiplier": mult, "fatigue_enabled": fatigue,
                                  "shield_decay": 0.0}))
    for team in (3, 6):
        for code, decay in (("00", 0.0), ("025", 0.25), ("033", 0.33), ("05", 0.5)):
            specs.append(("shield", f"sd{code}_t{team}", "shield_decay_2026-07-27",
                          f"sd00_t{team}", {"damage_multiplier": 1.0,
                          "fatigue_enabled": True, "shield_decay": decay}))
    cells = []
    all_summaries = []
    for study, name, folder, baseline, conditions in specs:
        relative = ORIGINAL_ARCHIVE / folder / f"battle_pace_{name}.csv"
        path = data_root / folder / f"battle_pace_{name}.csv"
        rows = load_rows(path)
        base = load_rows(data_root / folder / f"battle_pace_{baseline}.csv")
        summary = describe(rows)
        paired = pair(base, rows)
        cell = {
            "study": study, "cell": name, "baseline": baseline,
            "format": rows[0]["format"], "team_size": rows[0]["team"], "level": 30,
            "conditions": conditions, "summary": summary, "paired_to_baseline": paired,
            "source": relative.as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "turn_histogram": {str(k): v for k, v in sorted(Counter(r["turns"] for r in rows).items())},
        }
        if study == "damage":
            cell["offensive_profile"] = offensive_profile(rows, style_of)
        cells.append(cell)
        all_summaries.append({"study": study, "cell": name, "team_size": rows[0]["team"],
                              **conditions, **summary,
                              "paired_mean_turn_change": paired["mean_turn_change"],
                              "decisive_winner_reversals": paired["decisive_winner_reversals"],
                              "all_outcome_changes": paired["all_outcome_changes"]})
    # The three experiment archives intentionally reuse controls. Do not sum
    # their row counts and imply that every row is an independent new battle.
    lookup = {c["cell"]: c for c in cells}
    for left, right in (("dm10_t6", "fx_base"), ("dm15_t6", "fx_dmg"),
                        ("dm10_t6", "sd00_t6"), ("dm10_t3", "sd00_t3")):
        if lookup[left]["sha256"] != lookup[right]["sha256"]:
            raise ValueError(f"Expected reused baseline differs: {left}, {right}")
    result = {
        "schema_version": 1, "measurement_date": "2026-07-27", "analysis_date": "2026-09-11",
        "description": "Recorded July experiments, recomputed without running new battles.",
        "units": {"turns": "simulation rounds, truncated at 120", "scores": "fractions"},
        "quantiles": "Linear interpolation at (n-1)*p; medians match statistics.median.",
        "pairing": {
            "recorded_fields_checked": list(MATCH_FIELDS),
            "producer_review": "Authored style overwrites constructor roll; deterministic stats/moves; separate seeded roster/loadout streams; seeded battle RNG.",
            "not_recorded": ["full per-battle stats", "moves", "held items", "styles", "runtime state hash"],
            "interpretation": "Recorded scenario pairing is verified; full input matching additionally relies on the archived producer. This is not a replay of the historical engine.",
            "source_revisions_reviewed": ["72e1ca250", "31278e99c", "3d444759b"],
        },
        "sampling": "Uniform authored-roster draws, level30, same seeds within each format; player receives two common relics and both sides held items. No human play data.",
        "style_group": sorted(OFFENSIVE_STYLES),
        "style_source_sha256": hashlib.sha256(style_path.read_bytes()).hexdigest(),
        "reused_controls": [["dm10_t6", "fx_base", "sd00_t6"], ["dm15_t6", "fx_dmg"], ["dm10_t3", "sd00_t3"]],
        "cells": cells,
    }
    (output / "pacing-results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with (output / "pacing-summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_summaries[0]))
        writer.writeheader()
        writer.writerows(all_summaries)
    print(f"Validated {len(cells)} cells; wrote pacing-results.json and pacing-summary.csv.")


if __name__ == "__main__":
    main()
