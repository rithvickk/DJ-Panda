/*
 * DJ Panda: the host. Sits at the decks, bobs along (to the song's beat once
 * one is playing), hops whenever a new line of dialogue appears, and talks
 * through a speech bubble.
 */
import { AnimatePresence, motion } from 'motion/react'
import panda from '../assets/dj-panda.png'

export default function DjPanda({ line, bpm = 96, lineKey }) {
  const beat = 60 / bpm

  return (
    <div className="dj-corner">
      <div className="bubble-slot" aria-live="polite">
        <AnimatePresence mode="wait">
          <motion.div
            key={lineKey}
            className="bubble"
            initial={{ opacity: 0, scale: 0.6, y: 14 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: -6 }}
            transition={{ type: 'spring', stiffness: 420, damping: 24 }}
          >
            {line}
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="panda-wrap">
        <div className="notes" aria-hidden="true">
          <span style={{ animationDelay: '0s' }}>♪</span>
          <span style={{ animationDelay: `${beat * 2}s` }}>♫</span>
          <span style={{ animationDelay: `${beat * 4}s` }}>♪</span>
        </div>
        {/* Outer element hops on each new line; inner one bobs on the beat. */}
        <motion.div
          key={lineKey}
          initial={{ y: 0 }}
          animate={{ y: [0, -18, 0, -6, 0] }}
          transition={{ duration: 0.55, ease: 'easeOut' }}
        >
          <img
            src={panda}
            alt="DJ Panda at the turntables"
            className="panda"
            style={{ '--beat': `${beat.toFixed(3)}s` }}
          />
        </motion.div>
      </div>
    </div>
  )
}
