/*
 * Quiz results: which musical world is closest to the sound you're after.
 * Mood map on the left, the ranking of all five worlds on the right. Picking a
 * world (on either) selects it; the big button heads there and spins a song.
 */
import { useState } from 'react'
import { motion } from 'motion/react'
import MoodMap from './MoodMap'
import { FEATURE_WORDS, WORLDS, artistsOf } from '../lib/dj'

const reason = (r) =>
  `Closest on ${FEATURE_WORDS[r.closestOn[0]]} and ${FEATURE_WORDS[r.closestOn[1]]}; ` +
  `differs most in ${FEATURE_WORDS[r.differsMost]}.`

export default function Results({ target, ranking, onGo, onMap, onRestart }) {
  const [selected, setSelected] = useState(ranking[0].world)
  const top = ranking[0]
  // Closeness bar: 100% = on the target, shrinking with distance.
  const maxDistance = Math.max(...ranking.map((r) => r.distance)) * 1.2

  return (
    <div className="results">
      <div className="results-head">
        <div className="kicker">Your results</div>
        <h2><span style={{ '--world': WORLDS[top.world].color }} className="world-word">{top.world}</span> is closest
          to the sound you're after</h2>
        <p>{reason(top)} Here's the whole map and how every world stacks up.</p>
      </div>

      <div className="results-grid">
        <MoodMap target={target} ranking={ranking} selected={selected} onSelect={setSelected} />

        <section className="panel ranking">
          <div className="panel-head">
            <h3>Ranking</h3>
            <p>Distance across all five sound features. Click a world to pick it.</p>
          </div>
          <ol className="rank-list">
            {ranking.map((r, i) => (
              <motion.li key={r.world} initial={{ opacity: 0, x: 18 }} animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + i * 0.07 }}>
                <button className={`rank-row ${selected === r.world ? 'is-on' : ''}`}
                  style={{ '--world': WORLDS[r.world].color }} onClick={() => setSelected(r.world)}
                  aria-pressed={selected === r.world}>
                  <span className="rank-num">{i + 1}</span>
                  <span className="rank-body">
                    <strong><i className="swatch" />{r.world}</strong>
                    <span>{reason(r)}</span>
                    <em>Closest song: “{r.bestSong.track_name}” by {artistsOf(r.bestSong)}</em>
                  </span>
                  <span className="rank-bar" title={`Distance ${r.distance.toFixed(2)} (lower is closer)`}>
                    <motion.i initial={{ width: 0 }}
                      animate={{ width: `${Math.max(6, (1 - r.distance / maxDistance) * 100)}%` }}
                      transition={{ delay: 0.25 + i * 0.07, duration: 0.6, ease: 'easeOut' }} />
                  </span>
                </button>
              </motion.li>
            ))}
          </ol>
          <div className="actions">
            <button className="btn btn-primary" onClick={() => onGo(selected)}>Escape to {selected} →</button>
            <button className="btn btn-ghost" onClick={onMap}>Pick on the world map</button>
            <button className="btn btn-ghost" onClick={onRestart}>↺ Retake quiz</button>
          </div>
        </section>
      </div>

      <p className="disclaimer">
        Not medical advice. The target sound comes from Music &amp; Mental Health survey respondents
        who reported a similar feeling and said music helps them; it shows patterns associated with
        those answers, not what will work for you. No world, genre or song is better or worse for
        mental health.
      </p>
    </div>
  )
}
