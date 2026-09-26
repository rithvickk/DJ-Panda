"""
The "brain" of Culture DJ: loading data, matching songs, and writing text.

Nothing in here uses Streamlit, so you can test it from a plain Python shell:
    python dj_logic.py
"""

import math
import random
from pathlib import Path

import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parent / "processed"

# ---------------------------------------------------------------------------
# Choices shown in the app. Moods and goals must match scripts/02_mood_profiles.py
# and world names must match scripts/01_build_song_pool.py.
# ---------------------------------------------------------------------------
MOODS = ["Stressed", "Drained", "Lonely", "Restless", "Can't sleep", "Happy", "Energetic"]
GOALS = ["Calm down", "Lift my mood", "Get energized", "Keep the vibe"]

WORLDS = {
    "India": {"subtitle": "Bollywood", "dance": "Bollywood-inspired"},
    "South Korea": {"subtitle": "K-pop", "dance": "K-pop-inspired choreography"},
    "Latin America": {"subtitle": "Latin & reggaeton", "dance": "salsa-inspired"},
    "Europe": {"subtitle": "British, French & German", "dance": "Eurodance club-inspired"},
    "West Africa": {"subtitle": "Afrobeats", "dance": "Afrobeats-inspired"},
}

# ---------------------------------------------------------------------------
# EDIT ME: matching settings.
# A bigger weight means that feature matters more when finding the closest song.
# ---------------------------------------------------------------------------
FEATURES = ["danceability", "energy", "valence", "acousticness", "tempo"]
FEATURE_WEIGHTS = {
    "danceability": 1.0,
    "energy": 1.5,
    "valence": 1.5,
    "acousticness": 0.75,
    "tempo": 1.0,
}
TOP_K = 5  # pick randomly among this many closest songs

# Friendly names for features (used in the chart and explanation).
FEATURE_LABELS = {
    "danceability": "Danceability",
    "energy": "Energy",
    "valence": "Positivity (valence)",
    "acousticness": "Acousticness",
    "tempo": "Tempo (BPM)",
}

# Keep in sync with HIGH_SCORE / LOW_SCORE in scripts/02_mood_profiles.py.
HIGH_SCORE = 7
LOW_SCORE = 3

# How the DJ repeats back each mood ("You said you're ...").
MOOD_PHRASES = {
    "Stressed": "feeling stressed",
    "Drained": "feeling drained",
    "Lonely": "feeling lonely",
    "Restless": "feeling restless",
    "Can't sleep": "having trouble sleeping",
    "Happy": "feeling happy",
    "Energetic": "feeling energetic",
}

# Only mention the Last.fm listener count if there are at least this many.
MIN_LASTFM_USERS_FOR_FACT = 50

# How each goal changed the target (used in the explanation text).
GOAL_EFFECTS = {
    "Calm down": "lowered the energy and tempo and added more acoustic sound",
    "Lift my mood": "raised the positivity (valence)",
    "Get energized": "raised the energy, tempo and danceability",
    "Keep the vibe": "kept the profile as it was",
}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def load_processed():
    """Load the three small CSVs made by the scripts. Returns three DataFrames."""
    files = {
        "song_pool": "song_pool.csv  (run scripts/01_build_song_pool.py)",
        "mood_profiles": "mood_profiles.csv  (run scripts/02_mood_profiles.py)",
        "culture_context": "culture_context.csv  (run scripts/03_culture_context.py)",
    }
    tables = []
    for name, hint in files.items():
        path = PROCESSED_DIR / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing processed/{hint}")
        tables.append(pd.read_csv(path))
    return tables


def get_target_profile(mood_profiles, mood, goal):
    """Return the one row of mood_profiles for this mood + goal, as a dict."""
    match = mood_profiles[(mood_profiles["mood"] == mood) & (mood_profiles["goal"] == goal)]
    if match.empty:
        raise ValueError(f"No profile for mood={mood!r}, goal={goal!r}. Rerun script 02.")
    return match.iloc[0].to_dict()


def get_culture_row(culture_context, world):
    """Return the culture_context row for a world as a dict (or {} if missing)."""
    match = culture_context[culture_context["world"] == world]
    return match.iloc[0].to_dict() if not match.empty else {}


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------
def rank_songs(song_pool, world, target):
    """
    Score every song in a world by how close it is to the target profile.

    1. Turn each feature into a z-score (how many standard deviations from the
       average song), so tempo (~120) and energy (~0.6) are on the same scale.
    2. Weighted Euclidean distance = sqrt( sum of weight * (song_z - target_z)^2 ).
    Returns the world's songs sorted from closest to farthest.
    """
    # Use the whole pool for the averages so every world is on the same scale.
    means = song_pool[FEATURES].mean()
    stds = song_pool[FEATURES].std()

    songs = song_pool[song_pool["world"] == world].copy()
    song_z = (songs[FEATURES] - means) / stds
    target_z = (pd.Series({f: target[f] for f in FEATURES}) - means) / stds

    squared = (song_z - target_z) ** 2
    weighted = sum(FEATURE_WEIGHTS[f] * squared[f] for f in FEATURES)
    songs["distance"] = weighted ** 0.5
    return songs.sort_values("distance")


def pick_song(ranked, avoid_track_id=None, rng=random):
    """Pick one song at random from the TOP_K closest (optionally skipping one)."""
    candidates = ranked
    if avoid_track_id is not None and len(ranked) > 1:
        candidates = ranked[ranked["track_id"] != avoid_track_id]
    top = candidates.head(TOP_K)
    return top.iloc[rng.randrange(len(top))].to_dict()


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------
def _is_missing(value):
    return value is None or (isinstance(value, float) and math.isnan(value))


def culture_fact(context, rng=random):
    """One neutral, data-backed fact about the world's representative country."""
    if not context:
        return ""
    country = context["country_name"]
    stand_in = (f"{country} (our stand-in for {context['world']})"
                if country != context["world"] else country)
    facts = []
    if not _is_missing(context.get("social_support")):
        facts.append(
            f"in the World Happiness Report data ({int(context['whr_year'])}), "
            f"{context['social_support']:.0%} of people surveyed in {stand_in} said they "
            f"have someone to count on in times of trouble")
    if not _is_missing(context.get("positive_affect")):
        facts.append(
            f"in the World Happiness Report data, {stand_in} scored "
            f"{context['positive_affect']:.2f} out of 1 on positive affect "
            f"(how often people reported laughing and enjoying their day)")
    if not _is_missing(context.get("indulgence")):
        facts.append(
            f"{stand_in} scores {context['indulgence']:.0f}/100 on Hofstede's indulgence "
            f"dimension, which measures how freely a society values enjoying life and having fun")
    if not _is_missing(context.get("lastfm_users")) and context["lastfm_users"] >= MIN_LASTFM_USERS_FOR_FACT:
        facts.append(
            f"the Last.fm culture dataset we used includes "
            f"{int(context['lastfm_users']):,} listeners from {country}")
    return rng.choice(facts) if facts else ""


def make_dj_intro(mood, goal, world, song, context, rng=random):
    """
    ===================== SWAP POINT FOR AN LLM =====================
    Returns the DJ's short spoken intro. Right now it's a template string.
    To use an LLM later, build a prompt from these same inputs and return
    the model's reply instead. Keep the rule: describe the music, never
    diagnose or make claims about the listener's mental health.
    =================================================================
    """
    goal_phrases = {
        "Calm down": "something to help you slow down",
        "Lift my mood": "something to lift you up",
        "Get energized": "something with a spark",
        "Keep the vibe": "something that keeps the vibe going",
    }
    fact = culture_fact(context, rng)
    fact_line = f" Fun fact: {fact}." if fact else ""
    return (
        f"Hey, it's your Culture DJ! You said you're {MOOD_PHRASES.get(mood, mood.lower())} and want "
        f"{goal_phrases.get(goal, 'something good')}, so we're heading to {world}.{fact_line} "
        f"Here's \"{song['track_name']}\" by {song['artists'].replace(';', ', ')}. Let's dance!"
    )


def explain_match(target, song, mood, goal, world, n_world_songs):
    """Return 3 plain-language sentences explaining why this song was picked."""
    # Sentence 1: who in the survey this is based on.
    if target["signal"] == "low_all":
        who = (f"rated anxiety, depression, insomnia and OCD all {LOW_SCORE} or lower "
               f"out of 10")
    else:
        who = f"rated their {target['signal'].lower()} {HIGH_SCORE} or higher out of 10"
    bpm = "" if _is_missing(target.get("median_bpm")) else (
        f", and reported a median favorite tempo of {target['median_bpm']:.0f} BPM")
    s1 = (f"For \"{mood}\", we looked at the {int(target['n_respondents'])} people in the "
          f"Music & Mental Health (MxMH) survey who {who} and said music improves how they "
          f"feel. Compared with the average respondent, they listened more to "
          f"{target['top_genres']}{bpm}.")

    # Sentence 2: how that became a target sound.
    s2 = (f"We translated that listening mix into a target sound using genre averages "
          f"from the Spotify Tracks Dataset, then your goal \"{goal}\" "
          f"{GOAL_EFFECTS.get(goal, 'adjusted it')}.")

    # Sentence 3: why this particular song.
    gaps = {f: abs(song[f] - target[f]) / (200 if f == "tempo" else 1) for f in FEATURES}
    closest = min(gaps, key=gaps.get)
    s3 = (f"Out of {n_world_songs} {world} songs, \"{song['track_name']}\" was one of the "
          f"{TOP_K} closest matches; its {FEATURE_LABELS[closest].lower()} was especially "
          f"close to the target ({_fmt(closest, song[closest])} vs "
          f"{_fmt(closest, target[closest])}).")
    return [s1, s2, s3]


def _fmt(feature, value):
    return f"{value:.0f} BPM" if feature == "tempo" else f"{value:.2f}"


# ---------------------------------------------------------------------------
# Quick self-test: python dj_logic.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    song_pool, mood_profiles, culture_context = load_processed()
    print(f"Loaded {len(song_pool)} songs, {len(mood_profiles)} profiles, "
          f"{len(culture_context)} culture rows")

    for mood, goal, world in [("Stressed", "Calm down", "India"),
                              ("Happy", "Get energized", "West Africa"),
                              ("Can't sleep", "Calm down", "South Korea")]:
        target = get_target_profile(mood_profiles, mood, goal)
        ranked = rank_songs(song_pool, world, target)
        song = pick_song(ranked)
        print(f"\n=== {mood} / {goal} / {world}")
        print(ranked.head(TOP_K)[["track_name", "artists", "distance"] + FEATURES]
              .round(2).to_string(index=False))
        print("\nDJ:", make_dj_intro(mood, goal, world, song, get_culture_row(culture_context, world)))
        for sentence in explain_match(target, song, mood, goal, world, len(ranked)):
            print(" -", sentence)
