"""Estimate the effective reproduction number Rt for Pakistan dengue from
weekly national case counts, using the renewal-equation method of
Cori et al. (2013) ("A New Framework and Software to Estimate
Time-Varying Reproduction Numbers During Epidemics", Am J Epidemiol).

Why this instead of fitting a mechanistic SEIR/SIR by MLE:
dengue is vector-borne (human <-> mosquito), so a "true" mechanistic R0
needs vector density, biting rate, extrinsic incubation period, and the
size of the susceptible human population -- none of which this case-count
series identifies on its own, and guessing them would manufacture false
precision. The renewal-equation approach only needs the case time series
and a serial-interval distribution, is the standard tool epidemiologists
actually use for exactly this kind of routine surveillance data (it is
the method behind the EpiEstim R package and the Rt estimates public
health agencies publish), and is estimated by a simple, well-understood
Bayesian conjugate-Gamma update -- no numerical optimizer, no local-minima
risk, no silent misspecification.

Serial interval: dengue's mean serial interval (time between successive
cases in a transmission chain, human-mosquito-human) has been estimated
at roughly 15 days (SD ~7 days) in the literature (e.g. Nishiura 2006;
subsequent dengue Rt studies commonly use 15-20 day means). We use a
discretized Gamma(mean=15d, sd=7d) converted to weekly lags, and note
this is a literature-based assumption, not something re-estimated here.
"""
import csv
from pathlib import Path

import numpy as np
from scipy.stats import gamma as gamma_dist

DATA = Path(__file__).parent.parent / "data" / "dengue_panel.csv"
OUT = Path(__file__).parent.parent / "results" / "rt_estimates.csv"
CUTOFF = "2023-05-29"  # first week of the gap-free, weekly-complete window

SI_MEAN_DAYS = 15.0
SI_SD_DAYS = 7.0
WINDOW_WEEKS = 4          # sliding window for the Rt estimate (smooths weekly noise)
PRIOR_SHAPE = 1.0         # Gamma(1, 1/5) prior on R, the EpiEstim default
PRIOR_RATE = 0.2


def discretized_serial_interval(max_lag_weeks: int = 8) -> np.ndarray:
    """Discretized weekly serial-interval PMF w[1..max_lag], w[0] unused (=0)."""
    mean_w = SI_MEAN_DAYS / 7.0
    sd_w = SI_SD_DAYS / 7.0
    shape = (mean_w / sd_w) ** 2
    scale = sd_w ** 2 / mean_w
    # discretize by integrating the continuous Gamma density over [k-0.5, k+0.5)
    edges = np.arange(0.5, max_lag_weeks + 1.5, 1.0)
    cdf = gamma_dist.cdf(edges, a=shape, scale=scale)
    pmf = np.diff(cdf, prepend=0.0)
    w = np.zeros(max_lag_weeks + 1)
    w[1:] = pmf[: max_lag_weeks]
    w /= w.sum()
    return w


def load_series():
    dates, I = [], []
    with open(DATA, newline="") as f:
        for r in csv.DictReader(f):
            if r["date"] < CUTOFF:
                continue
            dates.append(r["date"])
            I.append(int(r["dengue_cases"]))
    return dates, np.array(I, dtype=float)


def total_infectiousness(I: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Lambda_t = sum_{s=1}^{min(t, len(w)-1)} w[s] * I[t-s], for t=0..n-1 (0-indexed)."""
    n = len(I)
    lam = np.zeros(n)
    for t in range(n):
        s_max = min(t, len(w) - 1)
        for s in range(1, s_max + 1):
            lam[t] += w[s] * I[t - s]
    return lam


def sliding_rt(I: np.ndarray, lam: np.ndarray, window: int):
    """Cori et al. posterior mean/CI for R in each sliding window ending at t."""
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


def main():
    dates, I = load_series()
    w = discretized_serial_interval()
    lam = total_infectiousness(I, w)
    mean_r, lo_r, hi_r = sliding_rt(I, lam, WINDOW_WEEKS)

    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "dengue_cases", "Rt_mean", "Rt_lo95", "Rt_hi95"])
        for d, i_val, m, lo, hi in zip(dates, I, mean_r, lo_r, hi_r):
            writer.writerow([d, int(i_val),
                              f"{m:.3f}" if not np.isnan(m) else "",
                              f"{lo:.3f}" if not np.isnan(lo) else "",
                              f"{hi:.3f}" if not np.isnan(hi) else ""])

    valid = ~np.isnan(mean_r)
    print(f"serial interval PMF (weeks 1..8): {np.round(w[1:], 3)}")
    print(f"n weeks with Rt estimate: {valid.sum()} / {len(I)}")
    print(f"overall mean Rt: {np.nanmean(mean_r):.3f}")
    print(f"share of weeks with Rt point estimate > 1: {(mean_r[valid] > 1).mean():.2%}")

    # year-by-year summary
    years = sorted(set(d[:4] for d in dates))
    print("\nyear | weeks | mean case/wk | mean Rt | share Rt>1")
    for y in years:
        idx = [i for i, d in enumerate(dates) if d.startswith(y)]
        r_vals = mean_r[idx]
        r_valid = r_vals[~np.isnan(r_vals)]
        print(f"{y} | {len(idx):5d} | {I[idx].mean():11.1f} | "
              f"{np.nanmean(r_vals):7.3f} | {(r_valid > 1).mean():9.2%}")


if __name__ == "__main__":
    main()
