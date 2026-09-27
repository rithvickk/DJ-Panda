/*
 * DJ Panda. The DJ walks you through three questions (mood, how strong,
 * goal), reads the survey data for people like you, lets you pick a musical
 * world on a map, then spins a matching song.
 *
 * Steps: intro -> mood -> intensity -> goal -> reading -> results -> (map) -> playing -> why
 */
import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import DjPanda from './components/DjPanda'
import Question from './components/Question'
import WorldMap from './components/WorldMap'
import NowPlaying from './components/NowPlaying'
import WhySong from './components/WhySong'
import Results from './components/Results'
import {
  GOALS, MOODS, getMood, getTarget, intensityOptions, makeDjIntro, makeReading,
  pickSong, rankSongs, rankWorlds, danceBpm,
} from './lib/dj'

const STEPS = ['intro', 'mood', 'intensity', 'goal', 'reading', 'results', 'map', 'playing', 'why']
const PROGRESS = [
  { label: 'You', steps: ['mood', 'intensity', 'goal', 'reading'] },
  { label: 'World', steps: ['results', 'map'] },
  { label: 'Song', steps: ['playing'] },
  { label: 'Why', steps: ['why'] },
]
const WIDE_STEPS = ['results', 'map', 'playing', 'why']

export default function App() {
  const [step, setStep] = useState('intro')
  const [answers, setAnswers] = useState({ mood: null, intensity: null, goal: null })
  const [world, setWorld] = useState(null)
  const [ranked, setRanked] = useState([])
  const [song, setSong] = useState(null)
  const [intro, setIntro] = useState('')

  const target = answers.goal ? getTarget(answers.mood, answers.intensity, answers.goal) : null
  const mood = getMood(answers.mood)
  const ranking = useMemo(() => (target ? rankWorlds(target) : []), [target])

  const answer = (key, next) => (value) => {
    // Changing the mood resets how strong it is (the options differ).
    setAnswers((a) => ({ ...a, [key]: value, ...(key === 'mood' && value !== a.mood ? { intensity: null } : {}) }))
    setStep(next)
  }

  const back = () => setStep(STEPS[Math.max(STEPS.indexOf(step) - 1, 0)])

  const spin = (list, pickedWorld, avoid) => {
    const next = pickSong(list, avoid)
    setSong(next)
    setIntro(makeDjIntro(answers.mood, answers.goal, pickedWorld, next))
  }

  const chooseWorld = (picked) => {
    const list = rankSongs(picked, target)
    setWorld(picked)
    setRanked(list)
    spin(list, picked, null)
    setStep('playing')
  }

  const restart = () => {
    setAnswers({ mood: null, intensity: null, goal: null })
    setWorld(null)
    setSong(null)
    setStep('mood')
  }

  // What DJ Panda says on each step.
  const reading = target ? makeReading(target, answers.mood, answers.goal) : null
  const lines = {
    intro: "Yo! I'm DJ Panda. Answer three quick questions and I'll spin you a song from around the world that fits your vibe.",
    mood: 'First up: how are you feeling right now?',
    intensity: mood?.positive ? 'Love that! How good are we talking?' : `Got it, ${mood?.adjective}. How strong is that feeling?`,
    goal: 'Last one. What do you want the music to do for you?',
    reading: "Okay, I've read the room! Here's what the data says about people who feel like you.",
    results: ranking.length
      ? `Your sound lives closest to ${ranking[0].world}! Check the map, or pick any world you like.`
      : '',
    map: 'Where should we go? Tap a spot on the map.',
    playing: intro,
    why: "Here's how I picked it: no guesswork, just data.",
  }
  const bpm = step === 'playing' && song ? danceBpm(song.tempo) : 96

  return (
    <div className="app">
      <header className="topbar">
        <div className="logo">DJ <span>Panda</span></div>
        {step !== 'intro' && (
          <nav className="progress-dots" aria-label="Progress">
            {PROGRESS.map((p) => {
              const index = STEPS.indexOf(step)
              const done = p.steps.every((s) => STEPS.indexOf(s) < index)
              const current = p.steps.includes(step)
              return (
                <span key={p.label} className={`dot ${current ? 'is-current' : ''} ${done ? 'is-done' : ''}`}>
                  {p.label}
                </span>
              )
            })}
          </nav>
        )}
      </header>

      <main className={`booth ${WIDE_STEPS.includes(step) ? 'is-wide' : ''}`}>
        <DjPanda line={lines[step]} lineKey={step === 'playing' ? `playing-${song?.track_id}` : step} bpm={bpm} />

        <section className="stage-area">
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              className="card"
              initial={{ opacity: 0, y: 40, scale: 0.92 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -24, scale: 0.96 }}
              transition={{ type: 'spring', stiffness: 320, damping: 28 }}
            >
              {step === 'intro' && (
                <div className="intro">
                  <h1>Your mood.<br />A new world of music.</h1>
                  <p>Tell DJ Panda how you feel, pick a place on the map, and get a song that matches,
                    chosen using real survey and Spotify data.</p>
                  <button className="btn btn-primary btn-big" onClick={() => setStep('mood')}>Let's go 🎧</button>
                </div>
              )}

              {step === 'mood' && (
                <Question step={1} title="How are you feeling right now?" options={MOODS}
                  value={answers.mood} onAnswer={answer('mood', 'intensity')} columns={2} />
              )}

              {step === 'intensity' && (
                <Question step={2}
                  title={mood?.positive ? 'How good are you feeling?' : `How ${mood?.adjective} are you?`}
                  options={intensityOptions(answers.mood)}
                  value={answers.intensity} onAnswer={answer('intensity', 'goal')} columns={1} />
              )}

              {step === 'goal' && (
                <Question step={3} title="What do you want the music to do?" options={GOALS}
                  value={answers.goal} onAnswer={answer('goal', 'reading')} columns={2} />
              )}

              {step === 'reading' && reading && (
                <div className="reading">
                  <div className="kicker">DJ Panda's read</div>
                  <h2>You're {reading.moodPhrase}. You want to {answers.goal.toLowerCase()}.</h2>
                  <div className="reading-stats">
                    <div className="stat"><strong>{target.n_respondents}</strong><span>survey listeners like you</span></div>
                    <div className="stat"><strong>{Math.round(target.tempo)}</strong><span>target BPM</span></div>
                    <div className="stat"><strong>{target.energy.toFixed(2)}</strong><span>target energy</span></div>
                  </div>
                  <p>{reading.headline}</p>
                  <p>{reading.detail}</p>
                  <button className="btn btn-primary btn-big" onClick={() => setStep('results')}>See my matches 📊</button>
                </div>
              )}

              {step === 'results' && ranking.length > 0 && (
                <Results target={target} ranking={ranking} onGo={chooseWorld}
                  onMap={() => setStep('map')} onRestart={restart} />
              )}

              {step === 'map' && (
                <div>
                  <div className="kicker">Pick a musical world</div>
                  <WorldMap onPick={chooseWorld} />
                </div>
              )}

              {step === 'playing' && song && (
                <NowPlaying
                  world={world}
                  song={song}
                  onWhy={() => setStep('why')}
                  onSpin={() => spin(ranked, world, song.track_id)}
                  onChangeWorld={() => setStep('map')}
                  onRestart={restart}
                />
              )}

              {step === 'why' && song && (
                <WhySong target={target} song={song} mood={answers.mood} goal={answers.goal} world={world}
                  onBack={() => setStep('playing')} onRestart={restart} />
              )}
            </motion.div>
          </AnimatePresence>

          {['intensity', 'goal', 'reading', 'results', 'map'].includes(step) && (
            <button className="btn btn-ghost back" onClick={back}>← Back</button>
          )}
        </section>
      </main>
    </div>
  )
}
