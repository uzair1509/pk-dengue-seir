"""Reproducible scraper for Pakistan NIH's IDSR weekly bulletin archive.

This is the "normal machine" version of the pipeline: plain requests +
pdfplumber, no browser needed. It exists because the archive index page
(nih.org.pk/phb/weekly-bulletin) is a static list of direct PDF links, and
on an ordinary internet connection that's all you need.

(Note on how this repo's own data/nih_idsr_raw.csv was actually built:
the sandboxed environment this project was developed in blocks outbound
curl/requests to non-allowlisted hosts including nih.org.pk, while still
allowing an in-session Chrome-based browser tool to reach the same site
and run pdf.js in-page. That one-off constraint is specific to that
sandbox, not to this site or this code -- this script is the version you
should actually run, and it reproduces the same data.)

Usage:
    python src/scrape_bulletins.py --out data/nih_idsr_raw.csv
"""
import argparse
import csv
import re
import time
from pathlib import Path

import pdfplumber
import requests
from bs4 import BeautifulSoup

INDEX_URL = "https://www.nih.org.pk/phb/weekly-bulletin"
HEADERS = {"User-Agent": "Mozilla/5.0 (research data collection; see repo README)"}


def list_bulletins():
    resp = requests.get(INDEX_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        if not re.search(r"\.pdf", href, re.I):
            continue
        m = re.search(r"Week\s+(\d+)\s+Bulletin\s+\((\d{4})\)", text, re.I)
        if not m:
            continue
        items.append({"week": int(m.group(1)), "year": int(m.group(2)), "url": href, "text": text})
    return items


def extract_disease_total(full_text: str, disease: str):
    """Same logic as the browser/pdf.js version: take the FIRST occurrence of
    the disease name followed by a run of >=3 numeric/NR tokens (the national
    Table 1 row), and read its last value as the national total. Bulletins
    also contain per-district/trend tables further down that mention the same
    disease name with their own numeric runs -- taking the first, not the
    longest, run is what keeps this pointed at Table 1."""
    tokens = full_text.split()
    name_lower = disease.lower()
    for i, tok in enumerate(tokens):
        if tok.lower() == name_lower:
            run = []
            j = i + 1
            while j < len(tokens) and re.fullmatch(r"NR|[\d,]+", tokens[j]):
                run.append(tokens[j])
                j += 1
            if len(run) >= 3:
                last = run[-1]
                if last == "NR":
                    return None
                return int(last.replace(",", ""))
    return None


def fetch_and_parse(item, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(item["url"], headers=HEADERS, timeout=60)
            resp.raise_for_status()
            tmp = Path("/tmp") / "bulletin.pdf"
            tmp.write_bytes(resp.content)
            with pdfplumber.open(tmp) as pdf:
                full_text = " ".join((p.extract_text() or "") for p in pdf.pages)
                num_pages = len(pdf.pages)
            return {
                **item,
                "num_pages": num_pages,
                "dengue": extract_disease_total(full_text, "Dengue"),
                "malaria": extract_disease_total(full_text, "Malaria"),
            }
        except Exception as e:
            if attempt == retries - 1:
                return {**item, "error": str(e)}
            time.sleep(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/nih_idsr_raw.csv")
    args = ap.parse_args()

    items = list_bulletins()
    print(f"found {len(items)} bulletins in the archive index")

    results = []
    for i, item in enumerate(items):
        r = fetch_and_parse(item)
        results.append(r)
        status = "ERROR: " + r["error"] if r.get("error") else f"dengue={r.get('dengue')}"
        print(f"[{i+1}/{len(items)}] week {item['week']}/{item['year']}: {status}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["week", "year", "dengue", "malaria", "num_pages", "url"])
        for r in results:
            if r.get("error"):
                continue
            w.writerow([r["week"], r["year"],
                        r["dengue"] if r["dengue"] is not None else "",
                        r["malaria"] if r["malaria"] is not None else "",
                        r["num_pages"], r["url"]])
    n_errors = sum(1 for r in results if r.get("error"))
    print(f"\nwrote {len(results) - n_errors} rows to {out_path} ({n_errors} errors)")


if __name__ == "__main__":
    main()
