/*
 * The "brain" of DJ Panda: the questions, song matching and the DJ's words.
 *
 * Data comes from the Python pipeline (scripts/01-04) as JSON in src/data/.
 * Mood, intensity and goal ids must match scripts/02_mood_profiles.py, and
 * world names must match scripts/01_build_song_pool.py.
 */
import songs from '../data/songs.json'
import profiles from '../data/profiles.json'
import culture from '../data/culture.json'

export { songs }

// ---------------------------------------------------------------------------
// Question 1: how are you feeling?
// ---------------------------------------------------------------------------
export const MOODS = [
  { id: 'Stressed', emoji: '😣', phrase: 'feeling stressed', adjective: 'stressed' },
  { id: 'Drained', emoji: '🪫', phrase: 'feeling drained', adjective: 'drained' },
  { id: 'Lonely', emoji: '🌧️', phrase: 'feeling lonely', adjective: 'lonely' },
  { id: 'Restless', emoji: '🌀', phrase: 'feeling restless', adjective: 'restless' },
  { id: "Can't sleep", emoji: '🌙', phrase: 'having trouble sleeping', adjective: 'wired' },
  { id: 'Happy', emoji: '😄', phrase: 'feeling happy', adjective: 'happy', positive: true },
  { id: 'Energetic', emoji: '⚡', phrase: 'feeling energetic', adjective: 'energetic', positive: true },
]

// ---------------------------------------------------------------------------
// Question 2: how strong is it? Each answer is a band of the MxMH survey's own
// 0-10 scores (see SIGNAL_BANDS / LOW_ALL_MAX in scripts/02_mood_profiles.py).
// ---------------------------------------------------------------------------
const INTENSITY_OPTIONS = {
  negative: [
    { id: 'mild', label: 'A little', hint: 'like a 4-6 out of 10' },
    { id: 'strong', label: 'Quite a bit', hint: 'like a 7-8 out of 10' },
    { id: 'intense', label: 'A lot', hint: 'like a 9-10 out of 10' },
  ],
  positive: [
    { id: 'mild', label: 'Pretty good', hint: 'a few worries in the mix' },
    { id: 'strong', label: 'Really good', hint: 'hardly any worries' },
    { id: 'intense', label: 'On top of the world', hint: 'no worries at all' },
  ],
}

export function intensityOptions(mood) {
  return getMood(mood)?.positive ? INTENSITY_OPTIONS.positive : INTENSITY_OPTIONS.negative
}

// ---------------------------------------------------------------------------
// Question 3: what should the music do?
// ---------------------------------------------------------------------------
export const GOALS = [
  { id: 'Calm down', emoji: '🫧', ask: 'something to help you slow down',
    effect: 'lowered the energy and tempo and added more acoustic sound' },
  { id: 'Lift my mood', emoji: '🌈', ask: 'something to lift you up',
    effect: 'raised the positivity (valence)' },
  { id: 'Get energized', emoji: '🔥', ask: 'something with a spark',
    effect: 'raised the energy, tempo and danceability' },
  { id: 'Keep the vibe', emoji: '🎶', ask: 'something that keeps the vibe going',
    effect: 'kept the profile as it was' },
]

// ---------------------------------------------------------------------------
// Musical worlds + where they sit on the map (ISO 3166 numeric country ids,
// as used by the world-atlas package).
// ---------------------------------------------------------------------------
export const WORLDS = {
  India: {
    subtitle: 'Bollywood',
    color: '#e8890c', pin: [78.9, 22.5],
    countries: ['356'],
  },
  'South Korea': {
    subtitle: 'K-pop',
    color: '#c04fd6', pin: [127.8, 36.4],
    countries: ['410'],
  },
  'Latin America': {
    subtitle: 'Latin & reggaeton',
    color: '#e5484d', pin: [-60, -12],
    countries: ['484', '320', '084', '340', '222', '558', '188', '591', '192', '214', '332',
      '630', '388', '780', '170', '862', '218', '604', '068', '076', '600', '858', '032',
      '152', '328', '740'],
  },
  Europe: {
    subtitle: 'British, French & German',
    color: '#4d7cfe', pin: [8, 50],
    countries: ['826', '372', '250', '276', '380', '724', '620', '528', '056', '442', '756',
      '040', '208', '578', '752', '246', '352', '616', '203', '703', '348', '705', '191',
      '070', '688', '499', '008', '807', '300', '100', '642', '498', '804', '112', '440',
      '428', '233'],
    extraNames: ['Kosovo'],
  },
  'West Africa': {
    subtitle: 'Afrobeats',
    color: '#0aa37f', pin: [-2, 11],
    countries: ['566', '288', '686', '384', '466', '854', '324', '694', '430', '768', '204',
      '562', '270', '624', '478'],
  },
}

// ---------------------------------------------------------------------------
// EDIT ME: matching settings. A bigger weight = that feature matters more.
// ---------------------------------------------------------------------------
const FEATURES = ['danceability', 'energy', 'valence', 'acousticness', 'tempo']
const FEATURE_WEIGHTS = { danceability: 1.0, energy: 1.5, valence: 1.5, acousticness: 0.75, tempo: 1.0 }
const TOP_K = 2 // pick randomly among this many closest songs (each world only has 5)

export const FEATURE_LABELS = {
  danceability: 'Danceability',
  energy: 'Energy',
  valence: 'Positivity (valence)',
  acousticness: 'Acousticness',
  tempo: 'Tempo (BPM)',
}

// Only mention the Last.fm listener count if there are at least this many.
const MIN_LASTFM_USERS_FOR_FACT = 50

// ---------------------------------------------------------------------------
// Lookups
// ---------------------------------------------------------------------------
export const getMood = (id) => MOODS.find((m) => m.id === id)
const getGoal = (id) => GOALS.find((g) => g.id === id)
const getCulture = (world) => culture.find((c) => c.world === world) ?? null
export const worldSongCount = (world) => songs.filter((s) => s.world === world).length

export function getTarget(mood, intensity, goal) {
  const row = profiles.find((p) => p.mood === mood && p.intensity === intensity && p.goal === goal)
  if (!row) throw new Error(`No profile for ${mood} / ${intensity} / ${goal}. Rerun scripts 02 and 04.`)
  return row
}

// ---------------------------------------------------------------------------
// Matching
// ---------------------------------------------------------------------------
// Mean and (sample) standard deviation of each feature over the whole pool,
// so every world is scored on the same scale.
const STATS = Object.fromEntries(FEATURES.map((f) => {
  const values = songs.map((s) => s[f])
  const mean = values.reduce((a, b) => a + b, 0) / values.length
  const variance = values.reduce((a, v) => a + (v - mean) ** 2, 0) / (values.length - 1)
  return [f, { mean, std: Math.sqrt(variance) }]
}))

const z = (feature, value) => (value - STATS[feature].mean) / STATS[feature].std

/**
 * Score every song in a world by weighted Euclidean distance between z-scores
 * (so tempo ~120 and energy ~0.6 count on the same scale). Closest first.
 */
export function rankSongs(world, target) {
  return songs
    .filter((s) => s.world === world)
    .map((s) => {
      const squared = FEATURES.reduce(
        (sum, f) => sum + FEATURE_WEIGHTS[f] * (z(f, s[f]) - z(f, target[f])) ** 2, 0)
      return { ...s, distance: Math.sqrt(squared) }
    })
    .sort((a, b) => a.distance - b.distance)
}

// Short feature names for sentences ("closest on tempo and energy").
export const FEATURE_WORDS = {
  danceability: 'danceability', energy: 'energy', valence: 'positivity', acousticness: 'acousticness', tempo: 'tempo',
}

/** A world's sound fingerprint: the average of its songs on each feature. */
function worldFingerprint(world) {
  const list = songs.filter((s) => s.world === world)
  return Object.fromEntries(FEATURES.map((f) => [f, list.reduce((sum, s) => sum + s[f], 0) / list.length]))
}

/**
 * Rank every world by the same weighted z-score distance used for songs, but
 * measured to the world's fingerprint. Also says which features match best and
 * which differs most, and which of its songs the DJ would reach for first.
 */
export function rankWorlds(target) {
  return Object.keys(WORLDS)
    .map((world) => {
      const fingerprint = worldFingerprint(world)
      const terms = Object.fromEntries(FEATURES.map((f) =>
        [f, FEATURE_WEIGHTS[f] * (z(f, fingerprint[f]) - z(f, target[f])) ** 2]))
      const byGap = [...FEATURES].sort((a, b) => terms[a] - terms[b])
      return {
        world,
        fingerprint,
        distance: Math.sqrt(FEATURES.reduce((sum, f) => sum + terms[f], 0)),
        closestOn: byGap.slice(0, 2),
        differsMost: byGap[byGap.length - 1],
        bestSong: rankSongs(world, target)[0],
        nSongs: worldSongCount(world),
      }
    })
    .sort((a, b) => a.distance - b.distance)
}

/** Pick one song at random from the TOP_K closest (optionally skipping one). */
export function pickSong(ranked, avoidTrackId = null) {
  const candidates = avoidTrackId && ranked.length > 1
    ? ranked.filter((s) => s.track_id !== avoidTrackId)
    : ranked
  const top = candidates.slice(0, TOP_K)
  return top[Math.floor(Math.random() * top.length)]
}

// ---------------------------------------------------------------------------
// Words
// ---------------------------------------------------------------------------
const missing = (v) => v === null || v === undefined || Number.isNaN(v)
const pick = (list) => list[Math.floor(Math.random() * list.length)]
const pct = (v) => `${Math.round(v * 100)}%`
export const artistsOf = (song) => song.artists.replaceAll(';', ', ')

/** Describe the target sound in words ("mellow", "upbeat" ...). */
function soundWords(target) {
  const energy = target.energy < 0.45 ? 'mellow' : target.energy > 0.7 ? 'high-energy' : 'mid-energy'
  const mood = target.valence > 0.62 ? 'bright' : target.valence < 0.45 ? 'moody' : 'warm'
  return `${energy}, ${mood}`
}

/** What the DJ says after the three questions: the data behind the read. */
export function makeReading(target, mood, goal) {
  const genres = target.top_genres
  return {
    headline: `${target.n_respondents} people in the survey ${target.score_rule} and said music helps them.`,
    detail: `Compared with everyone else, they lean toward ${genres}. Mixed with your goal ` +
      `"${goal.toLowerCase()}", I'm cueing up something ${soundWords(target)} at about ` +
      `${Math.round(target.tempo)} BPM.`,
    moodPhrase: getMood(mood)?.phrase ?? mood.toLowerCase(),
  }
}

/** One neutral, data-backed fact about the world's representative country. */
function cultureFact(ctx) {
  if (!ctx) return ''
  const country = ctx.country_name
  const standIn = country !== ctx.world ? `${country} (our stand-in for ${ctx.world})` : country
  const facts = []
  if (!missing(ctx.social_support)) {
    facts.push(`in the World Happiness Report data (${ctx.whr_year}), ${pct(ctx.social_support)} ` +
      `of people surveyed in ${standIn} said they have someone to count on in times of trouble`)
  }
  if (!missing(ctx.positive_affect)) {
    facts.push(`in the World Happiness Report data, ${standIn} scored ${ctx.positive_affect.toFixed(2)} ` +
      'out of 1 on positive affect (how often people reported laughing and enjoying their day)')
  }
  if (!missing(ctx.indulgence)) {
    facts.push(`${standIn} scores ${Math.round(ctx.indulgence)}/100 on Hofstede's indulgence ` +
      'dimension, which measures how freely a society values enjoying life and having fun')
  }
  if (!missing(ctx.lastfm_users) && ctx.lastfm_users >= MIN_LASTFM_USERS_FOR_FACT) {
    facts.push(`the Last.fm culture dataset we used includes ${ctx.lastfm_users.toLocaleString()} ` +
      `listeners from ${country}`)
  }
  return facts.length ? pick(facts) : ''
}

/**
 * ===================== SWAP POINT FOR AN LLM =====================
 * The DJ's spoken intro. Right now it's a template. Keep the rule:
 * describe the music, never diagnose the listener's mental health.
 * =================================================================
 */
export function makeDjIntro(mood, goal, world, song) {
  const fact = cultureFact(getCulture(world))
  const factLine = fact ? ` Fun fact: ${fact}.` : ''
  return `You said you're ${getMood(mood)?.phrase ?? mood} and want ${getGoal(goal)?.ask ?? 'something good'}, ` +
    `so we're heading to ${world}.${factLine} Here's "${song.track_name}" by ${artistsOf(song)}. Let's dance!`
}

const fmt = (feature, value) => (feature === 'tempo' ? `${Math.round(value)} BPM` : value.toFixed(2))

/** Three plain-language sentences explaining why this song was picked. */
export function explainMatch(target, song, mood, goal, world) {
  const bpm = missing(target.median_bpm) ? ''
    : `, and reported a median favorite tempo of ${Math.round(target.median_bpm)} BPM`
  const s1 = `For "${mood}", we looked at the ${target.n_respondents} people in the Music & Mental ` +
    `Health (MxMH) survey who ${target.score_rule} and said music improves how they feel. ` +
    `Compared with the average respondent, they listened more to ${target.top_genres}${bpm}.`

  const s2 = 'We translated that listening mix into a target sound using genre averages from the ' +
    `Spotify Tracks Dataset, then your goal "${goal}" ${getGoal(goal)?.effect ?? 'adjusted it'}.`

  const gaps = Object.fromEntries(FEATURES.map((f) =>
    [f, Math.abs(song[f] - target[f]) / (f === 'tempo' ? 200 : 1)]))
  const closest = FEATURES.reduce((a, b) => (gaps[b] < gaps[a] ? b : a))
  const s3 = `Out of ${worldSongCount(world)} ${world} songs, "${song.track_name}" was one of the ` +
    `${TOP_K} closest matches; its ${FEATURE_LABELS[closest].toLowerCase()} was especially close ` +
    `to the target (${fmt(closest, song[closest])} vs ${fmt(closest, target[closest])}).`
  return [s1, s2, s3]
}

// ---------------------------------------------------------------------------
// Dance timing: Spotify sometimes reports double or half the "felt" tempo, so
// squeeze it into a comfortable dancing range.
// ---------------------------------------------------------------------------
export function danceBpm(tempo) {
  let bpm = tempo > 0 ? tempo : 120
  while (bpm > 150) bpm /= 2
  while (bpm < 70) bpm *= 2
  return bpm
}
