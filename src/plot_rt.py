"""Plot weekly dengue case counts and estimated Rt over the gap-free window."""
import csv
import datetime as dt
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

RT_CSV = Path(__file__).parent.parent / "results" / "rt_estimates.csv"
OUT_PNG = Path(__file__).parent.parent / "results" / "dengue_rt.png"


def main():
    dates, cases, rt_mean, rt_lo, rt_hi = [], [], [], [], []
    with open(RT_CSV, newline="") as f:
        for r in csv.DictReader(f):
            dates.append(dt.date.fromisoformat(r["date"]))
            cases.append(int(r["dengue_cases"]))
            rt_mean.append(float(r["Rt_mean"]) if r["Rt_mean"] else float("nan"))
            rt_lo.append(float(r["Rt_lo95"]) if r["Rt_lo95"] else float("nan"))
            rt_hi.append(float(r["Rt_hi95"]) if r["Rt_hi95"] else float("nan"))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True,
                                    gridspec_kw={"height_ratios": [1, 1.2]})

    ax1.bar(dates, cases, width=6, color="#7a2e2e", alpha=0.85)
    ax1.set_ylabel("Weekly dengue cases\n(Pakistan, national)")
    ax1.set_title("Pakistan weekly dengue case counts and estimated $R_t$, 2023–2026\n"
                   "(source: NIH IDSR weekly bulletins)", fontsize=11)

    ax2.plot(dates, rt_mean, color="#1f4e79", lw=1.3, label="$R_t$ (posterior mean)")
    ax2.fill_between(dates, rt_lo, rt_hi, color="#1f4e79", alpha=0.2, label="95% credible interval")
    ax2.axhline(1.0, color="black", lw=1, ls="--", label="$R_t = 1$")
    ax2.set_ylabel("Effective reproduction\nnumber $R_t$")
    ax2.set_ylim(0, min(4, max(rt_hi[i] for i in range(len(rt_hi)) if rt_hi[i] == rt_hi[i]) * 1.05))
    ax2.legend(loc="upper right", fontsize=8, framealpha=0.9)

    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150)
    print(f"wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
