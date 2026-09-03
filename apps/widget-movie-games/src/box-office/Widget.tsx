// Box Office Heads Up — compact 420px widget edition. Game logic ported
// from the WSYATM BoxOffice feature (vibe-taker bundle v1); UI re-dressed
// in 626 Labs brand for the hub's play section. Anonymous play, best
// score in localStorage.
import { useState, useCallback, useRef, useEffect } from 'react';
import {
  generateMatchups,
  getWinner,
  getFunFact,
  type Matchup,
} from './matchups';
import { formatDollars, formatDollarsFull, type Movie } from '../shared/movies';

const BEST_KEY = '626-boxoffice-best';
const ROUNDS = 10;

type RoundPhase = 'picking' | 'revealing' | 'revealed';

type GameResult = {
  score: number;
  correct: number;
  total: number;
  maxStreak: number;
  perfectGame: boolean;
};

function readBest(): number {
  try {
    return parseInt(localStorage.getItem(BEST_KEY) ?? '0', 10) || 0;
  } catch {
    return 0;
  }
}

export function Widget() {
  // The first game is dealt at mount so round 1 shows through the
  // translucent welcome overlay; Start just lifts the veil onto it.
  const [matchups, setMatchups] = useState<Matchup[]>(() => generateMatchups(ROUNDS));
  const [gameId, setGameId] = useState(0);
  const [covered, setCovered] = useState(true);
  const [result, setResult] = useState<GameResult | null>(null);
  const [best, setBest] = useState(readBest);

  const redeal = useCallback((cover: boolean) => {
    setMatchups(generateMatchups(ROUNDS));
    setGameId((id) => id + 1);
    setResult(null);
    setCovered(cover);
  }, []);

  const complete = useCallback((r: GameResult) => {
    setResult(r);
    setBest((prev) => {
      const next = Math.max(prev, r.score);
      try {
        localStorage.setItem(BEST_KEY, String(next));
      } catch {
        /* storage unavailable — score just isn't remembered */
      }
      return next;
    });
  }, []);

  return (
    <div className="box-office-widget">
      <div className="bow-brand">
        <span className="bow-brand-name">Box Office <em>Heads Up</em></span>
        <span className="bow-brand-tag">626 LABS</span>
      </div>
      {result ? (
        <Result result={result} best={best} onPlayAgain={() => redeal(false)} onMenu={() => redeal(true)} />
      ) : (
        <div className="bow-stage">
          <Rounds key={gameId} matchups={matchups} onComplete={complete} />
          {covered && (
            <div className="bow-overlay">
              <p className="bow-lead">
                Two movies. One question. Which opened bigger at the US box office?
              </p>
              <ul className="bow-rules">
                <li><strong>10</strong> rounds per game</li>
                <li><strong>75</strong> films spanning 1972–2024</li>
                <li><strong>Streaks</strong> multiply your score</li>
              </ul>
              {best > 0 && (
                <p className="bow-best">Best score <strong>{best.toLocaleString()}</strong></p>
              )}
              <button className="bow-btn-primary" onClick={() => setCovered(false)}>Start game</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Rounds({
  matchups,
  onComplete,
}: {
  matchups: Matchup[];
  onComplete: (r: GameResult) => void;
}) {
  const [round, setRound] = useState(0);
  const [roundPhase, setRoundPhase] = useState<RoundPhase>('picking');
  const [picked, setPicked] = useState<'a' | 'b' | null>(null);
  const [score, setScore] = useState(0);
  const [correct, setCorrect] = useState(0);
  const [streak, setStreak] = useState(0);
  const [maxStreak, setMaxStreak] = useState(0);
  const [countUpA, setCountUpA] = useState(0);
  const [countUpB, setCountUpB] = useState(0);
  const animFrame = useRef<number>(0);

  useEffect(() => () => cancelAnimationFrame(animFrame.current), []);

  const matchup = matchups[round];

  const handlePick = useCallback(
    (side: 'a' | 'b') => {
      if (roundPhase !== 'picking' || !matchup) return;
      setPicked(side);
      setRoundPhase('revealing');

      const winner = getWinner(matchup);
      const pickedMovie = side === 'a' ? matchup.movieA : matchup.movieB;
      const isCorrect = pickedMovie.id === winner.id;
      const newStreak = isCorrect ? streak + 1 : 0;
      const multiplier = streak >= 3 ? 2.0 : streak === 2 ? 1.5 : 1.0;
      const roundPoints = isCorrect ? Math.round(100 * multiplier) : 0;

      const targetA = matchup.movieA.openingWeekend;
      const targetB = matchup.movieB.openingWeekend;
      const duration = 1600;
      const startTime = performance.now();

      function animate(now: number) {
        const progress = Math.min((now - startTime) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        setCountUpA(Math.round(targetA * eased));
        setCountUpB(Math.round(targetB * eased));
        if (progress < 1) {
          animFrame.current = requestAnimationFrame(animate);
        } else {
          setCountUpA(targetA);
          setCountUpB(targetB);
          if (isCorrect) {
            setScore((s) => s + roundPoints);
            setCorrect((c) => c + 1);
          }
          setStreak(newStreak);
          setMaxStreak((mx) => Math.max(mx, newStreak));
          setRoundPhase('revealed');
        }
      }
      animFrame.current = requestAnimationFrame(animate);
    },
    [roundPhase, matchup, streak]
  );

  const handleNext = useCallback(() => {
    if (round + 1 >= matchups.length) {
      onComplete({
        score,
        correct,
        total: matchups.length,
        maxStreak,
        perfectGame: correct === matchups.length,
      });
    } else {
      setRound((r) => r + 1);
      setRoundPhase('picking');
      setPicked(null);
      setCountUpA(0);
      setCountUpB(0);
    }
  }, [round, matchups.length, score, correct, maxStreak, onComplete]);

  if (!matchup) return null;
  const winner = getWinner(matchup);
  const funFact = getFunFact(matchup);
  const multiplier = streak >= 3 ? 2.0 : streak === 2 ? 1.5 : 1.0;
  const isCorrect = picked
    ? (picked === 'a' ? matchup.movieA : matchup.movieB).id === winner.id
    : false;

  return (
    <div className="bow-screen">
      <div className="bow-hud">
        <span className="bow-hud-round">
          Round <strong>{round + 1}</strong>/{matchups.length}
        </span>
        <span className="bow-hud-score">
          {streak >= 2 && <em className="bow-mult">{multiplier}x</em>}
          {streak > 0 && <em className="bow-streak">streak {streak}</em>}
          <strong>{score.toLocaleString()}</strong>
        </span>
      </div>

      <h3 className={`bow-question${roundPhase === 'revealed' ? (isCorrect ? ' is-right' : ' is-wrong') : ''}`}>
        {roundPhase === 'picking'
          ? 'Which opened bigger?'
          : roundPhase === 'revealing'
            ? 'Counting the take…'
            : isCorrect
              ? 'Correct!'
              : 'Wrong!'}
      </h3>

      <div className="bow-matchup">
        <Card movie={matchup.movieA} side="a" picked={picked} phase={roundPhase} isWinner={matchup.movieA.id === winner.id} countUp={countUpA} onPick={handlePick} />
        <div className="bow-vs">VS</div>
        <Card movie={matchup.movieB} side="b" picked={picked} phase={roundPhase} isWinner={matchup.movieB.id === winner.id} countUp={countUpB} onPick={handlePick} />
      </div>

      {roundPhase === 'revealed' && (
        <div className="bow-reveal-footer">
          {funFact && <p className="bow-fact">{funFact}</p>}
          <button className="bow-btn-primary" onClick={handleNext}>
            {round + 1 >= matchups.length ? 'See results' : 'Next round →'}
          </button>
        </div>
      )}
    </div>
  );
}

function Card({
  movie,
  side,
  picked,
  phase,
  isWinner,
  countUp,
  onPick,
}: {
  movie: Movie;
  side: 'a' | 'b';
  picked: 'a' | 'b' | null;
  phase: RoundPhase;
  isWinner: boolean;
  countUp: number;
  onPick: (side: 'a' | 'b') => void;
}) {
  const isPicked = picked === side;
  const finished = phase === 'revealed';
  let stateClass = '';
  if (finished) stateClass = isWinner ? ' is-winner' : ' is-loser';
  else if (isPicked && phase === 'revealing') stateClass = ' is-picked';

  return (
    <button
      className={`bow-card${stateClass}`}
      onClick={() => onPick(side)}
      disabled={phase !== 'picking'}
    >
      <span className="bow-poster">
        {movie.posterUrl ? (
          <img src={movie.posterUrl} alt={movie.title} loading="lazy" />
        ) : (
          <span className="bow-poster-blank" aria-hidden="true" />
        )}
      </span>
      <span className="bow-card-title">{movie.title}</span>
      <span className="bow-card-meta">
        {movie.year} · {movie.rating}
      </span>
      {phase !== 'picking' ? (
        <span className={`bow-take${finished ? (isWinner ? ' is-winner' : ' is-loser') : ''}`}>
          {finished ? formatDollars(movie.openingWeekend) : formatDollarsFull(countUp)}
        </span>
      ) : (
        <span className="bow-pick-hint">pick</span>
      )}
    </button>
  );
}

function Result({
  result,
  best,
  onPlayAgain,
  onMenu,
}: {
  result: GameResult;
  best: number;
  onPlayAgain: () => void;
  onMenu: () => void;
}) {
  const pct = Math.round((result.correct / result.total) * 100);
  const title = result.perfectGame
    ? 'Perfect game!'
    : result.correct >= 8
      ? 'Box office buff'
      : result.correct >= 6
        ? 'Solid run'
        : result.correct >= 4
          ? 'Not bad'
          : 'Tough crowd';

  return (
    <div className="bow-screen bow-result">
      <h3 className="bow-result-title">{title}</h3>
      <div className="bow-result-score">{result.score.toLocaleString()}</div>
      <p className="bow-result-pts">points{result.score >= best && result.score > 0 ? ' · new best' : ''}</p>
      <div className="bow-result-stats">
        <div><strong>{result.correct}/{result.total}</strong><span>correct</span></div>
        <div><strong>{pct}%</strong><span>accuracy</span></div>
        <div><strong>{result.maxStreak}</strong><span>best streak</span></div>
      </div>
      <button className="bow-btn-primary" onClick={onPlayAgain}>Play again</button>
      <button className="bow-btn-ghost" onClick={onMenu}>Main menu</button>
    </div>
  );
}
