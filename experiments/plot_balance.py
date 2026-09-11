"""Draw the recorded training curve and independent holdout result."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "data" / "balance-summary.json").read_text())
rows = data["training"]
selected = next(r for r in data["holdout"] if r["scale"] == data["selected_scale"])
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "svg.fonttype": "none"})
fig, ax = plt.subplots(figsize=(10, 5.4), constrained_layout=True)
fig.patch.set_facecolor("#fafaf7")
ax.set_facecolor("#fafaf7")
x = [r["scale"] for r in rows]
y = [r["mean"] for r in rows]
lo = [r["bootstrap95"][0] for r in rows]
hi = [r["bootstrap95"][1] for r in rows]
ax.fill_between(x, lo, hi, color="#667acd", alpha=0.16)
ax.plot(x, y, color="#4d60b4", marker="o", markersize=5, lw=2.2, label="Training scenarios")
ax.axhline(0.5, color="#738176", linestyle=(0, (4, 4)), lw=1)
ax.errorbar([selected["scale"]], [selected["mean"]], yerr=[[selected["mean"]-selected["bootstrap95"][0]], [selected["bootstrap95"][1]-selected["mean"]]], fmt="D", color="#207b64", capsize=5, markersize=7, label="Independent holdout")
ax.annotate(f"Holdout: {selected['mean']:.1%}", (selected["scale"], selected["mean"]), xytext=(1.17, 0.32), arrowprops={"arrowstyle": "-", "color": "#207b64"}, color="#145b49", fontsize=12)
ax.set(xlabel="Single-type stat multiplier, relative to current game", ylabel="Single-type battle score", ylim=(0, 1), xticks=x)
ax.yaxis.set_major_formatter(PercentFormatter(1))
ax.set_title("A measurable response to a stat adjustment", loc="left", fontsize=19, fontweight="bold", pad=22)
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left", "bottom"]].set_color("#b5bbb5")
ax.grid(axis="y", alpha=0.16)
ax.legend(loc="upper left", frameon=False)
fig.text(0.5, -0.035, "Bands: pointwise 95% scenario-bootstrap intervals. Level 30; 1v1; 41 single-type and 61 dual-type species.", ha="center", fontsize=9, color="#535e58")
fig.savefig(ROOT / "media" / "balance-curve.svg", bbox_inches="tight")
fig.savefig(ROOT / "media" / "balance-curve.png", dpi=160, bbox_inches="tight")
