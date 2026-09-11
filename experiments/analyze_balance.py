"""Recompute the balance study from recorded battle outcomes (Python 3.10+)."""

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def percentile(values, p):
    values = sorted(values)
    index = (len(values) - 1) * p
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (index - lower)


def mean(values):
    return sum(values) / len(values)


def score(victor, single_side):
    return 1.0 if victor == single_side else 0.5 if victor in ("draw", "timeout") else 0.0


def describe(rows, seed=29091):
    """Resample entire scenarios, preserving the two matched orientations."""
    values = [row["score"] for row in rows]
    rng = random.Random(seed)
    samples = [mean(rng.choices(values, k=len(values))) for _ in range(4000)]
    estimate = mean(values)
    radius = math.sqrt(math.log(40) / (2 * len(values)))
    return {
        "scenarios": len(values),
        "battles": 2 * len(values),
        "mean": estimate,
        "bootstrap95": [percentile(samples, 0.025), percentile(samples, 0.975)],
        "hoeffding95": [max(0.0, estimate - radius), min(1.0, estimate + radius)],
        "single_on_player_side": mean([score(r["first"], "p") for r in rows]),
        "single_on_enemy_side": mean([score(r["second"], "e") for r in rows]),
        "timeouts": sum(row["timeouts"] for row in rows),
        "draws": sum(row["draws"] for row in rows),
        "mean_turns": mean([v for row in rows for v in row["turns"]]),
    }


def validate(data):
    rows = data["rows"]
    assert not data["checks"]["failures"], data["checks"]
    assert data["checks"]["deterministic"]
    assert data["checks"]["reverse_order_cases"] == 56
    assert data["checks"]["scale_survives_initialization"]
    assert len({r["id"] for r in data["roster"]}) == len(data["roster"])
    train = [r for r in rows if r["split"] == "train"]
    test = [r for r in rows if r["split"] == "test"]
    assert {r["seed"] for r in train}.isdisjoint({r["seed"] for r in test})
    keys = [(r["split"], r["scale"], r["case"]) for r in rows]
    assert len(set(keys)) == len(keys), "duplicate cases"
    reference = {}
    for row in rows:
        assert row["first"] in ("p", "e", "draw", "timeout")
        assert row["second"] in ("p", "e", "draw", "timeout")
        actual = (score(row["first"], "p") + score(row["second"], "e")) / 2
        assert actual == row["score"]
        assert row["timeouts"] == (row["first"] == "timeout") + (row["second"] == "timeout")
        key = row["split"], row["case"]
        design = row["single"], row["dual"], row["seed"]
        assert reference.setdefault(key, design) == design, "unmatched parameter comparison"
    means = {m: mean([r["score"] for r in train if r["scale"] == m]) for m in data["multipliers"]}
    best = min(data["multipliers"], key=lambda m: abs(means[m] - 0.5))
    assert best == data["selected"], "selection differs from training-only criterion"
    for m in data["multipliers"]:
        assert len([r for r in train if r["scale"] == m]) == data["train_n"]
    for m in set([1.0, data["selected"]]):
        assert len([r for r in test if r["scale"] == m]) == data["test_n"]


def main():
    data = json.loads((ROOT / "data" / "battle-outcomes.json").read_text())
    validate(data)
    curve = []
    for multiplier in data["multipliers"]:
        rows = [r for r in data["rows"] if r["split"] == "train" and r["scale"] == multiplier]
        curve.append({"scale": multiplier, **describe(rows)})
    holdout = []
    for multiplier in sorted(set([1.0, data["selected"]])):
        rows = [r for r in data["rows"] if r["split"] == "test" and r["scale"] == multiplier]
        holdout.append({"scale": multiplier, **describe(rows)})
    selected = next(row for row in holdout if row["scale"] == data["selected"])
    trace_rows = [r for r in data["rows"] if r["split"] == "test" and r["scale"] == data["selected"]]
    trace = []
    for n in [16, 32, 64, 128, 256, 512, 1024]:
        estimate = mean([r["score"] for r in trace_rows[:n]])
        radius = math.sqrt(math.log(40) / (2 * n))
        trace.append({"n": n, "mean": estimate, "hoeffding95": [max(0, estimate - radius), min(1, estimate + radius)]})
    summary = {
        "title": "How much does a stat adjustment change matchup balance?",
        "date": "2026-09-11",
        "roster_seed": data["roster_seed"],
        "existing_single_type_compensation": data["existing_single_type_compensation"],
        "single_count": data["single_count"],
        "dual_count": data["dual_count"],
        "level": data["level"],
        "selected_scale": data["selected"],
        "training": curve,
        "holdout": holdout,
        "holdout_trace": trace,
        "total_battles": 2 * len(data["rows"]),
        "selection_rule": "Minimize |mean single-type battle score - 0.5| on training scenarios; ties take the first ascending grid value.",
        "score_definition": "Win 1, loss 0, draw or turn-limit timeout 0.5; average both side orientations for each scenario.",
        "confidence": "Bootstrap intervals resample whole scenarios, not individual battles. Hoeffding intervals use scores bounded in [0,1]. Both quantify random matchup/seed sampling within this fixed roster, not generalization to player campaigns.",
        "takeaway": f"Training selected a {data['selected']:.2f}× multiplier. The independent holdout score was {selected['mean']:.1%}.",
        "scope": data["scope"],
    }
    output = ROOT / "data" / "balance-summary.json"
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
