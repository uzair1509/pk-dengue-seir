"""Plot province-level dengue Rt (KP, Sindh, Balochistan) and the
compliance-adjusted vs raw national case series."""
import csv
import datetime as dt
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

PROV_RT_CSV = Path(__file__).parent.parent / "results" / "rt_estimates_province.csv"
COMPLIANCE_CSV = Path(__file__).parent.parent / "results" / "compliance_adjusted.csv"
OUT_PROVINCE_PNG = Path(__file__).parent.parent / "results" / "dengue_rt_province.png"
OUT_COMPLIANCE_PNG = Path(__file__).parent.parent / "results" / "dengue_compliance_adjusted.png"

PROVINCE_COLORS = {"KP": "#1f4e79", "Sindh": "#7a2e2e", "Balochistan": "#4c7a2e"}


def plot_province_rt():
    by_province = defaultdict(lambda: {"date": [], "Rt": [], "lo": [], "hi": []})
    with open(PROV_RT_CSV, newline="") as f:
        for r in csv.DictReader(f):
            p = r["province"]
            by_province[p]["date"].append(dt.date.fromisoformat(r["date"]))
            by_province[p]["Rt"].append(float(r["Rt_mean"]) if r["Rt_mean"] else float("nan"))
            by_province[p]["lo"].append(float(r["Rt_lo95"]) if r["Rt_lo95"] else float("nan"))
            by_province[p]["hi"].append(float(r["Rt_hi95"]) if r["Rt_hi95"] else float("nan"))

    fig, ax = plt.subplots(figsize=(11, 5.5))
    for p in ["KP", "Sindh", "Balochistan"]:
        d = by_province[p]
        ax.plot(d["date"], d["Rt"], color=PROVINCE_COLORS[p], lw=1.3, label=p)
        ax.fill_between(d["date"], d["lo"], d["hi"], color=PROVINCE_COLORS[p], alpha=0.12)
    ax.axhline(1.0, color="black", lw=1, ls="--", label="$R_t = 1$")
    ax.set_ylabel("Effective reproduction number $R_t$")
    ax.set_title("Province-level dengue $R_t$: KP, Sindh, Balochistan, 2023-2026\n"
                  "(shaded = 95% credible interval; provinces with sparse/NR reporting excluded)",
                  fontsize=11)
    ax.set_ylim(0, 5)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    fig.tight_layout()
    fig.savefig(OUT_PROVINCE_PNG, dpi=150)
    print(f"wrote {OUT_PROVINCE_PNG}")


def plot_compliance_adjusted():
    dates, reported, adjusted, compliance = [], [], [], []
    with open(COMPLIANCE_CSV, newline="") as f:
        for r in csv.DictReader(f):
            dates.append(dt.date.fromisoformat(r["date"]))
            reported.append(int(r["reported_cases"]))
            adjusted.append(float(r["adjusted_cases"]) if r["adjusted_cases"] else float("nan"))
            compliance.append(float(r["compliance_pct"]))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True,
                                    gridspec_kw={"height_ratios": [1.4, 1]})
    ax1.plot(dates, reported, color="#7a2e2e", lw=1.1, label="Reported cases")
    ax1.plot(dates, adjusted, color="#1f4e79", lw=1.1, ls="--",
              label="Compliance-adjusted cases")
    ax1.set_ylabel("Weekly dengue cases")
    ax1.set_title("Reported vs. reporting-compliance-adjusted dengue cases, 2023-2026\n"
                   "(adjustment = reported / national compliance rate -- a scale check, not a correction)",
                   fontsize=10.5)
    ax1.legend(loc="upper right", fontsize=9)

    ax2.plot(dates, compliance, color="#555555", lw=1.1)
    ax2.axhline(100, color="black", lw=0.7, ls=":")
    ax2.set_ylabel("National IDSR\ncompliance (%)")
    ax2.set_ylim(0, 105)
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    fig.tight_layout()
    fig.savefig(OUT_COMPLIANCE_PNG, dpi=150)
    print(f"wrote {OUT_COMPLIANCE_PNG}")


if __name__ == "__main__":
    plot_province_rt()
    plot_compliance_adjusted()
