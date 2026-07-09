"""render the latency comparison chart from the captured benchmark numbers.

the values below are the results measured during the practicum run against
live aws (us-east-1); see docs/cost-performance-analysis.md for context.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "data" / "performance_comparison.png"

categories = ["100 requests", "1000 requests"]
rds_times = [0.1461, 1.3930]
dynamo_times = [0.0335, 0.3451]

x = np.arange(len(categories))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
# aws-brand colors: rds navy, dynamodb orange
rects1 = ax.bar(x - width / 2, rds_times, width, label="aws rds (mysql)", color="#232f3e")
rects2 = ax.bar(x + width / 2, dynamo_times, width, label="aws dynamodb", color="#ff9900")

ax.set_ylabel("latency (seconds)")
ax.set_title("performance comparison: rds vs dynamodb")
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.legend()


def autolabel(rects) -> None:
    for rect in rects:
        height = rect.get_height()
        ax.annotate(
            f"{height:.4f}s",
            xy=(rect.get_x() + rect.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
        )


autolabel(rects1)
autolabel(rects2)
fig.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=300)
print(f"success: chart saved as {OUTPUT_FILE}")
