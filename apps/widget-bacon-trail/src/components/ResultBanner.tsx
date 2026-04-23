import { Sparkles, Clock } from 'lucide-react';
import type { Outcome } from '../types';

interface Props {
  outcome: Outcome;
  filmCount: number;
}

// One-line celebratory banner shown in the top slot when the round ends.
// Replaces the TrailBreadcrumb box since the ResultCard below already
// shows the full trail. No frame, no padding box — just a voice line.
export function ResultBanner({ outcome, filmCount }: Props) {
  if (outcome === 'found') {
    return (
      <p className="btw-banner success">
        <Sparkles size={14} strokeWidth={2} aria-hidden="true" />
        <span>
          Kevin Bacon found in <strong>{filmCount}</strong> film{filmCount === 1 ? '' : 's'}.
        </span>
      </p>
    );
  }
  return (
    <p className="btw-banner miss">
      <Clock size={14} strokeWidth={2} aria-hidden="true" />
      <span>6 films walked — no Bacon this time.</span>
    </p>
  );
}
