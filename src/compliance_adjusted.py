"""Reporting-compliance-adjusted national dengue case series.

Each NIH bulletin states a national IDSR reporting compliance rate (share
of expected district reports actually received that week). This script
builds a simple compliance-adjusted case series:

    adjusted_cases = reported_cases / (compliance_national / 100)

This is a rough scale-up, not a real correction: compliance measures
whether a district *submitted a report at all*, not whether cases within
a submitting district were fully/accurately counted, and it says nothing
about health-seeking behaviour (people who never see a clinician aren't
in the denominator at all, no matter how "compliant" reporting is). It
also gets noisy and unreliable exactly when compliance is very low (a
40% compliance week inflates its case count 2.5x on a single, possibly
unrepresentative, statistic) -- so this is presented as an illustrative
sensitivity check on how much of the raw trend could plausibly be a
reporting-completeness artifact, not a replacement headline series.

Weeks with compliance < 30% are flagged separately and excluded from the
adjusted series (adjustment factor >3.3x on a single noisy input is not
informative) rather than silently extrapolated.
"""
import csv
from pathlib import Path

PROVINCE_PANEL = Path(__file__).parent.parent / "data" / "province_dengue_panel.csv"
NATIONAL_PANEL = Path(__file__).parent.parent / "data" / "dengue_panel.csv"
OUT_CSV = Path(__file__).parent.parent / "results" / "compliance_adjusted.csv"

MIN_RELIABLE_COMPLIANCE = 30.0  # below this, don't extrapolate


def main():
    prov_rows = {r["date"]: r for r in csv.DictReader(open(PROVINCE_PANEL, newline=""))}
    nat_rows = list(csv.DictReader(open(NATIONAL_PANEL, newline="")))

    out = []
    n_flagged = 0
    compliance_vals = []
    for r in nat_rows:
        d = r["date"]
        if d not in prov_rows or r["dengue_cases"] == "":
            continue
        cases = int(r["dengue_cases"])
        comp_str = prov_rows[d]["compliance_National"]
        if comp_str in ("NA", ""):
            continue
        comp = float(comp_str)
        compliance_vals.append(comp)
        if comp < MIN_RELIABLE_COMPLIANCE:
            n_flagged += 1
            adjusted = ""
            reliable = False
        else:
            adjusted = round(cases / (comp / 100.0), 1)
            reliable = True
        out.append([d, cases, comp, adjusted, reliable])

    OUT_CSV.parent.mkdir(exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "reported_cases", "compliance_pct", "adjusted_cases", "reliable"])
        w.writerows(out)

    print(f"wrote {OUT_CSV}: {len(out)} weeks")
    print(f"national compliance: mean={sum(compliance_vals)/len(compliance_vals):.1f}%, "
          f"min={min(compliance_vals):.0f}%, max={max(compliance_vals):.0f}%")
    print(f"weeks below {MIN_RELIABLE_COMPLIANCE:.0f}% compliance (adjustment not computed): {n_flagged}/{len(out)}")

    reliable_rows = [r for r in out if r[4]]
    total_reported = sum(r[1] for r in reliable_rows)
    total_adjusted = sum(r[3] for r in reliable_rows)
    print(f"\nOver the {len(reliable_rows)} weeks with reliable (>=30%) compliance:")
    print(f"  total reported cases: {total_reported:,}")
    print(f"  total compliance-adjusted cases: {total_adjusted:,.0f}")
    print(f"  implied average underreporting multiplier: {total_adjusted/total_reported:.2f}x")

    # year-by-year
    years = sorted(set(r[0][:4] for r in reliable_rows))
    print("\nyear | reported total | adjusted total | multiplier")
    for y in years:
        yr = [r for r in reliable_rows if r[0].startswith(y)]
        rep = sum(r[1] for r in yr)
        adj = sum(r[3] for r in yr)
        print(f"{y} | {rep:>14,} | {adj:>14,.0f} | {adj/rep:.2f}x")


if __name__ == "__main__":
    main()
