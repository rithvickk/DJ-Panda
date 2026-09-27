"""
Step 01: Build the song pool.

Reads the Spotify Tracks Dataset (data/spotify_tracks.csv), keeps only the
genres that belong to our five musical "worlds", cleans it up, and saves a
small file the app can load quickly: processed/song_pool.csv

Run from the project folder:
    python scripts/01_build_song_pool.py
"""

import sys
from pathlib import Path

import pandas as pd

# Windows terminals sometimes can't print accents (e.g. "Tití"). This fixes that.
sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# EDIT ME: which Spotify track_genre values belong to each world.
# The world names here must match WORLDS in web/src/lib/dj.js.
# ---------------------------------------------------------------------------
WORLD_TO_GENRES = {
    "India": ["indian"],
    "South Korea": ["k-pop"],
    "Latin America": ["latin", "latino"],
    "Europe": ["british", "french", "german"],
    # NOTE: in this dataset the "afrobeat" genre is mostly Brazilian and Latin
    # funk (Criolo, BaianaSystem, Jorge Drexler...), not West African music.
    # So West Africa is built from WORLD_ARTISTS below instead.
    "West Africa": [],
}

# EDIT ME: artists whose songs belong to a world, found in ANY track_genre.
# A song matches if ANY of its credited artists is in the list.
# This overrides the genre mapping above.
WORLD_ARTISTS = {
    "West Africa": [
        # Nigeria
        "Burna Boy", "Wizkid", "Omah Lay", "Fireboy DML", "Tiwa Savage", "Mr Eazi",
        "Yemi Alade", "Olamide", "P-Square", "Fela Kuti", "Femi Kuti", "Tony Allen",
        "William Onyeabor", "Patoranking", "Wande Coal", "D'banj", "Rema", "Flavour",
        "2Baba", "Phyno", "Timaya", "Iyanya", "Peruzzi", "Reekado Banks", "Ice Prince",
        "Lil Kesh", "Seyi Shay", "Larry Gaaga", "Orlando Julius", "SPINALL",
        "DJ Neptune", "Show Dem Camp", "Limoblaze", "Eben",
        # Ghana
        "Sarkodie", "Stonebwoy", "Shatta Wale", "R2Bees", "Amaarae", "Ebo Taylor",
        "Juls", "Eugy",
        # Mali, Niger, Senegal, Benin
        "Tinariwen", "Ali Farka Touré", "Amadou & Mariam", "Salif Keita", "Bombino",
        "Youssou N'Dour", "Angelique Kidjo",
    ],
}

# EDIT ME: artists to remove from a world (the genre label was wrong for them).
EXCLUDE_ARTISTS = {
    "South Korea": ["Yuvan Shankar Raja", "Dhanush", "Alka Yagnik", "Jubin Nautiyal",
                    "Izzamuzzic", "RADWIMPS"],
}

# How many songs to keep per world (the most popular ones).
SONGS_PER_WORLD = 5

# Paths (built from this file's location so the script works from any folder).
PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_DIR / "data" / "spotify_tracks.csv"
OUTPUT_FILE = PROJECT_DIR / "processed" / "song_pool.csv"

# Columns the app needs. Everything else is dropped to keep the file small.
KEEP_COLUMNS = [
    "track_id", "track_name", "artists", "album_name", "popularity",
    "duration_ms", "danceability", "energy", "valence", "acousticness",
    "tempo", "track_genre", "world",
]


def main():
    # --- 1. Load ----------------------------------------------------------
    print(f"Loading {INPUT_FILE} ...")
    tracks = pd.read_csv(INPUT_FILE)
    # The Hugging Face / Kaggle copy has an unnamed index column. Drop it.
    tracks = tracks.drop(columns=[c for c in tracks.columns if c.startswith("Unnamed")])
    print(f"  Loaded {len(tracks):,} rows and {tracks.shape[1]} columns")

    # --- 2. Tag each track with its world --------------------------------
    # Flip the dictionary around: genre -> world
    genre_to_world = {}
    for world, genres in WORLD_TO_GENRES.items():
        for genre in genres:
            genre_to_world[genre] = world

    tracks["world"] = tracks["track_genre"].map(genre_to_world)

    # Warn if a genre in the dictionary was not found at all (probably a typo).
    found_genres = set(tracks["track_genre"].unique())
    for genre in genre_to_world:
        if genre not in found_genres:
            print(f"  WARNING: genre '{genre}' not found in spotify_tracks.csv - check spelling")

    # "artists" looks like "Burna Boy;Ed Sheeran", so split it into a list.
    artist_lists = tracks["artists"].fillna("").str.split(";")

    # Artist lists override the genre mapping.
    for world, artists in WORLD_ARTISTS.items():
        wanted = set(artists)
        matches = artist_lists.apply(lambda names: any(name in wanted for name in names))
        tracks.loc[matches, "world"] = world
        print(f"  Artist list for {world}: matched {matches.sum():,} rows")

    # Remove mislabeled artists.
    for world, artists in EXCLUDE_ARTISTS.items():
        unwanted = set(artists)
        matches = (tracks["world"] == world) & artist_lists.apply(
            lambda names: any(name in unwanted for name in names))
        tracks.loc[matches, "world"] = None
        print(f"  Excluded {matches.sum():,} rows from {world}")

    tracks = tracks.dropna(subset=["world"])

    print("\nCHECK: raw track counts per world (before cleaning)")
    print(tracks["world"].value_counts().to_string())

    # --- 3. Clean ---------------------------------------------------------
    before = len(tracks)
    # Sort by popularity first so that, among duplicates, we keep the most popular copy.
    tracks = tracks.sort_values("popularity", ascending=False)
    tracks = tracks.drop_duplicates(subset=["track_name", "artists"])
    print(f"\nDropped {before - len(tracks):,} duplicate (track_name, artists) rows")

    before = len(tracks)
    tracks = tracks[tracks["explicit"] == False]  # noqa: E712 (explicit column is True/False)
    print(f"Dropped {before - len(tracks):,} explicit tracks")

    before = len(tracks)
    tracks = tracks.dropna(subset=["danceability", "energy", "valence", "acousticness", "tempo"])
    tracks = tracks[tracks["tempo"] > 0]  # a tempo of 0 means Spotify could not detect it
    print(f"Dropped {before - len(tracks):,} tracks with missing audio features or tempo = 0")

    # --- 4. Keep the top N per world by popularity -----------------------
    song_pool = (
        tracks.sort_values("popularity", ascending=False)
        .groupby("world")
        .head(SONGS_PER_WORLD)
    )
    song_pool = song_pool[KEEP_COLUMNS].sort_values(["world", "popularity"], ascending=[True, False])

    # --- 5. Save + print checks -------------------------------------------
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    song_pool.to_csv(OUTPUT_FILE, index=False)

    print(f"\nCHECK: final songs per world (target {SONGS_PER_WORLD})")
    counts = song_pool["world"].value_counts()
    print(counts.to_string())
    for world in WORLD_TO_GENRES:
        if counts.get(world, 0) < SONGS_PER_WORLD:
            print(f"  NOTE: {world} has only {counts.get(world, 0)} songs (fewer than {SONGS_PER_WORLD})")

    print("\nCHECK: average audio features per world")
    features = ["danceability", "energy", "valence", "acousticness", "tempo"]
    print(song_pool.groupby("world")[features].mean().round(2).to_string())

    print("\nCHECK: top 2 songs per world")
    print(song_pool.groupby("world").head(2)[["world", "track_name", "artists", "popularity"]].to_string(index=False))

    print(f"\nSaved {len(song_pool):,} songs to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
