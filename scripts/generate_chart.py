"""render the serial latency chart from the captured benchmark numbers.

these are average per-request read latency for the same "one year, one major"
lookup, measured against live aws (us-east-1) at two sample sizes. the average
is stable across sample size, as an average should be; the gap between the two
backends is the story. see docs/cost-performance-analysis.md for context.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "data" / "performance_comparison.png"

# average per-request latency (seconds), measured live at n=100 and n=1000
categories = ["100 requests", "1000 requests"]
rds_times = [0.1438, 0.1454]
dynamo_times = [0.0345, 0.0318]

# rds = blue, dynamodb = orange; the same entity keeps the same color across
# every chart in this repo. palette validated colorblind-safe (see readme).
RDS_COLOR = "#2a78d6"
DYNAMO_COLOR = "#eb6834"
INK = "#2b2a28"
MUTED = "#6b6a66"

x = np.arange(len(categories))
width = 0.36

fig, ax = plt.subplots(figsize=(9, 5.5))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

rects1 = ax.bar(x - width / 2, rds_times, width, label="Amazon RDS (MySQL)", color=RDS_COLOR)
rects2 = ax.bar(x + width / 2, dynamo_times, width, label="Amazon DynamoDB", color=DYNAMO_COLOR)

ax.set_ylabel("average latency per request (seconds)", color=INK)
ax.set_title("Serial read latency: RDS vs DynamoDB", color=INK, fontsize=13, pad=14)
ax.set_xticks(x)
ax.set_xticklabels(categories, color=INK)

# recessive axes: drop the box, keep a faint value grid
for spine in ("top", "right", "left"):
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color(MUTED)
ax.tick_params(length=0, colors=MUTED)
ax.yaxis.grid(True, color="#e6e5e1", linewidth=0.8)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper right")


def label(rects) -> None:
    for rect in rects:
        height = rect.get_height()
        ax.annotate(
            f"{height:.4f}s",
            xy=(rect.get_x() + rect.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color=INK,
            fontsize=9,
        )


label(rects1)
label(rects2)
fig.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=200)
print(f"success: chart saved as {OUTPUT_FILE}")
