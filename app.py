"""
Culture DJ - Streamlit app.

Screens (stored in st.session_state["screen"]):
    "mood"    -> pick a mood and a goal
    "culture" -> pick a musical world
    "dj"      -> DJ intro, song card, animated dancer
    "why"     -> chart + plain-language explanation

Run with:  streamlit run app.py
(Run scripts 01, 02 and 03 first so the processed/ files exist.)
"""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import dj_logic as dj
from dancer import build_dancer_html

st.set_page_config(page_title="Culture DJ", page_icon="🎧", layout="wide")

# Load our CSS theme (assets/style.css) into the page.
CSS = (Path(__file__).parent / "assets" / "style.css").read_text(encoding="utf-8")
st.html(f"<style>{CSS}</style>")

# Chart colors (validated colorblind-safe pair for dark backgrounds).
TARGET_COLOR = "#3987e5"
SONG_COLOR = "#d95926"


# ---------------------------------------------------------------------------
# Data (cached, so it only loads once)
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    return dj.load_processed()


try:
    song_pool, mood_profiles, culture_context = load_data()
except FileNotFoundError as error:
    st.error(f"{error}. See README.md for the run order.")
    st.stop()


# ---------------------------------------------------------------------------
# Session state + navigation helpers
# ---------------------------------------------------------------------------
st.session_state.setdefault("screen", "mood")


def go_to(screen):
    st.session_state["screen"] = screen


def choose_world(world):
    """Called when a world card is clicked: find the target, rank songs, pick one."""
    mood = st.session_state["mood"]
    goal = st.session_state["goal"]
    target = dj.get_target_profile(mood_profiles, mood, goal)
    ranked = dj.rank_songs(song_pool, world, target)
    st.session_state.update(world=world, target=target, ranked=ranked)
    spin_song()
    go_to("dj")


def spin_song():
    """Pick a (new) song from the closest matches and write a fresh DJ intro."""
    current = st.session_state.get("song")
    avoid = current["track_id"] if current else None
    song = dj.pick_song(st.session_state["ranked"], avoid_track_id=avoid)
    context = dj.get_culture_row(culture_context, st.session_state["world"])
    intro = dj.make_dj_intro(st.session_state["mood"], st.session_state["goal"],
                             st.session_state["world"], song, context)
    st.session_state.update(song=song, intro=intro)


def start_over():
    for key in ["mood_pick", "goal_pick", "world", "target", "ranked", "song", "intro"]:
        st.session_state.pop(key, None)
    go_to("mood")


def header(step_text):
    with st.container(key="hero"):
        st.title("Culture DJ")
        st.write("Tell us how you feel, pick a musical world, and let the DJ spin.")
    with st.container(key="step"):
        st.write(step_text)


def slug(text):
    return text.lower().replace(" ", "-")


# ---------------------------------------------------------------------------
# Player placeholder
# ---------------------------------------------------------------------------
def render_player(track_id):
    """
    ===================== SWAP POINT FOR AUDIO =====================
    Song playback is not built yet. When you're ready, replace this with e.g.
        st.iframe(f"https://open.spotify.com/embed/track/{track_id}", height=152)
    ================================================================
    """
    st.caption("🔇 Audio preview coming soon. The dancer is already moving to this song's tempo.")


# ---------------------------------------------------------------------------
# Screen 1: mood + goal
# ---------------------------------------------------------------------------
def mood_screen():
    header("Step 1 of 4 · Your mood")
    with st.container(key="panel-mood"):
        mood = st.pills("How are you feeling right now?", dj.MOODS, key="mood_pick")
        goal = st.pills("What do you want the music to do?", dj.GOALS, key="goal_pick")
        st.write("")
        if st.button("Choose a musical world →", type="primary", disabled=not (mood and goal)):
            st.session_state.update(mood=mood, goal=goal)
            go_to("culture")
            st.rerun()


# ---------------------------------------------------------------------------
# Screen 2: culture
# ---------------------------------------------------------------------------
def culture_screen():
    header("Step 2 of 4 · Pick a musical world")
    st.write(f"You're **{st.session_state['mood'].lower()}** and want to "
             f"**{st.session_state['goal'].lower()}**. Where should the DJ take you?")

    columns = st.columns(len(dj.WORLDS))
    for column, (world, info) in zip(columns, dj.WORLDS.items()):
        with column, st.container(key=f"world-{slug(world)}"):
            st.subheader(world)
            st.write(f"{info['subtitle']}  \n*{info['dance']} moves*")
            st.button("Go", key=f"go-{slug(world)}", on_click=choose_world, args=(world,))

    st.write("")
    st.button("← Change mood", on_click=go_to, args=("mood",))


# ---------------------------------------------------------------------------
# Screen 3: DJ + dancer
# ---------------------------------------------------------------------------
def dj_screen():
    song = st.session_state["song"]
    world = st.session_state["world"]
    header(f"Step 3 of 4 · Now spinning in {world}")

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.iframe(build_dancer_html(world, song["tempo"]), height=410)

    with right:
        with st.container(key="panel-dj"):
            st.markdown("**🎧 DJ says**")
            st.write(st.session_state["intro"])

        with st.container(key="panel-song"):
            st.subheader(song["track_name"])
            st.write(f"{song['artists'].replace(';', ', ')} · *{song['album_name']}*")
            a, b = st.columns(2)
            a.metric("Tempo", f"{song['tempo']:.0f} BPM")
            b.metric("Energy", f"{song['energy']:.2f}")
            render_player(song["track_id"])

    st.write("")
    c1, c2, c3 = st.columns(3)
    c1.button("Why this song? →", type="primary", on_click=go_to, args=("why",),
              width="stretch")
    c2.button("🔀 Spin another", on_click=spin_song, width="stretch")
    c3.button("↺ Start over", on_click=start_over, width="stretch")


# ---------------------------------------------------------------------------
# Screen 4: explanation
# ---------------------------------------------------------------------------
def feature_chart(target, song):
    """Grouped bar chart: target profile vs chosen song (features on a 0-1 scale)."""
    rows = []
    for feature in ["danceability", "energy", "valence", "acousticness"]:
        rows.append({"Feature": dj.FEATURE_LABELS[feature], "Profile": "Target", "Value": target[feature]})
        rows.append({"Feature": dj.FEATURE_LABELS[feature], "Profile": "This song", "Value": song[feature]})
    data = pd.DataFrame(rows)

    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=4, size=22)
        .encode(
            y=alt.Y("Feature:N", title=None, sort=None),
            yOffset=alt.YOffset("Profile:N", sort=["Target", "This song"]),
            x=alt.X("Value:Q", scale=alt.Scale(domain=[0, 1]), title="Score (0 to 1)",
                    axis=alt.Axis(grid=True, gridOpacity=0.15, tickCount=5)),
            color=alt.Color("Profile:N",
                            scale=alt.Scale(domain=["Target", "This song"],
                                            range=[TARGET_COLOR, SONG_COLOR]),
                            legend=alt.Legend(orient="top", title=None)),
            tooltip=["Feature", "Profile", alt.Tooltip("Value:Q", format=".2f")],
        )
        .properties(height=300, background="transparent")
        .configure_view(stroke=None)
        .configure_axis(labelColor="#c3c2b7", titleColor="#c3c2b7", domainColor="#3a3552",
                        labelFontSize=13)
        .configure_legend(labelColor="#f4f2ff", labelFontSize=13)
    )
    return chart, data


def why_screen():
    song = st.session_state["song"]
    target = st.session_state["target"]
    world = st.session_state["world"]
    mood, goal = st.session_state["mood"], st.session_state["goal"]
    header("Step 4 of 4 · Why this song?")

    left, right = st.columns([3, 2], gap="large")
    with left:
        with st.container(key="panel-chart"):
            st.markdown(f"**Target sound vs \"{song['track_name']}\"**")
            chart, data = feature_chart(target, song)
            st.altair_chart(chart, width="stretch")
            a, b = st.columns(2)
            a.metric("Target tempo", f"{target['tempo']:.0f} BPM")
            b.metric("Song tempo", f"{song['tempo']:.0f} BPM",
                     delta=f"{song['tempo'] - target['tempo']:+.0f} BPM", delta_color="off")
            with st.expander("See the numbers as a table"):
                st.dataframe(data.pivot(index="Feature", columns="Profile", values="Value").round(2))

    with right:
        with st.container(key="panel-why"):
            st.markdown("**How the DJ chose**")
            sentences = dj.explain_match(target, song, mood, goal, world,
                                         int((song_pool["world"] == world).sum()))
            st.markdown("\n".join(f"- {s}" for s in sentences))

    with st.container(key="disclaimer"):
        st.write(
            "Data: Music & Mental Health survey (Kaggle MxMH), Spotify Tracks Dataset, and the "
            "Culture-Aware Music Recommendation Dataset (Zenodo: Last.fm users, Hofstede "
            "dimensions, World Happiness Report 2018). These describe population-level patterns "
            "in how survey respondents say music helps them. Culture DJ does not diagnose, "
            "assess or predict anyone's mental health."
        )

    c1, c2 = st.columns(2)
    c1.button("← Back to the DJ", on_click=go_to, args=("dj",), width="stretch")
    c2.button("↺ Start over", on_click=start_over, width="stretch")


# ---------------------------------------------------------------------------
# Router: show the screen stored in session_state
# ---------------------------------------------------------------------------
SCREENS = {"mood": mood_screen, "culture": culture_screen, "dj": dj_screen, "why": why_screen}

# If the page reloads mid-flow and state is missing, fall back to the start.
if st.session_state["screen"] in ("dj", "why") and "song" not in st.session_state:
    go_to("mood")

SCREENS[st.session_state["screen"]]()
