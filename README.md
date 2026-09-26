# Culture DJ

Tell the app how you're feeling, pick a musical world, and a virtual DJ picks a
song from that culture that fits your mood while an animated dancer moves to its
tempo. A "Why this song?" screen explains the data behind the pick.

> Culture DJ describes population-level patterns in how survey respondents say
> music helps them. It does not diagnose, assess or predict anyone's mental health.

## Setup

```powershell
# Create the environment (skip if .venv already exists)
uv venv
uv pip install -r requirements.txt

# Or with plain pip
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Data (put these in `data/`)

| File | Source | In git? |
|---|---|---|
| `mxmh_survey_results.csv` | Kaggle: Music & Mental Health survey | yes |
| `spotify_tracks.csv` | maharshipandya Spotify Tracks Dataset ([Hugging Face copy](https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/main/dataset.csv), renamed) | yes |
| `users.tsv`, `hofstede.tsv`, `world_happiness_report_2018.tsv` | Zenodo Culture-Aware Music Recommendation Dataset | yes |
| `acoustic_features_lfm_id.tsv`, `events.tsv` | Zenodo (same dataset) | **no** (too big, only needed for step 03b) |

## Run order

```powershell
.venv\Scripts\activate
python scripts/01_build_song_pool.py     # -> processed/song_pool.csv
python scripts/02_mood_profiles.py       # -> processed/mood_profiles.csv
python scripts/03_culture_context.py     # -> processed/culture_context.csv
streamlit run app.py
```

Optional stretch (needs `events.tsv`, about 351 million rows, streamed with polars):

```powershell
python scripts/03b_country_listening.py  # -> processed/country_listening.csv
```

Every script prints `CHECK:` tables. Read them after each run. Two quick tests
that need no Streamlit:

```powershell
python dj_logic.py   # prints the top 5 matches, the DJ intro and the explanation for 3 examples
python dancer.py     # writes dancer_preview.html; open it to watch all 5 dance styles
```

## Layout

```
app.py                     Streamlit screens (mood -> culture -> DJ -> why)
dj_logic.py                matching, DJ intro (LLM swap point), explanations
dancer.py                  builds the dancer (palette + tempo -> CSS variables)
assets/style.css           app theme
assets/dancer.css          all dancer animation (one move set per world)
.streamlit/config.toml     dark base theme
scripts/01..03b            offline data prep -> processed/
processed/                 small CSVs the app reads (commit these for deployment)
data/                      raw datasets
notebooks/                 exploratory notebooks
```

## How it works

1. **Song pool (01):** Spotify `track_genre` values are mapped to five worlds.
   The dataset's `afrobeat` genre is mostly Brazilian and Latin funk, so West
   Africa is built from an editable list of West African artists instead, and a
   few mislabeled artists are removed from K-pop. Duplicates and explicit tracks
   are dropped; the top 300 per world by popularity are kept (West Africa has 229).
2. **Mood profiles (02):** each mood maps to an MxMH score (for example Stressed
   maps to Anxiety of 7 or more). For respondents who said music improves how
   they feel, we compare their genre listening mix to the average respondent's,
   turn it into audio features using Spotify genre averages, and use their median
   reported BPM for tempo. Then the goal nudges the profile.
3. **Culture context (03):** one representative country per world, with Last.fm
   listener counts, Hofstede dimensions and World Happiness Report scores. South
   Korea and Nigeria have no Hofstede row, so those values stay blank.
4. **Matching (app):** features are converted to z-scores and the app computes a
   weighted Euclidean distance to the target. It then picks randomly among the 5 closest songs.

Song playback is not built yet. See `render_player()` in `app.py`.
