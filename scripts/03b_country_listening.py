"""
Step 03b (OPTIONAL stretch): average audio profile of what each country listens to.

events.tsv has about 351 MILLION rows - far too big for pandas. We use polars
in "lazy + streaming" mode: polars reads the file in small chunks, keeps only
running totals per country, and never holds the whole file in memory.

Needs: pip install polars
Needs: data/events.tsv (download it from Zenodo first; about 20+ GB)

Output: processed/country_listening.csv (one row per country)

Run from the project folder:
    python scripts/03b_country_listening.py
    python scripts/03b_country_listening.py path/to/events.tsv   # use a different file
"""

import sys
from pathlib import Path

import polars as pl

sys.stdout.reconfigure(encoding="utf-8")

# EDIT ME: set to a number like 5_000_000 for a quick test run. None = all rows.
MAX_ROWS = None

FEATURES = ["danceability", "energy", "valence", "acousticness", "tempo"]

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
EVENTS_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR / "events.tsv"
OUTPUT_FILE = PROJECT_DIR / "processed" / "country_listening.csv"


def scan_tsv(path, n_rows=None):
    """Lazily scan a Zenodo TSV file (tab-separated, no quoting). Nothing is read yet."""
    return pl.scan_csv(path, separator="\t", quote_char=None, n_rows=n_rows)


def main():
    if not EVENTS_FILE.exists():
        print(f"events file not found: {EVENTS_FILE}")
        print("This step is optional. Download events.tsv from Zenodo to run it.")
        return

    # --- 1. Describe the query (still nothing loaded) ---------------------
    events = scan_tsv(EVENTS_FILE, n_rows=MAX_ROWS).select(["user_id", "track_id"])
    users = scan_tsv(DATA_DIR / "users.tsv").select(["user_id", "country"])
    features = scan_tsv(DATA_DIR / "acoustic_features_lfm_id.tsv").select(["track_id"] + FEATURES)

    per_country = (
        events
        .join(users, on="user_id", how="inner")        # add each listener's country
        .join(features, on="track_id", how="inner")    # add the track's audio features
        .group_by("country")
        .agg(
            [pl.len().alias("listening_events"),
             pl.col("user_id").n_unique().alias("users")]
            + [pl.col(f).mean().alias(f) for f in FEATURES]
        )
        .sort("listening_events", descending=True)
    )

    # --- 2. Run it in streaming mode ---------------------------------------
    print(f"Streaming {EVENTS_FILE} (rows: {'all' if MAX_ROWS is None else MAX_ROWS}) ...")
    try:
        result = per_country.collect(engine="streaming")   # polars >= 1.23
    except TypeError:
        result = per_country.collect(streaming=True)       # older polars

    # --- 3. Save + checks ---------------------------------------------------
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    result.write_csv(OUTPUT_FILE)

    print(f"\nCHECK: {result.height} countries, "
          f"{result['listening_events'].sum():,} matched listening events")
    with pl.Config(tbl_rows=15, tbl_cols=10):
        print(result.head(15))
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
