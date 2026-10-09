"""Province-level Rt estimation, extending estimate_rt.py's national analysis.

Uses the same Cori et al. (2013) renewal-equation method and the same
serial-interval assumption (Gamma, mean 15d / SD 7d) as the national
estimate, applied separately to each province's weekly dengue case series.

Province data source: NIH IDSR bulletins' "Table 1: Province/Area-wise
distribution", extracted per-bulletin (171 bulletins, 2023 wk22-2026 wk36)
alongside each bulletin's stated province reporting-compliance percentage.

Why only some provinces get an Rt estimate: the renewal-equation method
needs a reasonably continuous, non-trivial case series -- a province that
is mostly zero or mostly "No Report" (NR) produces a numerically unstable,
meaningless Rt (dividing by a near-zero total-infectiousness denominator).
Provinces are only estimated if they clear both a low-NR-rate bar and a
minimum average weekly case count; see MIN_NONNR_SHARE / MIN_MEAN_CASES
below and the printed eligibility table.
"""
import csv
from pathlib import Path

import numpy as np
from scipy.stats import gamma as gamma_dist

DATA = Path(__file__).parent.parent / "data" / "province_dengue_panel.csv"
OUT_CSV = Path(__file__).parent.parent / "results" / "rt_estimates_province.csv"

PROVINCES = ["AJK", "Balochistan", "GB", "ICT", "KP", "Punjab", "Sindh"]
SI_MEAN_DAYS = 15.0
SI_SD_DAYS = 7.0
WINDOW_WEEKS = 4
PRIOR_SHAPE = 1.0
PRIOR_RATE = 0.2

MIN_NONNR_SHARE = 0.90   # province must report (non-NR) at least 90% of weeks
MIN_MEAN_CASES = 20.0    # and average at least 20 cases/week among reported weeks


def discretized_serial_interval(max_lag_weeks: int = 8) -> np.ndarray:
    mean_w = SI_MEAN_DAYS / 7.0
    sd_w = SI_SD_DAYS / 7.0
    shape = (mean_w / sd_w) ** 2
    scale = sd_w ** 2 / mean_w
    edges = np.arange(0.5, max_lag_weeks + 1.5, 1.0)
    cdf = gamma_dist.cdf(edges, a=shape, scale=scale)
    pmf = np.diff(cdf, prepend=0.0)
    w = np.zeros(max_lag_weeks + 1)
    w[1:] = pmf[: max_lag_weeks]
    w /= w.sum()
    return w


def total_infectiousness(I: np.ndarray, w: np.ndarray) -> np.ndarray:
    n = len(I)
    lam = np.zeros(n)
    for t in range(n):
        s_max = min(t, len(w) - 1)
        for s in range(1, s_max + 1):
            lam[t] += w[s] * I[t - s]
    return lam


def sliding_rt(I: np.ndarray, lam: np.ndarray, window: int):
    n = len(I)
    mean_r = np.full(n, np.nan)
    lo_r = np.full(n, np.nan)
    hi_r = np.full(n, np.nan)
    for t in range(window - 1, n):
        win = slice(t - window + 1, t + 1)
        sum_I = I[win].sum()
        sum_lam = lam[win].sum()
        if sum_lam <= 0:
            continue
        a_post = PRIOR_SHAPE + sum_I
        b_post = PRIOR_RATE + sum_lam
        mean_r[t] = a_post / b_post
        lo_r[t] = gamma_dist.ppf(0.025, a=a_post, scale=1 / b_post)
        hi_r[t] = gamma_dist.ppf(0.975, a=a_post, scale=1 / b_post)
    return mean_r, lo_r, hi_r


def load_panel():
    rows = list(csv.DictReader(open(DATA, newline="")))
    rows.sort(key=lambda r: (int(r["iso_year"]), int(r["iso_week"])))
    return rows


def series_for(rows, province):
    """Returns (dates, I) with NR/NA treated as 0 for the purposes of the
    renewal calc (documented explicitly as a limitation -- NR is 'unknown',
    not 'zero', but the renewal method needs a numeric series)."""
    dates, I = [], []
    for r in rows:
        dates.append(r["date"])
        v = r[province]
        I.append(0.0 if v in ("NR", "NA", "") else float(v.replace(",", "")))
    return dates, np.array(I)


def eligibility(rows, province):
    vals = [r[province] for r in rows]
    non_nr = [v for v in vals if v not in ("NR", "NA", "")]
    non_nr_share = len(non_nr) / len(vals)
    mean_cases = np.mean([float(v.replace(",", "")) for v in non_nr]) if non_nr else 0.0
    return non_nr_share, mean_cases


def main():
    rows = load_panel()
    w = discretized_serial_interval()

    print("Province eligibility for Rt estimation (need >=90% weeks reported, "
          ">=20 mean cases/week among reported weeks):\n")
    print(f"{'Province':<12} {'% reported':>10} {'mean cases':>11} {'eligible?':>10}")
    eligible_provinces = []
    for p in PROVINCES:
        share, mean_c = eligibility(rows, p)
        elig = share >= MIN_NONNR_SHARE and mean_c >= MIN_MEAN_CASES
        print(f"{p:<12} {share:>9.1%} {mean_c:>11.1f} {str(elig):>10}")
        if elig:
            eligible_provinces.append(p)

    all_results = {}
    for p in eligible_provinces:
        dates, I = series_for(rows, p)
        lam = total_infectiousness(I, w)
        mean_r, lo_r, hi_r = sliding_rt(I, lam, WINDOW_WEEKS)
        all_results[p] = (dates, I, mean_r, lo_r, hi_r)

    OUT_CSV.parent.mkdir(exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["province", "date", "cases", "Rt_mean", "Rt_lo95", "Rt_hi95"])
        for p, (dates, I, mean_r, lo_r, hi_r) in all_results.items():
            for d, i_val, m, lo, hi in zip(dates, I, mean_r, lo_r, hi_r):
                writer.writerow([p, d, int(i_val),
                                  f"{m:.3f}" if not np.isnan(m) else "",
                                  f"{lo:.3f}" if not np.isnan(lo) else "",
                                  f"{hi:.3f}" if not np.isnan(hi) else ""])
    print(f"\nwrote {OUT_CSV}")

    print("\nPer-province year-by-year mean Rt (eligible provinces only):")
    for p, (dates, I, mean_r, lo_r, hi_r) in all_results.items():
        print(f"\n-- {p} --")
        years = sorted(set(d[:4] for d in dates))
        for y in years:
            idx = [i for i, d in enumerate(dates) if d.startswith(y)]
            r_vals = mean_r[idx]
            r_valid = r_vals[~np.isnan(r_vals)]
            if len(r_valid) == 0:
                continue
            print(f"  {y}: mean Rt={np.nanmean(r_vals):.3f}, "
                  f"share>1={((r_valid > 1).mean()):.1%}, weeks={len(idx)}")


if __name__ == "__main__":
    main()
