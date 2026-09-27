/*
 * Why this song? Target sound vs the song on each feature, the tempo gap,
 * and three plain-language sentences about the data behind the pick.
 */
import { motion } from 'motion/react'
import { FEATURE_LABELS, explainMatch } from '../lib/dj'

const BAR_FEATURES = ['danceability', 'energy', 'valence', 'acousticness']

export default function WhySong({ target, song, mood, goal, world, onBack, onRestart }) {
  const sentences = explainMatch(target, song, mood, goal, world)
  const tempoGap = song.tempo - target.tempo

  return (
    <div className="why">
      <div className="why-grid">
        <section className="panel">
          <h3>Target sound vs “{song.track_name}”</h3>
          <div className="legend">
            <span><i className="key key-target" />Target</span>
            <span><i className="key key-song" />This song</span>
          </div>
          <div className="bars">
            {BAR_FEATURES.map((f, i) => (
              <div className="bar-row" key={f}>
                <div className="bar-name">{FEATURE_LABELS[f]}</div>
                <Bar kind="target" value={target[f]} delay={i * 0.08} />
                <Bar kind="song" value={song[f]} delay={i * 0.08 + 0.04} />
              </div>
            ))}
            <div className="bar-axis"><span>0</span><span>0.5</span><span>1</span></div>
          </div>
          <div className="tiles">
            <div className="tile"><span>Target tempo</span><strong>{Math.round(target.tempo)} BPM</strong></div>
            <div className="tile">
              <span>Song tempo</span>
              <strong>{Math.round(song.tempo)} BPM</strong>
              <em>{tempoGap >= 0 ? '+' : ''}{Math.round(tempoGap)} BPM</em>
            </div>
          </div>
        </section>

        <section className="panel">
          <h3>How the DJ chose</h3>
          <ol className="reasons">
            {sentences.map((s, i) => (
              <motion.li key={i} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15 + i * 0.12 }}>{s}</motion.li>
            ))}
          </ol>
        </section>
      </div>

      <p className="disclaimer">
        Data: Music &amp; Mental Health survey (Kaggle MxMH), Spotify Tracks Dataset, and the
        Culture-Aware Music Recommendation Dataset (Zenodo: Last.fm users, Hofstede dimensions,
        World Happiness Report 2018). These describe population-level patterns in how survey
        respondents say music helps them. DJ Panda does not diagnose, assess or predict anyone's
        mental health.
      </p>

      <div className="actions">
        <button className="btn btn-primary" onClick={onBack}>← Back to the DJ</button>
        <button className="btn btn-ghost" onClick={onRestart}>↺ Start over</button>
      </div>
    </div>
  )
}

function Bar({ kind, value, delay }) {
  return (
    <div className="bar-track" title={`${kind === 'target' ? 'Target' : 'This song'}: ${value.toFixed(2)}`}>
      <motion.div
        className={`bar-fill bar-${kind}`}
        initial={{ width: 0 }}
        animate={{ width: `${Math.max(value, 0.02) * 100}%` }}
        transition={{ delay, duration: 0.6, ease: 'easeOut' }}
      />
      <span className="bar-value">{value.toFixed(2)}</span>
    </div>
  )
}
