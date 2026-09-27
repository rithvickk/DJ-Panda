"""
Step 04: Copy the processed tables into the React app as JSON.

The web app (web/) has no Python server. It reads these three files, which
are bundled into the site when you run `npm run build`:
    web/src/data/songs.json      <- processed/song_pool.csv
    web/src/data/profiles.json   <- processed/mood_profiles.csv
    web/src/data/culture.json    <- processed/culture_context.csv

Run from the project folder (after steps 01, 02 and 03):
    python scripts/04_export_web_data.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_DIR / "processed"
WEB_DATA_DIR = PROJECT_DIR / "web" / "src" / "data"

FEATURES = ["danceability", "energy", "valence", "acousticness", "tempo"]

# processed file -> (web file, the columns the app actually reads).
EXPORTS = {
    "song_pool.csv": ("songs.json", [
        "track_id", "track_name", "artists", "album_name", "track_genre", "world", *FEATURES,
    ]),
    "mood_profiles.csv": ("profiles.json", [
        "mood", "intensity", "goal", "score_rule", "n_respondents", "median_bpm", "top_genres", *FEATURES,
    ]),
    "culture_context.csv": ("culture.json", [
        "world", "country_name", "lastfm_users", "indulgence", "whr_year", "social_support", "positive_affect",
    ]),
}


def main():
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for source, (target, columns) in EXPORTS.items():
        path = PROCESSED_DIR / source
        if not path.exists():
            raise FileNotFoundError(f"Missing processed/{source} - run steps 01-03 first")
        table = pd.read_csv(path)[columns]
        # NaN becomes null in JSON, which the app treats as "missing".
        table.to_json(WEB_DATA_DIR / target, orient="records", double_precision=4, indent=None)
        size_kb = (WEB_DATA_DIR / target).stat().st_size / 1024
        print(f"CHECK: {source:22} -> web/src/data/{target:14} {len(table):5} rows  {size_kb:6.0f} KB")


if __name__ == "__main__":
    main()
