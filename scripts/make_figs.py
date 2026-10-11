import json, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

with open("ablation_results.json") as f:
    res = json.load(f)

# Fig 1: threshold sensitivity -- avg error vs mean cycles for rotation stage, 3 modes
# We only have single threshold/depth points per mode (as tuned), so plot ablation trend instead:
# combined config cycles vs error for High/Medium/Low (rotation stage)
modes = ["High","Medium","Low"]
rot_avg = [res[f"combined_{m}"]["rot_avg"] for m in modes]
rot_cyc = [res[f"combined_{m}"]["rot_cyc"] for m in modes]
vec_avg = [res[f"combined_{m}"]["vec_avg"] for m in modes]
vec_cyc = [res[f"combined_{m}"]["vec_cyc"] for m in modes]

fig, axes = plt.subplots(1,2, figsize=(9,3.6))
axes[0].plot(rot_cyc, rot_avg, marker='o')
for x,y,m in zip(rot_cyc, rot_avg, modes):
    axes[0].annotate(m, (x,y), textcoords="offset points", xytext=(5,5), fontsize=8)
axes[0].set_xlabel("Mean cycles (rotation stage)")
axes[0].set_ylabel("Average relative error")
axes[0].set_yscale("log")
axes[0].set_title("Sin/Cos (rotation)")
axes[0].grid(True, alpha=0.3)

axes[1].plot(vec_cyc, vec_avg, marker='s', color='tab:orange')
for x,y,m in zip(vec_cyc, vec_avg, modes):
    axes[1].annotate(m, (x,y), textcoords="offset points", xytext=(5,5), fontsize=8)
axes[1].set_xlabel("Mean cycles (vectoring stage)")
axes[1].set_ylabel("Average relative error")
axes[1].set_yscale("log")
axes[1].set_title("Atan2 (vectoring)")
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("fig_accuracy_latency.png", dpi=200)
print("saved fig_accuracy_latency.png")

# Fig 2: ablation bar chart (mean cycles) baseline/early/dual/combined for High mode
configs = ["baseline","earlyonly","dualonly","combined"]
labels = ["Baseline","Early-stop\nonly","Dual-step\nonly","Combined"]
rot_c = [res[f"{c}_High"]["rot_cyc"] for c in configs]
vec_c = [res[f"{c}_High"]["vec_cyc"] for c in configs]

x = np.arange(len(configs))
w = 0.35
fig2, ax2 = plt.subplots(figsize=(6,4))
ax2.bar(x-w/2, rot_c, w, label="Rotation (sin/cos)")
ax2.bar(x+w/2, vec_c, w, label="Vectoring (atan2)")
ax2.set_xticks(x); ax2.set_xticklabels(labels)
ax2.set_ylabel("Mean cycles (High-precision mode)")
ax2.set_title("Ablation: latency reduction sources")
ax2.legend()
ax2.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig("fig_ablation.png", dpi=200)
print("saved fig_ablation.png")
