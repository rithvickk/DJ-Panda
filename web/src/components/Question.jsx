/*
 * One question card: a big prompt and chunky answer chips that pop in one
 * after another. Picking an answer flashes it, then moves on automatically.
 */
import { useState } from 'react'
import { motion } from 'motion/react'

const ADVANCE_DELAY_MS = 380

export default function Question({ step, title, options, value, onAnswer, columns = 2 }) {
  const [chosen, setChosen] = useState(value ?? null)

  const choose = (id) => {
    if (chosen && chosen !== value) return // already advancing
    setChosen(id)
    setTimeout(() => onAnswer(id), ADVANCE_DELAY_MS)
  }

  return (
    <div className="question">
      <div className="kicker">Question {step} of 3</div>
      <h2>{title}</h2>
      <div className="options" style={{ '--cols': columns }}>
        {options.map((option, i) => (
          <motion.button
            key={option.id}
            className={`chip answer ${chosen === option.id ? 'is-on' : ''}`}
            initial={{ opacity: 0, y: 18, scale: 0.9 }}
            animate={chosen === option.id
              ? { opacity: 1, y: 0, scale: [1, 1.08, 1] }
              : { opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: chosen ? 0 : 0.12 + i * 0.05, type: 'spring', stiffness: 500, damping: 28 }}
            whileHover={{ y: -3 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => choose(option.id)}
          >
            {option.emoji && <span className="answer-emoji" aria-hidden="true">{option.emoji}</span>}
            <span className="answer-text">
              <span className="answer-label">{option.label ?? option.id}</span>
              {option.hint && <span className="answer-hint">{option.hint}</span>}
            </span>
          </motion.button>
        ))}
      </div>
    </div>
  )
}
