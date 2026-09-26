"""
Step 03: Build a small "culture context" table, one row per world.

Uses the Zenodo Culture-Aware Music Recommendation Dataset:
  - users.tsv          -> how many Last.fm users come from each country
  - hofstede.tsv       -> Hofstede's cultural dimensions (0-100 scores)
  - world_happiness_report_2018.tsv -> happiness / social support scores

Output: processed/culture_context.csv

Run from the project folder:
    python scripts/03_culture_context.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# EDIT ME: the country we use to represent each world.
# ---------------------------------------------------------------------------
WORLD_TO_COUNTRY = {
    "India": "IN",
    "South Korea": "KR",
    "Latin America": "MX",
    "Europe": "DE",
    "West Africa": "NG",
}

# Countries we print checks for.
CHECK_COUNTRIES = ["IN", "KR", "MX", "BR", "GB", "FR", "DE", "NG", "GH"]

# The Zenodo files use "UK" for the United Kingdom instead of the ISO code "GB".
ZENODO_CODE = {"GB": "UK"}

# The happiness report uses full country names, not codes.
CODE_TO_NAME = {
    "IN": "India", "KR": "South Korea", "MX": "Mexico", "BR": "Brazil",
    "GB": "United Kingdom", "FR": "France", "DE": "Germany",
    "NG": "Nigeria", "GH": "Ghana",
}

HOFSTEDE_COLUMNS = ["power_distance", "individualism", "masculinity",
                    "uncertainty_avoidance", "long_term_orientation", "indulgence"]
WHR_COLUMNS = {  # original name -> our simpler name
    "Life Ladder": "life_ladder",
    "Social support": "social_support",
    "Positive affect": "positive_affect",
    "Negative affect": "negative_affect",
}

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_FILE = PROJECT_DIR / "processed" / "culture_context.csv"


def read_tsv(name):
    """The Zenodo files are tab-separated with no quoting."""
    return pd.read_csv(DATA_DIR / name, sep="\t", quoting=3)  # 3 = csv.QUOTE_NONE


def main():
    # --- 1. Load ----------------------------------------------------------
    users = read_tsv("users.tsv")
    hofstede = read_tsv("hofstede.tsv")
    whr = read_tsv("world_happiness_report_2018.tsv")
    print(f"users: {len(users):,} rows | hofstede: {len(hofstede)} rows | WHR: {len(whr):,} rows")

    # Hofstede: some cells may be blank or non-numeric; force numbers.
    for column in HOFSTEDE_COLUMNS:
        hofstede[column] = pd.to_numeric(hofstede[column], errors="coerce")

    # WHR has one row per country per year. Keep each country's latest year.
    whr = whr.sort_values("year").groupby("country").tail(1).set_index("country")

    user_counts = users["country"].value_counts()
    hofstede = hofstede.set_index("ctr")

    # --- 2. Checks: what do we have for each country? ---------------------
    check_rows = []
    for code in CHECK_COUNTRIES:
        zenodo_code = ZENODO_CODE.get(code, code)
        name = CODE_TO_NAME[code]
        check_rows.append({
            "code": code,
            "name": name,
            "lastfm_users": int(user_counts.get(zenodo_code, 0)),
            "has_hofstede": zenodo_code in hofstede.index,
            "has_whr": name in whr.index,
        })
    print("\nCHECK: data available per country")
    print(pd.DataFrame(check_rows).to_string(index=False))

    # --- 3. One row per world ---------------------------------------------
    rows = []
    for world, code in WORLD_TO_COUNTRY.items():
        zenodo_code = ZENODO_CODE.get(code, code)
        name = CODE_TO_NAME.get(code, code)
        row = {
            "world": world,
            "country_code": code,
            "country_name": name,
            "lastfm_users": int(user_counts.get(zenodo_code, 0)),
        }

        # Missing countries simply get empty (NaN) values. The app handles that.
        if zenodo_code in hofstede.index:
            for column in HOFSTEDE_COLUMNS:
                row[column] = hofstede.loc[zenodo_code, column]
        else:
            print(f"  NOTE: no Hofstede data for {name} ({code}) - leaving blank")
            for column in HOFSTEDE_COLUMNS:
                row[column] = None

        if name in whr.index:
            row["whr_year"] = int(whr.loc[name, "year"])
            for original, simple in WHR_COLUMNS.items():
                row[simple] = whr.loc[name, original]
        else:
            print(f"  NOTE: no World Happiness Report data for {name} - leaving blank")
            row["whr_year"] = None
            for simple in WHR_COLUMNS.values():
                row[simple] = None

        rows.append(row)

    context = pd.DataFrame(rows).round(3)

    # --- 4. Save ----------------------------------------------------------
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    context.to_csv(OUTPUT_FILE, index=False)
    print("\nCHECK: culture_context.csv")
    print(context.to_string(index=False))
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
