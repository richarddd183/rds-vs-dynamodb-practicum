"""render the concurrency chart from data/concurrency_results.json.

two panels, each with a single axis (throughput and tail latency live on
different scales, so they never share one). the numbers are read from the json
the load test writes, so this chart can never drift from the measured result.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "data" / "concurrency_results.json"
OUTPUT_FILE = ROOT / "data" / "concurrency_comparison.png"

RDS_COLOR = "#2a78d6"
DYNAMO_COLOR = "#eb6834"
INK = "#2b2a28"
MUTED = "#6b6a66"

results = {row["backend"]: row for row in json.loads(RESULTS.read_text())}
rds, dyn = results["rds"], results["dynamodb"]
workers = dyn["workers"]
requests = dyn["requests"]

labels = ["DynamoDB", "RDS"]
colors = [DYNAMO_COLOR, RDS_COLOR]

fig, (ax_tput, ax_lat) = plt.subplots(1, 2, figsize=(11, 5.2))
fig.patch.set_facecolor("white")
fig.suptitle(
    f"Under load: {requests} requests across {workers} concurrent clients",
    color=INK,
    fontsize=13,
)


def style(ax, ylabel) -> None:
    ax.set_facecolor("white")
    ax.set_ylabel(ylabel, color=INK)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(length=0, colors=MUTED)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, color=INK)
    ax.yaxis.grid(True, color="#e6e5e1", linewidth=0.8)
    ax.set_axisbelow(True)


def annotate(ax, values, fmt) -> None:
    for i, v in enumerate(values):
        ax.annotate(
            fmt(v),
            xy=(i, v),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color=INK,
            fontsize=10,
        )


# panel 1: throughput, higher is better
tput = [dyn["throughput_rps"], rds["throughput_rps"]]
ax_tput.bar(range(len(labels)), tput, width=0.55, color=colors)
style(ax_tput, "throughput (requests / second)")
ax_tput.set_title("Throughput  (higher is better)", color=INK, fontsize=11, pad=8)
annotate(ax_tput, tput, lambda v: f"{v:,.0f}")

# panel 2: p95 tail latency, lower is better
p95 = [dyn["p95_s"], rds["p95_s"]]
ax_lat.bar(range(len(labels)), p95, width=0.55, color=colors)
style(ax_lat, "p95 latency (seconds)")
ax_lat.set_title("p95 tail latency  (lower is better)", color=INK, fontsize=11, pad=8)
annotate(ax_lat, p95, lambda v: f"{v:.3f}s")

fig.tight_layout(rect=(0, 0, 1, 0.94))
plt.savefig(OUTPUT_FILE, dpi=200)
print(f"success: chart saved as {OUTPUT_FILE}")
