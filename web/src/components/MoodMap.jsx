/*
 * Mood map: every song as a faint dot at its positivity (valence) x energy,
 * each world's average as a big labelled dot, and the listener's target sound
 * as "You are here" with lines to the 3 closest worlds (closest on all five
 * features, not just these two).
 */
import { useEffect, useRef, useState } from 'react'
import { motion } from 'motion/react'
import { WORLDS, artistsOf, songs } from '../lib/dj'

const M = { top: 26, right: 20, bottom: 50, left: 60 }

/** Draw at the real on-screen width so text stays readable on phones. */
function useWidth(fallback) {
  const ref = useRef(null)
  const [width, setWidth] = useState(fallback)
  useEffect(() => {
    if (!ref.current) return undefined
    const observer = new ResizeObserver(([entry]) => setWidth(Math.round(entry.contentRect.width)))
    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])
  return [ref, width]
}
const CHAR_W = 7.6 // rough label width per character at 15px

// Zoom each axis to the world averages + target (plus room), snapped to 0.05.
function domain(values) {
  const lo = Math.max(0, Math.floor((Math.min(...values) - 0.06) * 20) / 20)
  const hi = Math.min(1, Math.ceil((Math.max(...values) + 0.06) * 20) / 20)
  return [lo, hi]
}
function ticks([lo, hi]) {
  const step = hi - lo > 0.5 ? 0.1 : 0.05
  const out = []
  for (let t = Math.ceil(lo / step - 1e-9) * step; t <= hi + 1e-9; t += step) out.push(+t.toFixed(2))
  return out
}

/**
 * Place each label beside its dot: right, left, above or below, whichever is
 * first to fit inside the plot without covering another dot or label.
 */
function placeLabels(items, bounds, obstacles) {
  const boxes = [
    ...items.map((it) => ({ x0: it.cx - it.r, x1: it.cx + it.r, y0: it.cy - it.r, y1: it.cy + it.r })),
    ...obstacles,
  ]
  const hits = (a, b) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1
  return items.map((it, i) => {
    const w = it.text.length * CHAR_W
    const options = [
      { x: it.cx + it.r + 6, y: it.cy + 5, anchor: 'start', box: [it.cx + it.r + 4, it.cy - 9, w + 4, 18] },
      { x: it.cx - it.r - 6, y: it.cy + 5, anchor: 'end', box: [it.cx - it.r - w - 8, it.cy - 9, w + 4, 18] },
      { x: it.cx, y: it.cy - it.r - 8, anchor: 'middle', box: [it.cx - w / 2, it.cy - it.r - 24, w, 18] },
      { x: it.cx, y: it.cy + it.r + 17, anchor: 'middle', box: [it.cx - w / 2, it.cy + it.r + 2, w, 18] },
    ].map((o) => ({ ...o, rect: { x0: o.box[0], y0: o.box[1], x1: o.box[0] + o.box[2], y1: o.box[1] + o.box[3] } }))
    const inside = (r) => r.x0 >= bounds.x0 && r.x1 <= bounds.x1 && r.y0 >= bounds.y0 && r.y1 <= bounds.y1
    const free = (r) => boxes.every((b, j) => j === i || !hits(r, b))
    const choice = options.find((o) => inside(o.rect) && free(o.rect)) ?? options.find((o) => inside(o.rect)) ?? options[0]
    boxes.push(choice.rect)
    return { id: it.id, text: it.text, x: choice.x, y: choice.y, anchor: choice.anchor }
  })
}

// Space taken by the four corner words (INTENSE, UPBEAT, MELLOW, BRIGHT & CALM).
function cornerBoxes(p) {
  const box = (x0, y0, w) => ({ x0, y0, x1: x0 + w, y1: y0 + 20 })
  return [
    box(p.x0, p.y0, 64), box(p.x1 - 58, p.y0, 58),
    box(p.x0, p.y1 - 20, 58), box(p.x1 - 112, p.y1 - 20, 112),
  ]
}

export default function MoodMap({ target, ranking, selected, onSelect }) {
  const [hovered, setHovered] = useState(null)
  const [asTable, setAsTable] = useState(false)
  const focus = hovered ?? selected
  const [frameRef, frameWidth] = useWidth(580)
  const W = Math.max(frameWidth, 280)
  const H = Math.round(Math.min(Math.max(W * 0.72, 300), 440))

  const xDomain = domain([...ranking.map((r) => r.fingerprint.valence), target.valence])
  const yDomain = domain([...ranking.map((r) => r.fingerprint.energy), target.energy])
  const x = (v) => M.left + ((v - xDomain[0]) / (xDomain[1] - xDomain[0])) * (W - M.left - M.right)
  const y = (v) => H - M.bottom - ((v - yDomain[0]) / (yDomain[1] - yDomain[0])) * (H - M.top - M.bottom)
  const plot = { x0: M.left, x1: W - M.right, y0: M.top, y1: H - M.bottom }
  const hiddenSongs = songs.filter((s) =>
    s.valence < xDomain[0] || s.valence > xDomain[1] || s.energy < yDomain[0] || s.energy > yDomain[1]).length

  const you = { x: x(target.valence), y: y(target.energy) }
  const nearest = ranking.slice(0, 3)
  const labels = placeLabels([
    { id: 'you', cx: you.x, cy: you.y, r: 12, text: 'You are here' },
    ...ranking.map((r, i) => ({
      id: r.world, cx: x(r.fingerprint.valence), cy: y(r.fingerprint.energy), r: 11, text: `${i + 1}. ${r.world}`,
    })),
  ], plot, cornerBoxes(plot))
  const focused = ranking.find((r) => r.world === focus)

  return (
    <section className="panel mood-map">
      <div className="panel-head">
        <h3>Mood map</h3>
        <p>Each big dot is the average of that world's {focused?.nSongs ?? ranking[0].nSongs} songs
          (Spotify audio features). Small dots are the songs themselves.</p>
      </div>

      <div ref={frameRef}>{asTable ? <MapTable target={target} ranking={ranking} /> : (
        <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} className="mm-svg" role="img"
          aria-label="Scatter of positivity against energy for each world and your target sound"
          onMouseLeave={() => setHovered(null)}>
          {/* grid + axes */}
          {ticks(xDomain).map((t) => (
            <g key={`x${t}`}>
              <line className="mm-grid" x1={x(t)} x2={x(t)} y1={M.top} y2={H - M.bottom} />
              <text className="mm-tick" x={x(t)} y={H - M.bottom + 18} textAnchor="middle">{t.toFixed(2)}</text>
            </g>
          ))}
          {ticks(yDomain).map((t) => (
            <g key={`y${t}`}>
              <line className="mm-grid" x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} />
              <text className="mm-tick" x={M.left - 8} y={y(t) + 4} textAnchor="end">{t.toFixed(2)}</text>
            </g>
          ))}
          <text className="mm-axis" x={(M.left + W - M.right) / 2} y={H - 10} textAnchor="middle">Positivity (valence) →</text>
          <text className="mm-axis" transform={`translate(14 ${(M.top + H - M.bottom) / 2}) rotate(-90)`} textAnchor="middle">Energy →</text>
          <text className="mm-quad" x={M.left + 8} y={M.top + 14}>INTENSE</text>
          <text className="mm-quad" x={W - M.right - 8} y={M.top + 14} textAnchor="end">UPBEAT</text>
          <text className="mm-quad" x={M.left + 8} y={H - M.bottom - 8}>MELLOW</text>
          <text className="mm-quad" x={W - M.right - 8} y={H - M.bottom - 8} textAnchor="end">BRIGHT &amp; CALM</text>

          {/* the songs behind each average (clipped to the zoomed plot) */}
          <clipPath id="mm-plot"><rect x={plot.x0} y={plot.y0} width={plot.x1 - plot.x0} height={plot.y1 - plot.y0} /></clipPath>
          <g clipPath="url(#mm-plot)">{songs.map((s) => (
            <circle key={s.track_id} className="mm-song" cx={x(s.valence)} cy={y(s.energy)} r="4.5"
              style={{ '--world': WORLDS[s.world].color, opacity: focus && focus !== s.world ? 0.12 : 0.45 }}>
              <title>{`${s.track_name} by ${artistsOf(s)} (${s.world})\npositivity ${s.valence.toFixed(2)}, energy ${s.energy.toFixed(2)}`}</title>
            </circle>
          ))}</g>

          {/* lines from you to your 3 nearest worlds */}
          {nearest.map((r, i) => (
            <motion.line key={r.world} className="mm-link" x1={you.x} y1={you.y}
              x2={x(r.fingerprint.valence)} y2={y(r.fingerprint.energy)}
              initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.3 + i * 0.12, duration: 0.5 }} />
          ))}

          {/* world averages */}
          {ranking.map((r) => (
            <g key={r.world} className="mm-world" style={{ '--world': WORLDS[r.world].color }}
              data-active={focus === r.world ? 'true' : undefined}
              onMouseEnter={() => setHovered(r.world)} onClick={() => onSelect(r.world)}>
              <circle className="mm-hit" cx={x(r.fingerprint.valence)} cy={y(r.fingerprint.energy)} r="18" />
              <circle className="mm-dot" cx={x(r.fingerprint.valence)} cy={y(r.fingerprint.energy)} r="9" />
            </g>
          ))}

          {/* you */}
          <g className="mm-you" transform={`translate(${you.x} ${you.y})`}>
            <circle className="mm-you-pulse" r="12" />
            <rect className="mm-you-mark" x="-8" y="-8" width="16" height="16" rx="3" transform="rotate(45)" />
          </g>

          {labels.map((l) => (
            <text key={l.id} className={`mm-label ${l.id === 'you' ? 'is-you' : ''}`} x={l.x} y={l.y} textAnchor={l.anchor}
              style={l.id !== 'you' && focus && focus !== l.id ? { opacity: 0.45 } : undefined}>{l.text}</text>
          ))}
        </svg>
      )}</div>

      <div className="mm-readout" aria-live="polite">
        {focused
          ? <><i className="swatch" style={{ '--world': WORLDS[focused.world].color }} /><strong>{focused.world}</strong> average:
            positivity {focused.fingerprint.valence.toFixed(2)} · energy {focused.fingerprint.energy.toFixed(2)} ·
            tempo {Math.round(focused.fingerprint.tempo)} BPM</>
          : <>Your target: positivity {target.valence.toFixed(2)} · energy {target.energy.toFixed(2)} · tempo {Math.round(target.tempo)} BPM</>}
      </div>

      <div className="mm-legend">
        <span><i className="key-you" />You (your target sound)</span>
        <span><i className="key-world" />World average (labelled by rank)</span>
        <span><i className="key-songdot" />One song</span>
        <span><i className="key-link" />Your 3 nearest worlds</span>
      </div>
      <p className="mm-note">
        Axes are zoomed in on the world averages
        {hiddenSongs > 0 ? `, so ${hiddenSongs} of the ${songs.length} songs sit outside the view` : ''}. Matching also uses danceability, acousticness and
        tempo, so the nearest dot on this map isn't always #1.{' '}
        <button className="link-btn" onClick={() => setAsTable((t) => !t)}>{asTable ? 'Show the map' : 'Show as a table'}</button>
      </p>
    </section>
  )
}

function MapTable({ target, ranking }) {
  const cols = [['valence', 'Positivity'], ['energy', 'Energy'], ['danceability', 'Dance'], ['acousticness', 'Acoustic'], ['tempo', 'BPM']]
  const cell = (f, v) => (f === 'tempo' ? Math.round(v) : v.toFixed(2))
  return (
    <table className="mm-table">
      <thead><tr><th>Rank</th><th>World</th>{cols.map(([, label]) => <th key={label}>{label}</th>)}</tr></thead>
      <tbody>
        <tr className="is-you"><td>–</td><td>You (target)</td>{cols.map(([f]) => <td key={f}>{cell(f, target[f])}</td>)}</tr>
        {ranking.map((r, i) => (
          <tr key={r.world}><td>{i + 1}</td><td>{r.world}</td>{cols.map(([f]) => <td key={f}>{cell(f, r.fingerprint[f])}</td>)}</tr>
        ))}
      </tbody>
    </table>
  )
}
