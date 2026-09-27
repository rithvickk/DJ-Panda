# DJ Panda

An AI music companion for mental well-being and global awareness. DJ Panda asks
how you're feeling, how strong it is and what you want the music to do. It then
builds a target sound from Music & Mental Health survey respondents who felt the
same way and said music helps them, ranks five world cultures by how close they
sound, and plays a matching song with a "Why this song?" explanation.

> Not medical advice. DJ Panda describes population-level patterns in how survey
> respondents say music helps them. It does not diagnose, assess or predict
> anyone's mental health.

## Run the app

Needs Node 20+.

```powershell
cd web
npm install
npm run dev        # http://localhost:5173
npm run build      # static site in web/dist/ (deploy to Vercel, Netlify or GitHub Pages)
```

## Rebuild the data (only if the data or scripts change)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python scripts/01_build_song_pool.py     # -> processed/song_pool.csv
python scripts/02_mood_profiles.py       # -> processed/mood_profiles.csv
python scripts/03_culture_context.py     # -> processed/culture_context.csv
python scripts/04_export_web_data.py     # -> web/src/data/*.json (what the app reads)
```

Every script prints `CHECK:` tables. Read them after each run.

## Data (in `data/`)

| File | Source |
|---|---|
| `mxmh_survey_results.csv` | Kaggle: Music & Mental Health survey |
| `spotify_tracks.csv` | Spotify Tracks Dataset ([Hugging Face copy](https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/main/dataset.csv), renamed) |
| `users.tsv`, `hofstede.tsv`, `world_happiness_report_2018.tsv` | Zenodo: Culture-Aware Music Recommendation Dataset |

## Layout

```
data/                  raw datasets
scripts/01..04         data prep -> processed/ -> web/src/data/
processed/             small CSVs made by the scripts
web/src/App.jsx        the flow: intro -> 3 questions -> DJ's read -> results -> song -> why
web/src/lib/dj.js      questions, matching and explanations
web/src/components/    DjPanda, Question, Results, MoodMap, WorldMap, NowPlaying, WhySong
web/src/data/          JSON exported by script 04
```

## How it works

1. **Song pool (01):** Spotify genres are mapped to five worlds (India, South
   Korea, Latin America, Europe, West Africa). West Africa uses a list of West
   African artists because the dataset's `afrobeat` genre is mostly Brazilian
   funk. Duplicates and explicit tracks are dropped, and each world keeps its 5
   most popular songs.
2. **Mood profiles (02):** each mood maps to an MxMH score, and "how strong is
   it?" picks a band of that 0-10 score (Stressed + "Quite a bit" = Anxiety 7-8).
   From respondents in that band who said music improves how they feel, we take
   the genres they play more than average, turn them into a sound using Spotify
   genre averages, and use their median favorite BPM. The goal then nudges the
   result (84 profiles: 7 moods x 3 strengths x 4 goals).
3. **Culture context (03):** one stand-in country per world, with Last.fm
   listener counts, Hofstede dimensions and World Happiness Report scores.
4. **Matching (dj.js):** features become z-scores, and a weighted distance ranks
   the worlds (by their average song) and the songs. The DJ picks randomly
   between a world's 2 closest songs.

Playback uses Spotify's embed player (a 30-second preview unless you're logged
in to Spotify).
