"""Build a clean, date-indexed weekly dengue panel from the raw NIH IDSR
bulletin extraction (data/nih_idsr_raw.csv).

The raw file has one row per bulletin PDF, in whatever order the NIH
archive page listed them (newest first, with real gaps -- NIH does not
publish every ISO week, especially in 2021-2023). This script:

  1. Converts (week, year) -> the Monday date of that ISO week.
  2. Sorts ascending by date.
  3. Drops exact duplicate (week, year) pairs if any slip through (there
     shouldn't be any -- build_panel asserts this).
  4. Leaves genuine gaps as missing rows (does NOT interpolate) and
     writes a manifest of which ISO weeks are missing, so this is an
     honest, auditable panel rather than a smoothed-over one.
"""
import csv
import datetime as dt
from pathlib import Path

RAW = Path(__file__).parent.parent / "data" / "nih_idsr_raw.csv"
OUT = Path(__file__).parent.parent / "data" / "dengue_panel.csv"
GAPS_OUT = Path(__file__).parent.parent / "data" / "missing_weeks.csv"


def iso_week_monday(year: int, week: int) -> dt.date:
    """Monday of the given ISO year/week."""
    return dt.date.fromisocalendar(year, week, 1)


def main():
    rows = []
    with open(RAW, newline="") as f:
        for r in csv.DictReader(f):
            week, year = int(r["week"]), int(r["year"])
            date = iso_week_monday(year, week)
            dengue = int(r["dengue"]) if r["dengue"] else None
            malaria = int(r["malaria"]) if r["malaria"] else None
            rows.append({"date": date, "year": year, "week": week,
                         "dengue": dengue, "malaria": malaria,
                         "num_pages": int(r["num_pages"]), "url": r["url"]})

    # dedupe check
    seen = set()
    for r in rows:
        key = (r["year"], r["week"])
        assert key not in seen, f"duplicate week {key}"
        seen.add(key)

    rows.sort(key=lambda r: r["date"])

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "iso_year", "iso_week", "dengue_cases", "malaria_cases", "num_pages", "source_url"])
        for r in rows:
            w.writerow([r["date"].isoformat(), r["year"], r["week"],
                        r["dengue"] if r["dengue"] is not None else "",
                        r["malaria"] if r["malaria"] is not None else "",
                        r["num_pages"], r["url"]])

    # find missing ISO weeks between first and last date present
    present = {(r["year"], r["week"]) for r in rows}
    start, end = rows[0]["date"], rows[-1]["date"]
    missing = []
    d = start
    while d <= end:
        y, wk, _ = d.isocalendar()
        if (y, wk) not in present and (y, wk) not in {m for m in missing}:
            missing.append((y, wk))
        d += dt.timedelta(days=7)

    with open(GAPS_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iso_year", "iso_week", "monday_date"])
        for y, wk in missing:
            w.writerow([y, wk, iso_week_monday(y, wk).isoformat()])

    n_null_dengue = sum(1 for r in rows if r["dengue"] is None)
    print(f"wrote {len(rows)} weeks to {OUT.name} "
          f"({rows[0]['date']} to {rows[-1]['date']})")
    print(f"  {n_null_dengue} weeks have no valid dengue total (NR/parse-null)")
    print(f"  {len(missing)} ISO weeks in range are entirely missing from the archive "
          f"(written to {GAPS_OUT.name})")


if __name__ == "__main__":
    main()
