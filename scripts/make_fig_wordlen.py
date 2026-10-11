import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

data = {
14:{12:7.032e-04},
16:{12:5.236e-04,15:1.421e-04},
18:{12:4.892e-04,15:7.343e-05,18:3.956e-05},
20:{12:4.838e-04,15:6.231e-05,18:1.320e-05,20:9.537e-06},
22:{12:4.834e-04,15:6.040e-05,18:8.112e-06,20:3.577e-06},
24:{12:4.837e-04,15:6.028e-05,18:7.542e-06,20:2.206e-06},
}
fig, ax = plt.subplots(figsize=(5,3.8))
for itmax, marker in zip([12,15,18,20], ['o','s','^','d']):
    fracs = sorted([f for f in data if itmax in data[f]])
    vals = [data[f][itmax] for f in fracs]
    ax.plot(fracs, vals, marker=marker, label=f"depth={itmax}")
ax.set_yscale('log')
ax.set_xlabel("Fractional bits (FRAC)")
ax.set_ylabel("Max relative error")
ax.set_title("Word-length sensitivity (rotation stage)")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("fig_wordlen.png", dpi=200)
print("saved")
