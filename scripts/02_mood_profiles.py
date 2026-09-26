"""
Step 02: Turn the MxMH survey into a "target sound" for every mood + goal.

The idea, in plain words:
  1. Pick survey respondents whose self-reported scores match a mood
     (for example, "Stressed" -> people who rated their Anxiety 7 or higher)
     AND who said music improves how they feel.
  2. Look at which genres that group listens to most.
  3. Use the Spotify Tracks Dataset to find what those genres typically
     sound like (danceability, energy, valence, acousticness).
  4. Nudge the result based on the user's goal (e.g. "Calm down" = less energy).

IMPORTANT: this describes population-level patterns in how survey respondents
say music helps them. It does NOT diagnose or predict anyone's mental health.

Output: processed/mood_profiles.csv (one row per mood + goal combination)

Run from the project folder:
    python scripts/02_mood_profiles.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# EDIT ME: which MxMH score each app mood is linked to.
# "low_all" means: low scores on all four (used for the positive moods).
# ---------------------------------------------------------------------------
MOOD_TO_SIGNAL = {
    "Stressed": "Anxiety",
    "Restless": "Anxiety",
    "Drained": "Depression",
    "Lonely": "Depression",
    "Can't sleep": "Insomnia",
    "Happy": "low_all",
    "Energetic": "low_all",
}

HIGH_SCORE = 7   # "high on a signal" means a score of 7 or more (out of 10)
LOW_SCORE = 3    # "low on everything" means all four scores are 3 or less
SIGNAL_COLUMNS = ["Anxiety", "Depression", "Insomnia", "OCD"]

# How we turn the frequency answers into numbers.
FREQUENCY_POINTS = {"Never": 0, "Rarely": 1, "Sometimes": 2, "Very frequently": 3}

# Reported BPM values outside this range are treated as typos / outliers.
BPM_MIN, BPM_MAX = 40, 220

# ---------------------------------------------------------------------------
# EDIT ME: MxMH genre name -> Spotify track_genre values that represent it.
# (Spotify has no "Rap" or "Lofi" genre, so we use the closest ones.)
# ---------------------------------------------------------------------------
MXMH_TO_SPOTIFY = {
    "Classical": ["classical"],
    "Country": ["country"],
    "EDM": ["edm"],
    "Folk": ["folk"],
    "Gospel": ["gospel"],
    "Hip hop": ["hip-hop"],
    "Jazz": ["jazz"],
    "K pop": ["k-pop"],
    "Latin": ["latin"],
    "Lofi": ["chill", "study"],
    "Metal": ["metal"],
    "Pop": ["pop"],
    "R&B": ["r-n-b"],
    "Rap": ["hip-hop"],
    "Rock": ["rock"],
    "Video game music": ["ambient", "electronic"],
}

# The audio features that make up a "profile".
PROFILE_FEATURES = ["danceability", "energy", "valence", "acousticness", "tempo"]

# ---------------------------------------------------------------------------
# EDIT ME: how each goal nudges the profile.
# Numbers for danceability/energy/valence/acousticness are on a 0-1 scale.
# tempo is in beats per minute.
# ---------------------------------------------------------------------------
GOAL_ADJUSTMENTS = {
    "Calm down":     {"danceability": -0.05, "energy": -0.20, "valence": 0.00, "acousticness": +0.15, "tempo": -15},
    "Lift my mood":  {"danceability": +0.05, "energy": +0.05, "valence": +0.20, "acousticness": 0.00, "tempo": +5},
    "Get energized": {"danceability": +0.10, "energy": +0.20, "valence": +0.05, "acousticness": -0.10, "tempo": +15},
    "Keep the vibe": {"danceability": 0.00, "energy": 0.00, "valence": 0.00, "acousticness": 0.00, "tempo": 0},
}

# Almost everyone in the survey listens to lots of Rock and Pop, so a plain
# average makes every mood sound the same. Instead we measure how a mood group
# DIFFERS from the average respondent and multiply that difference by CONTRAST.
#   CONTRAST = 1  -> the plain average (moods look almost identical)
#   CONTRAST = 4  -> the group's differences are 4x more visible
CONTRAST = 4

# Warn if a mood group has fewer respondents than this.
MIN_RESPONDENTS = 30

PROJECT_DIR = Path(__file__).resolve().parent.parent
SURVEY_FILE = PROJECT_DIR / "data" / "mxmh_survey_results.csv"
SPOTIFY_FILE = PROJECT_DIR / "data" / "spotify_tracks.csv"
OUTPUT_FILE = PROJECT_DIR / "processed" / "mood_profiles.csv"


def select_respondents(survey, signal):
    """Return the survey rows that match a signal AND said music helps."""
    helped = survey["Music effects"] == "Improve"
    if signal == "low_all":
        matches = (survey[SIGNAL_COLUMNS] <= LOW_SCORE).all(axis=1)
    else:
        matches = survey[signal] >= HIGH_SCORE
    return survey[helped & matches]


def genre_mix(group):
    """Average listening frequency (0-3) of each MxMH genre within a group."""
    mix = {}
    for genre in MXMH_TO_SPOTIFY:
        answers = group[f"Frequency [{genre}]"].map(FREQUENCY_POINTS)
        mix[genre] = answers.mean()
    return pd.Series(mix)


def main():
    # --- 1. Load ----------------------------------------------------------
    survey = pd.read_csv(SURVEY_FILE)
    spotify = pd.read_csv(SPOTIFY_FILE)
    print(f"Survey: {len(survey):,} respondents | Spotify: {len(spotify):,} tracks")

    # Check that every genre column we expect is really there.
    for genre in MXMH_TO_SPOTIFY:
        column = f"Frequency [{genre}]"
        if column not in survey.columns:
            raise KeyError(f"Missing survey column: {column}")

    # Clean BPM: turn outliers into missing values.
    survey["BPM_clean"] = survey["BPM"].where(survey["BPM"].between(BPM_MIN, BPM_MAX))
    print(f"BPM: {survey['BPM'].notna().sum()} answers, "
          f"{survey['BPM_clean'].notna().sum()} kept after removing outliers")

    # --- 2. What does each MxMH genre sound like? (from Spotify) ----------
    genre_sound = {}
    for mxmh_genre, spotify_genres in MXMH_TO_SPOTIFY.items():
        rows = spotify[spotify["track_genre"].isin(spotify_genres)]
        if rows.empty:
            print(f"  WARNING: no Spotify tracks for {mxmh_genre} -> {spotify_genres}")
            continue
        genre_sound[mxmh_genre] = rows[PROFILE_FEATURES].mean()
    genre_sound = pd.DataFrame(genre_sound).T  # rows = MxMH genre, columns = features

    print("\nCHECK: average Spotify sound of each MxMH genre")
    print(genre_sound.round(2).to_string())

    # --- 3. Build a base profile for each mood ----------------------------
    def sound_of(mix):
        """Weighted average of the genre sounds, using a genre mix as weights."""
        weights = mix / mix.sum()  # turn into shares that add up to 1
        return genre_sound.mul(weights, axis=0).sum()

    # The "average respondent" (everyone who answered the survey).
    everyone_mix = genre_mix(survey).loc[genre_sound.index]
    everyone_sound = sound_of(everyone_mix)
    print("\nCHECK: sound of the average respondent")
    print(everyone_sound.round(2).to_string())

    base_profiles = []
    for mood, signal in MOOD_TO_SIGNAL.items():
        group = select_respondents(survey, signal)
        if len(group) < MIN_RESPONDENTS:
            print(f"  WARNING: only {len(group)} respondents for {mood} - results may be noisy")

        mix = genre_mix(group).loc[genre_sound.index]
        group_sound = sound_of(mix)

        # Start from the average respondent, then add the group's difference x CONTRAST.
        profile = everyone_sound + CONTRAST * (group_sound - everyone_sound)

        # Use the group's own reported BPM for tempo (it's the most direct data).
        median_bpm = group["BPM_clean"].median()
        genre_tempo = profile["tempo"]
        if pd.notna(median_bpm):
            profile["tempo"] = median_bpm

        # "Lift" = how much more this group listens to a genre than average.
        lift = mix / everyone_mix
        distinctive = lift.sort_values(ascending=False).head(3).index.tolist()
        base_profiles.append({
            "mood": mood,
            "signal": signal,
            "n_respondents": len(group),
            "median_bpm": median_bpm,
            "genre_based_tempo": round(genre_tempo, 1),
            "top_genres": ", ".join(distinctive),
            **profile.to_dict(),
        })

    base = pd.DataFrame(base_profiles)
    print("\nCHECK: base profile per mood (before goal adjustment)")
    print(base.round(2).to_string(index=False))

    # --- 4. Apply each goal -----------------------------------------------
    rows = []
    for _, mood_row in base.iterrows():
        for goal, nudges in GOAL_ADJUSTMENTS.items():
            row = mood_row.to_dict()
            row["goal"] = goal
            for feature, change in nudges.items():
                row[feature] = row[feature] + change
            # Keep values inside realistic ranges.
            for feature in ["danceability", "energy", "valence", "acousticness"]:
                row[feature] = min(max(row[feature], 0.0), 1.0)
            row["tempo"] = min(max(row["tempo"], 60), 200)
            rows.append(row)

    profiles = pd.DataFrame(rows)
    column_order = ["mood", "goal", "signal", "n_respondents", "median_bpm",
                    "genre_based_tempo", "top_genres"] + PROFILE_FEATURES
    profiles = profiles[column_order].round(3)

    # --- 5. Save + print summary ------------------------------------------
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    profiles.to_csv(OUTPUT_FILE, index=False)

    print(f"\nCHECK: {len(profiles)} rows (expected {len(MOOD_TO_SIGNAL) * len(GOAL_ADJUSTMENTS)})")
    print(profiles[["mood", "goal", "n_respondents"] + PROFILE_FEATURES].round(2).to_string(index=False))
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
