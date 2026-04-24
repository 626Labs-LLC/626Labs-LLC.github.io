import { useEffect, useState } from 'react';
import { fetchLifetimeStats, type LifetimeStats, EMPTY_STATS } from '../services/statsService';

// Ambient mono caption line: "5,432 rounds · 1,876 found Bacon". Shown on the
// pick-actor screen (first thing a visitor sees) and on the result card.
// Renders `null` until stats load OR if counters are all zero (fresh deploy
// with no plays yet — no need to display "0 rounds · 0 found Bacon").

export function StatsLine() {
  const [stats, setStats] = useState<LifetimeStats>(EMPTY_STATS);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchLifetimeStats().then((s) => {
      if (cancelled) return;
      setStats(s);
      setLoaded(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!loaded || stats.totalPlayed === 0) return null;

  return (
    <p className="btw-stats-line" aria-label="Lifetime widget stats">
      <span className="num">{fmt(stats.totalPlayed)}</span>
      <span> rounds · </span>
      <span className="num">{fmt(stats.totalFound)}</span>
      <span> found Bacon</span>
    </p>
  );
}

function fmt(n: number): string {
  return n.toLocaleString('en-US');
}
