/*
 * The world picker: a map where each musical world lights up on hover and
 * pops up a card on click. Small places (South Korea) are reachable via pins,
 * and the chips under the map do the same thing for keyboard/touch users.
 */
import { useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { geoNaturalEarth1, geoPath } from 'd3-geo'
import { feature } from 'topojson-client'
import atlas from 'world-atlas/countries-110m.json'
import { WORLDS, worldSongCount } from '../lib/dj'

const WIDTH = 960
const HEIGHT = 470

// Built once: country shapes (minus Antarctica), projection and path strings.
const countries = feature(atlas, atlas.objects.countries).features
  .filter((c) => c.properties.name !== 'Antarctica')
const projection = geoNaturalEarth1()
  .fitSize([WIDTH, HEIGHT], { type: 'FeatureCollection', features: countries })
const toPath = geoPath(projection)

const worldOf = (country) => Object.keys(WORLDS).find((w) =>
  WORLDS[w].countries.includes(country.id) || WORLDS[w].extraNames?.includes(country.properties.name))

const shapes = countries.map((c) => ({ key: c.id ?? c.properties.name, d: toPath(c), world: worldOf(c) }))
const pins = Object.fromEntries(Object.entries(WORLDS).map(([w, info]) => [w, projection(info.pin)]))

export default function WorldMap({ onPick }) {
  const [hovered, setHovered] = useState(null)
  const [selected, setSelected] = useState(null)
  const active = hovered ?? selected

  const select = (world) => setSelected((current) => (current === world ? null : world))

  return (
    <div className="map-block">
      <div className="map-frame" onMouseLeave={() => setHovered(null)}>
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="map" role="group" aria-label="World map of musical worlds">
          {shapes.map((s) => (
            <path
              key={s.key}
              d={s.d}
              className={s.world ? 'country in-world' : 'country'}
              style={s.world ? {
                '--world': WORLDS[s.world].color,
                opacity: active && active !== s.world ? 0.45 : 1,
              } : undefined}
              data-active={s.world && s.world === active ? 'true' : undefined}
              onMouseEnter={s.world ? () => setHovered(s.world) : undefined}
              onClick={s.world ? () => select(s.world) : () => setSelected(null)}
            />
          ))}

          {Object.entries(pins).map(([world, [x, y]]) => (
            <g
              key={world}
              className="pin"
              transform={`translate(${x} ${y})`}
              style={{ '--world': WORLDS[world].color }}
              data-active={world === active ? 'true' : undefined}
              onMouseEnter={() => setHovered(world)}
              onClick={() => select(world)}
            >
              <circle className="pin-pulse" r="14" />
              <circle className="pin-dot" r="9" />
              <text className="pin-label" y="-18">{world}</text>
            </g>
          ))}
        </svg>

        <AnimatePresence>
          {selected && (
            <WorldPopup key={selected} world={selected} onClose={() => setSelected(null)} onGo={() => onPick(selected)} />
          )}
        </AnimatePresence>
      </div>

      <div className="world-chips">
        {Object.entries(WORLDS).map(([world, info]) => (
          <button
            key={world}
            className={`chip world-chip ${selected === world ? 'is-on' : ''}`}
            style={{ '--world': info.color }}
            onClick={() => select(world)}
            onMouseEnter={() => setHovered(world)}
            onMouseLeave={() => setHovered(null)}
          >
            <span className="swatch" />{world}
          </button>
        ))}
      </div>
    </div>
  )
}

function WorldPopup({ world, onClose, onGo }) {
  const info = WORLDS[world]
  const [x, y] = pins[world]
  // Keep the card inside the map: clamp sideways, flip below the pin near the top.
  const left = Math.min(Math.max((x / WIDTH) * 100, 20), 80)
  const below = y / HEIGHT < 0.42
  const top = (y / HEIGHT) * 100

  // The anchor does the positioning; the inner card does the pop animation.
  return (
    <div
      className="popup-anchor"
      style={{ left: `${left}%`, top: `${top}%`, '--world': info.color }}
      data-below={below ? 'true' : undefined}
    >
      <motion.div
        className="world-popup"
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.6 }}
        transition={{ type: 'spring', stiffness: 460, damping: 26 }}
      >
        <button className="popup-close" onClick={onClose} aria-label="Close">×</button>
        <div className="popup-kicker">{info.subtitle}</div>
        <h3>{world}</h3>
        <p>{worldSongCount(world)} songs</p>
        <button className="btn btn-primary" onClick={onGo}>Spin it here 🎧</button>
      </motion.div>
    </div>
  )
}
