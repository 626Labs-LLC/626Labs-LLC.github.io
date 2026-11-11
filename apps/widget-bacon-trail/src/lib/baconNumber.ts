// The Bacon number line on the result card. Mirrors WeSeeYouAtTheMovies'
// displayBaconNumber (functions/src/utils/bacon.js, its D74 part 1): the
// number shown is never one the player just beat.
//
// `stored` is the shard's baconNumber for the starting actor, copied nightly
// from the CinePerks actorDatabase by refresh-bacon-shards.mjs. That count
// was not computed under this widget's edge rules (top 45 films, top 27
// cast), so it can be beaten here; when it is, the player's count wins.
// The sibling app also flags the actor doc for a recheck on a beat. The hub
// has no write path to that database, so a beat here only changes the line.

export interface BaconNumberLine {
  /** What to show; null hides the line. */
  baconNumber: number | null;
  /** The win matched the stored number exactly. */
  shortestRoute: boolean;
}

export function displayBaconNumber({
  stored,
  won,
  steps,
}: {
  stored: unknown;
  won: boolean;
  steps: number;
}): BaconNumberLine {
  if (typeof stored !== 'number' || !Number.isInteger(stored) || stored < 0) {
    return { baconNumber: null, shortestRoute: false };
  }
  if (!won) return { baconNumber: stored, shortestRoute: false };
  if (steps >= stored) return { baconNumber: stored, shortestRoute: steps === stored };
  return { baconNumber: steps, shortestRoute: false };
}
