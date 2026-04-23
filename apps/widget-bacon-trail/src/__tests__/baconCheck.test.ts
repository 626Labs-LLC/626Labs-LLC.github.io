import { describe, it, expect } from 'vitest';
import { castIncludesBacon } from '../services/baconCheck';
import { KEVIN_BACON_TMDB_ID } from '../types';

const mkActor = (id: number, name = `Actor ${id}`) => ({ id, name, profilePath: null });

describe('castIncludesBacon', () => {
  it('returns false for an empty cast', () => {
    expect(castIncludesBacon([])).toBe(false);
  });

  it('returns false when Bacon is not present', () => {
    expect(castIncludesBacon([mkActor(1), mkActor(2), mkActor(3)])).toBe(false);
  });

  it('returns true when Bacon is the only cast member', () => {
    expect(castIncludesBacon([mkActor(KEVIN_BACON_TMDB_ID, 'Kevin Bacon')])).toBe(true);
  });

  it('returns true when Bacon is among multiple cast members', () => {
    expect(
      castIncludesBacon([
        mkActor(1),
        mkActor(KEVIN_BACON_TMDB_ID, 'Kevin Bacon'),
        mkActor(2),
      ])
    ).toBe(true);
  });

  it('matches strictly on id, not name', () => {
    // A different actor coincidentally named "Kevin Bacon" (real edge case
    // in TMDB — name matching is unreliable). Only id 4724 counts.
    expect(
      castIncludesBacon([{ id: 9999999, name: 'Kevin Bacon', profilePath: null }])
    ).toBe(false);
  });
});
