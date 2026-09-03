// Tag That Line — compact 420px widget edition. Round flow ported from
// the WSYATM TagThatLine component (vibe-taker bundle v1), scoring
// preserved (10/5/2 by wrong taps, 3 misses auto-reveals), server
// session/submission replaced by local generation + localStorage best.
// The tagline pool is runtime data fetched from
// /widget-tag-that-line/data/pool.json (see shared/data.ts).
import { useState, useCallback, useEffect } from 'react';
import { generateRounds, pointsFor, type Round } from './rounds';
import { loadPool, type PoolEntry } from '../shared/data';

const BEST_KEY = '626-tagthatline-best';
const ROUNDS = 8;
const MAX_WRONG = 3;

type GamePhase = 'playing' | 'result';
type CardState = 'default' | 'incorrect' | 'correct';

function readBest(): number {
  try {
    return parseInt(localStorage.getItem(BEST_KEY) ?? '0', 10) || 0;
  } catch {
    return 0;
  }
}

export function Widget() {
  // The pool fetches at mount, then the first session is dealt so round 1
  // shows through the translucent welcome overlay; Start lifts the veil.
  const [pool, setPool] = useState<PoolEntry[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadTry, setLoadTry] = useState(0);
  const [phase, setPhase] = useState<GamePhase>('playing');
  const [covered, setCovered] = useState(true);
  const [rounds, setRounds] = useState<Round[]>([]);
  const [roundIdx, setRoundIdx] = useState(0);
  const [score, setScore] = useState(0);
  const [tagged, setTagged] = useState(0);
  const [streak, setStreak] = useState(0);
  const [bestStreak, setBestStreak] = useState(0);
  const [wrongTaps, setWrongTaps] = useState(0);
  const [roundDone, setRoundDone] = useState(false);
  const [cardStates, setCardStates] = useState<Record<string, CardState>>({});
  const [best, setBest] = useState(readBest);

  useEffect(() => {
    let alive = true;
    setLoadError(null);
    loadPool().then(
      (entries) => {
        if (!alive) return;
        setPool(entries);
        setRounds(generateRounds(entries, ROUNDS));
      },
      (err: Error) => {
        if (alive) setLoadError(err.message);
      }
    );
    return () => {
      alive = false;
    };
  }, [loadTry]);

  const redeal = useCallback((cover: boolean) => {
    if (!pool) return;
    setRounds(generateRounds(pool, ROUNDS));
    setRoundIdx(0);
    setScore(0);
    setTagged(0);
    setStreak(0);
    setBestStreak(0);
    setWrongTaps(0);
    setRoundDone(false);
    setCardStates({});
    setPhase('playing');
    setCovered(cover);
  }, [pool]);

  const round = rounds[roundIdx];

  const handleTap = useCallback(
    (movieId: string) => {
      if (roundDone || !round) return;
      if (movieId === round.correctMovieId) {
        setScore((s) => s + pointsFor(wrongTaps));
        setTagged((t) => t + 1);
        setRoundDone(true);
        setCardStates((cs) => ({ ...cs, [movieId]: 'correct' }));
        if (wrongTaps === 0) {
          setStreak((st) => {
            const next = st + 1;
            setBestStreak((b) => Math.max(b, next));
            return next;
          });
        }
      } else {
        setStreak(0);
        setWrongTaps((w) => {
          const next = w + 1;
          if (next >= MAX_WRONG) {
            setRoundDone(true);
            setCardStates((cs) => ({
              ...cs,
              [movieId]: 'incorrect',
              [round.correctMovieId]: 'correct',
            }));
          } else {
            setCardStates((cs) => ({ ...cs, [movieId]: 'incorrect' }));
          }
          return next;
        });
      }
    },
    [roundDone, round, wrongTaps]
  );

  const nextRound = useCallback(() => {
    if (roundIdx + 1 < rounds.length) {
      setRoundIdx((i) => i + 1);
      setRoundDone(false);
      setWrongTaps(0);
      setCardStates({});
    } else {
      setBest((prev) => {
        const next = Math.max(prev, score);
        try {
          localStorage.setItem(BEST_KEY, String(next));
        } catch {
          /* storage unavailable — score just isn't remembered */
        }
        return next;
      });
      setPhase('result');
    }
  }, [roundIdx, rounds.length, score]);

  return (
    <div className="tag-that-line-widget">
      <div className="ttl-brand">
        <span className="ttl-brand-name">Tag <em>That Line</em></span>
        <span className="ttl-brand-tag">626 LABS</span>
      </div>

      {loadError && (
        <div className="ttl-screen ttl-load">
          <p className="ttl-load-title">Projector trouble.</p>
          <p className="ttl-load-note">Couldn't load the tagline pool.</p>
          <button className="ttl-btn-primary" onClick={() => setLoadTry((t) => t + 1)}>
            Retry
          </button>
        </div>
      )}

      {!loadError && (!pool || rounds.length === 0) && (
        <div className="ttl-screen ttl-load">
          <p className="ttl-load-note">Loading the reel…</p>
        </div>
      )}

      {phase === 'playing' && round && (
        <div className="ttl-stage">
        <div className="ttl-screen">
          <div className="ttl-hud">
            <span className="ttl-progress">
              {rounds.map((_, i) => (
                <i
                  key={i}
                  className={
                    i < roundIdx
                      ? 'is-done'
                      : i === roundIdx
                        ? 'is-current'
                        : ''
                  }
                />
              ))}
            </span>
            <span className="ttl-hud-score">
              {streak > 1 && <em>streak {streak}</em>}
              <strong>{score}</strong>
            </span>
          </div>

          <p className="ttl-tagline">&ldquo;{round.tagline}&rdquo;</p>

          <div className="ttl-grid">
            {round.posters.map((poster) => {
              const state = cardStates[poster.movieId] ?? 'default';
              return (
                <button
                  key={poster.movieId}
                  className={`ttl-poster is-${state}${roundDone && state === 'default' ? ' is-dimmed' : ''}`}
                  onClick={() => handleTap(poster.movieId)}
                  disabled={roundDone || state !== 'default'}
                  aria-label={roundDone ? poster.title : 'Movie poster'}
                >
                  <img src={poster.posterUrl} alt="" loading="lazy" />
                  {roundDone && state === 'correct' && (
                    <span className="ttl-poster-label">{poster.title}</span>
                  )}
                </button>
              );
            })}
          </div>

          <div className="ttl-footer">
            {roundDone ? (
              <button className="ttl-btn-primary" onClick={nextRound}>
                {roundIdx + 1 >= rounds.length ? 'See results' : 'Next tagline →'}
              </button>
            ) : (
              <span className="ttl-misses">
                {wrongTaps > 0
                  ? `${MAX_WRONG - wrongTaps} ${MAX_WRONG - wrongTaps === 1 ? 'tap' : 'taps'} left`
                  : 'a clean tag scores 10'}
              </span>
            )}
          </div>
        </div>
        {covered && (
          <div className="ttl-overlay">
            <p className="ttl-lead">
              A classic movie tagline, four posters. Tap the one it belongs to.
            </p>
            <ul className="ttl-rules">
              <li><strong>{ROUNDS}</strong> taglines per game</li>
              <li><strong>10</strong> points for a clean tag, less per miss</li>
              <li><strong>3</strong> misses reveals the answer</li>
            </ul>
            {best > 0 && (
              <p className="ttl-best">Best score <strong>{best}</strong></p>
            )}
            <button className="ttl-btn-primary" onClick={() => setCovered(false)}>Start game</button>
          </div>
        )}
        </div>
      )}

      {phase === 'result' && (
        <div className="ttl-screen ttl-result">
          <h3 className="ttl-result-title">
            {tagged === rounds.length
              ? 'Every line tagged!'
              : tagged >= rounds.length - 2
                ? 'Sharp eye'
                : tagged >= rounds.length / 2
                  ? 'Solid run'
                  : 'Tough reel'}
          </h3>
          <div className="ttl-result-score">{score}</div>
          <p className="ttl-result-pts">
            points{score >= best && score > 0 ? ' · new best' : ''}
          </p>
          <div className="ttl-result-stats">
            <div><strong>{tagged}/{rounds.length}</strong><span>tagged</span></div>
            <div><strong>{bestStreak}</strong><span>best streak</span></div>
          </div>
          <button className="ttl-btn-primary" onClick={() => redeal(false)}>Play again</button>
          <button className="ttl-btn-ghost" onClick={() => redeal(true)}>Main menu</button>
        </div>
      )}
    </div>
  );
}
