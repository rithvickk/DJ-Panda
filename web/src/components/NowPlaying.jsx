/*
 * Now spinning: the song card and a Spotify preview player.
 */
import { WORLDS, artistsOf } from '../lib/dj'

export default function NowPlaying({ world, song, onWhy, onSpin, onChangeWorld, onRestart }) {
  return (
    <div className="now-playing">
      <div className="song-card" style={{ '--world': WORLDS[world].color }}>
        <div className="kicker">Now spinning in {world}</div>
        <h2 className="song-title">{song.track_name}</h2>
        <p className="song-artist">{artistsOf(song)}</p>
        <p className="song-album">{song.album_name}</p>
        <div className="tags">
          <span className="tag">{Math.round(song.tempo)} BPM</span>
          <span className="tag">Energy {song.energy.toFixed(2)}</span>
          <span className="tag">{song.track_genre}</span>
        </div>
        <iframe
          key={song.track_id}
          className="player"
          title={`Spotify preview of ${song.track_name}`}
          src={`https://open.spotify.com/embed/track/${song.track_id}?utm_source=generator&theme=0`}
          height="152"
          allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
          loading="lazy"
        />
      </div>

      <div className="actions">
        <button className="btn btn-primary" onClick={onWhy}>Why this song? →</button>
        <button className="btn" onClick={onSpin}>🔀 Spin another</button>
        <button className="btn" onClick={onChangeWorld}>🌍 Change world</button>
        <button className="btn btn-ghost" onClick={onRestart}>↺ Start over</button>
      </div>
    </div>
  )
}
