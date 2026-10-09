# Pakistan Dengue Transmission: A Weekly Surveillance Panel and Rt Estimate

A from-scratch weekly national dengue case-count panel for Pakistan
(May 2023 – September 2026, 171 consecutive weeks, no gaps), built by
extracting the "Table 1: Province/Area-wise distribution" figures out of
198 individual NIH weekly surveillance bulletin PDFs, and used to estimate
the effective reproduction number (Rt) of dengue transmission over that
period using the standard renewal-equation method (Cori et al., 2013).

**Headline finding:** dengue transmission in Pakistan has *not* shown a
steady decline over 2023–2026. 2024 was a major outbreak year (peak week
~3,180 national cases, roughly 5x 2023's peak); 2025 partially reverted
but was still well above 2023 levels (peak ~2,030). Rt cycles regularly
above and below 1 on an annual seasonal clock (transmission grows from
~May, peaks ~August–November, collapses over winter) rather than trending
in one direction. This conclusion holds up under a reporting-completeness
adjustment (underreporting scale is stable at ~1.24-1.34x every year — see
below). See `results/RESULTS.md` for the full write-up.

**Two extensions beyond the national headline:** province-level Rt for
the three provinces (KP, Sindh, Balochistan) with reporting complete
enough to support it — Punjab is "No Report" for dengue in 71% of
bulletins and can't be estimated at all — surfaced a genuine lead: KP's
partial-2026 mean Rt (2.24) is the highest province-year value in the
whole series, rising every year since 2023, unlike Sindh's flat pattern.
And a compliance-adjusted case series (scaling reported cases by each
week's national IDSR reporting-completeness rate) shows the
underreporting multiplier is stable across all four years, so it doesn't
change the "no clean trend" conclusion — a robustness check, not a
different story.

## Why this exists

This project extends a Biology A* interest and a finance/econometrics
GitHub portfolio (see the companion
[`psx-censored-volatility`](https://github.com/uzair1509/psx-censored-volatility)
/ [`mtgarch`](https://pypi.org/project/mtgarch/) repos) into public-health
surveillance data — same standard, different domain: get real data, be
honest about what it can and can't support, and answer one specific
question properly rather than a vague survey.

## Data

**Source:** Pakistan NIH's [IDSR Weekly Public Health
Bulletin](https://www.nih.org.pk/phb/weekly-bulletin) archive — 198
individual PDF bulletins, 2021 week 21 through 2026 week 36. Each bulletin
contains a national province/area-wise case table for ~25 reportable
diseases, including dengue and malaria.

**What was pulled:** the national weekly dengue and malaria case totals
(the last column, "Total", of each bulletin's Table 1). This required
parsing the PDF text directly — the table format itself changed multiple
times over five years (column sets, disease list, layout), so the
extraction logic locates the *first* occurrence of the disease name
followed by a run of numeric/`NR` table cells (this is always the primary
national table; later pages contain per-district and historical-trend
tables that also mention each disease and would give a wrong "total" if
matched instead — see `src/scrape_bulletins.py` docstring for the
specifics and a worked example of why the naive "longest match" approach
is wrong).

**Known limitations — read before using this data for anything else:**

- **Reporting is not 100% complete in a given week.** Bulletins publish a
  province-level compliance rate (expected vs. received district reports);
  in the observed period this ranges roughly 55–100% depending on
  province and week, and AJK in particular is frequently `NR` (no report
  received) even in the recent, well-covered window. National weekly
  totals are therefore a lower bound on true case counts, with the degree
  of undercount varying over time — not a constant fraction you can just
  rescale away.
- **The archive itself has real gaps**, concentrated entirely in
  2021–2023 (see `data/missing_weeks.csv` — 78 ISO weeks with no bulletin
  published at all, mostly in 2022). **From 2023 week 22 onward the
  archive is complete and weekly with zero gaps** (171 consecutive weeks)
  — this is the window all analysis in this repo uses; 2021–2023-week-21
  data is saved in the raw file but not used for the Rt estimate.
- **This is surveillance data, not a validated case-definition dataset.**
  All reported cases are suspected, not lab-confirmed (stated on every
  bulletin). Case counts reflect clinical presentation and health-seeking
  behavior as much as true incidence.
- **Punjab is absent from this dataset for dengue specifically.** It's
  marked "No Report" in the national table in 71% of the 171 bulletins
  used here, likely because Punjab runs its own separate dengue
  surveillance outside this pipeline (not confirmed from the bulletins
  themselves). No Punjab-specific claim can be made from this dataset.
- **2026 is a partial year.** The archive's most recent bulletin (as of
  building this) is week 36 (early September). Pakistan's dengue season
  historically peaks around weeks 30–45 (Aug–Nov), so 2026's actual peak
  is very likely not yet in this data — don't read anything into the
  apparent 2026 numbers looking smaller than 2024/2025's full seasons.

## Method

Rather than fitting a mechanistic SEIR/SIR model by MLE, this project
estimates the time-varying effective reproduction number Rt directly from
the case series using the **Cori et al. (2013) renewal-equation method**
(the method behind the widely-used EpiEstim R package, and what most
public health agencies actually publish as "Rt").

**Why not a mechanistic SEIR/SIR fit:** dengue is vector-borne
(human↔mosquito), so a mechanistically "real" R0 needs vector density,
biting rate, extrinsic incubation period, and the size of the susceptible
human population — none of which a national weekly case-count series
identifies on its own. Fitting a human-only SIR to it and reporting an R0
would be manufacturing false precision from parameters the data can't
actually pin down. The renewal-equation approach only needs the case
series and a serial-interval distribution, and is estimated by a simple,
well-understood Bayesian conjugate-Gamma update — no optimizer, no
local-minima risk.

- **Serial interval:** literature-based Gamma(mean = 15 days, SD = 7
  days) (consistent with published dengue serial-interval estimates,
  e.g. Nishiura 2006), discretized to weekly lags.
- **Estimation window:** 4-week sliding window, Gamma(1, 0.2) prior (the
  EpiEstim default) — posterior mean and 95% credible interval reported
  per week.
- This is a standard, off-the-shelf epidemiological method applied
  correctly to real data, not a novel statistical contribution — the
  contribution here is the data pipeline and the honest handling of its
  limitations.

## Repository layout

```
data/
  nih_idsr_raw.csv            one row per bulletin PDF (as scraped)
  dengue_panel.csv            cleaned, date-sorted national weekly panel
  province_dengue_panel.csv   per-province dengue counts + compliance %, 171 weeks
  missing_weeks.csv           ISO weeks with no bulletin in the archive
results/
  rt_estimates.csv             weekly national Rt posterior mean + 95% CI
  rt_estimates_province.csv    weekly Rt for KP/Sindh/Balochistan (eligible provinces)
  compliance_adjusted.csv      reported vs. compliance-adjusted national case series
  dengue_rt.png                national case counts + Rt plot
  dengue_rt_province.png       province-level Rt plot
  dengue_compliance_adjusted.png  reported vs. adjusted case series plot
  RESULTS.md                   full write-up of the finding
src/
  scrape_bulletins.py       reproducible scraper (requests + pdfplumber)
  build_panel.py            raw bulletin rows -> clean date-indexed national panel
  estimate_rt.py            Cori et al. renewal-equation Rt estimation (national)
  estimate_rt_province.py   same method, per eligible province
  compliance_adjusted.py    reporting-compliance-adjusted case series
  plot_rt.py                national case-count + Rt plot
  plot_province_rt.py       province Rt plot + compliance-adjusted plot
```

## Reproducing

```bash
pip install requests beautifulsoup4 pdfplumber numpy scipy matplotlib
python src/scrape_bulletins.py --out data/nih_idsr_raw.csv
python src/build_panel.py
python src/estimate_rt.py
python src/plot_rt.py

# province-level extension (needs data/province_dengue_panel.csv --
# see src/estimate_rt_province.py's docstring for how that panel was built)
python src/estimate_rt_province.py
python src/compliance_adjusted.py
python src/plot_province_rt.py
```

## License

Code: MIT. The underlying NIH bulletin data is a public-sector Pakistani
government health surveillance publication; no license is stated on the
source site, so treat the extracted numbers as public-interest research
use and cite the NIH IDSR Weekly Bulletin as the primary source.
