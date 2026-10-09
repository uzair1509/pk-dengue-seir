# Results: Has Pakistan's Dengue Transmission Declined, 2023–2026?

## The question

Using a complete weekly national dengue case-count series (171
consecutive weeks, 2023 week 22 through 2026 week 36, zero gaps), and an
Rt estimate over that window: **is there evidence that effective dengue
transmission in Pakistan has trended downward, or is the picture better
described as a strongly seasonal, no-clear-trend cycle?**

## Case counts by season

| Year | Weeks observed | Peak week | Peak weekly cases | Annual total (partial for 2023, 2026) |
|---|---|---|---|---|
| 2023 | 31 (from wk 22) | 17 Jul 2023 | 607 | 6,638 |
| 2024 | 53 | 28 Oct 2024 | **3,180** | **59,611** |
| 2025 | 52 | 27 Oct 2025 | 2,027 | 27,181 |
| 2026 | 35 (through wk 36) | 4 May 2026 | 541 | 6,174 (season incomplete) |

2024 was a major national outbreak year — roughly 5x the peak weekly case
count of 2023, and total reported cases nearly 9x higher. 2025 pulled
back substantially from 2024 but was still more than 4x 2023's total.
**2026's own peak season (typically August–November) is not yet in this
data** — the archive's latest available bulletin is week 36 (early
September) — so nothing can be concluded yet about whether 2026 continues
the pullback from 2024's peak.

## Effective reproduction number (Rt)

Using the Cori et al. (2013) renewal-equation estimator (serial interval:
Gamma, mean 15 days / SD 7 days; 4-week sliding window):

| Year | Mean Rt | Share of weeks with Rt > 1 |
|---|---|---|
| 2023 | 1.27 | 60.7% |
| 2024 | 1.31 | 52.8% |
| 2025 | 1.07 | 50.0% |
| 2026 (partial) | 1.20 | 37.1% |

Rt shows a clear, repeating annual pattern rather than a trend: it rises
above 1 as the transmission season starts (roughly April–May, as the
monsoon approaches), stays elevated through the outbreak, and falls well
below 1 over the winter off-season, every single year in the observed
window (see `dengue_rt.png`). The magnitude and duration of each year's
above-1 period differs — 2024's was both larger in case terms and had a
higher peak Rt than 2023 or 2025 — but the *pattern* is seasonal
recurrence, not a one-directional trend.

One estimation artifact worth flagging directly: at the start of each new
season, case counts jump from a near-zero off-season base, which the
renewal-equation method can turn into a very large, noisy Rt spike (e.g.
the >4.0 spike in early May 2024) — this reflects the small-numbers
instability of the estimator at a near-zero denominator, not a real,
precisely-estimated four-fold-per-serial-interval growth rate. The
qualitative "above/below 1" reading is robust; the exact peak magnitude
during these transition weeks is not.

## Bottom line

**No, there is no clean downward trend in Pakistan's dengue transmission
over 2023–2026.** The honest description is: a strongly seasonal disease
with a large amount of year-to-year variation in outbreak size, where
2024 was a substantially worse year than either its predecessor or
successor, and where the most recent season (2026) can't yet be assessed
because the surveillance archive doesn't yet cover its peak weeks. Anyone
claiming a "successful decline" from looking only at 2024→2025 without
also comparing back to 2023, or without waiting for 2026's full season,
would be overreading a single year-over-year comparison in a series with
this much natural variability.

## Extension 1: province-level Rt

National-level Rt can hide province-specific dynamics, so each of the 171
bulletins was re-parsed for its "Table 1" province/area breakdown (AJK,
Balochistan, GB, ICT, KP, Punjab, Sindh) plus each bulletin's stated
province reporting-compliance percentage.

**Data-quality finding first, because it shapes everything else:** Punjab
is marked "No Report" for dengue in 121 of 171 weeks (70.8%) in this
national table, despite reporting other diseases normally and despite
Punjab historically having large dengue outbreaks (Lahore, in particular).
This is consistent with Punjab running its own separate provincial dengue
surveillance/dashboard outside the NIH weekly bulletin's IDSR pipeline,
though that isn't confirmed from the bulletins themselves — it's a
plausible read of the pattern, not a documented fact. Either way, this
national dataset **cannot support a Punjab Rt estimate**, and any
Punjab-specific case counts appearing in a small number of bulletins in
this table were found to be internally inconsistent with the bulletin's
own province-sum-to-total arithmetic on 3 of 171 weeks and were
conservatively excluded rather than used.

Provinces were only given an Rt estimate if they cleared two bars: ≥90%
of weeks with a real (non-NR) case count, and ≥20 mean weekly cases among
reported weeks (below that, the renewal-equation denominator is too close
to zero to mean anything). Result: **KP, Sindh, and Balochistan qualify;
AJK, GB, ICT, and Punjab do not** (see `results/rt_estimates_province.csv`
for the eligibility table and full series).

| Province | 2023 mean Rt | 2024 mean Rt | 2025 mean Rt | 2026 mean Rt (partial) |
|---|---|---|---|---|
| KP | 1.38 | 1.43 | 1.76 | **2.24** |
| Sindh | 1.36 | 1.05 | 1.28 | 1.10 |
| Balochistan | 1.50 | 1.69 | 1.34 | 1.50 |

All three provinces show the same seasonal above/below-1 cycling as the
national series (see `dengue_rt_province.png`) — this part is not new.
What *is* new: **KP's partial-2026 mean Rt (2.24) is the single highest
province-year value in the whole series**, and KP's year-on-year mean Rt
has risen every year (1.38 → 1.43 → 1.76 → 2.24), unlike Sindh's, which
has stayed roughly flat. The same small-numbers caveat that applies to
the national early-season spikes applies here with extra force at the
province level (smaller absolute case counts, noisier denominator), and
2026 is still a partial season for every province — so this is a
genuinely notable divergence worth flagging, **not** a confirmed
"KP transmission is worsening" conclusion. It's the strongest concrete
lead for anyone extending this analysis once 2026's full season is in.

## Extension 2: reporting-compliance-adjusted case series

Using each bulletin's stated national IDSR compliance rate (share of
expected district reports actually received that week — mean 77.2%,
range 65–85% across all 171 weeks, never catastrophically low), a simple
adjusted series was built: `adjusted = reported / (compliance / 100)`.
This is explicitly a scale check, not a real correction — compliance
measures whether a district *filed a report*, not whether cases within a
filing district were completely or accurately counted, and it says
nothing about untested/unpresented cases. Weeks below 30% compliance
would have been excluded as too unreliable to extrapolate from, but none
occurred.

| Year | Reported total | Compliance-adjusted total | Multiplier |
|---|---|---|---|
| 2023 | 6,638 | 8,897 | 1.34x |
| 2024 | 59,611 | 74,010 | 1.24x |
| 2025 | 27,181 | 35,322 | 1.30x |
| 2026 (partial) | 6,174 | 8,000 | 1.30x |

The finding here is a robustness result: **the underreporting-scale
multiplier is stable across all four years (1.24x–1.34x)**, so adjusting
for reporting completeness does not change the comparative story at all
— 2024 is still the clear outbreak year by a wide margin, and there is
still no directional trend once the adjustment is applied (see
`dengue_compliance_adjusted.png`). The original "no clean downward trend"
conclusion is robust to this specific adjustment.

## Still open

- **Waiting for 2026's full season** before drawing any conclusion about
  whether the 2024→2025 pullback continued, and specifically whether
  KP's rising partial-year Rt persists once its actual peak season
  (Aug–Nov) is in the archive.
- A true accuracy correction (as opposed to a completeness-scale check)
  would need clinic- or lab-level case-ascertainment data, which no
  public bulletin provides.
