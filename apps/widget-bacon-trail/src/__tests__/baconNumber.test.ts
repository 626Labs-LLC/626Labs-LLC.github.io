import { describe, expect, it } from 'vitest';
import { displayBaconNumber } from '../lib/baconNumber';

describe('displayBaconNumber', () => {
  it('hides the line when the stored number is unknown', () => {
    for (const stored of [undefined, null, -1, 2.5, '2', NaN]) {
      expect(displayBaconNumber({ stored, won: true, steps: 2 })).toEqual({
        baconNumber: null,
        shortestRoute: false,
      });
    }
  });

  it('shows the stored number on a loss, never shortest', () => {
    expect(displayBaconNumber({ stored: 2, won: false, steps: 6 })).toEqual({
      baconNumber: 2,
      shortestRoute: false,
    });
  });

  it('calls a win that matches the stored number the shortest route', () => {
    expect(displayBaconNumber({ stored: 2, won: true, steps: 2 })).toEqual({
      baconNumber: 2,
      shortestRoute: true,
    });
  });

  it('shows the stored number on a longer win, not shortest', () => {
    expect(displayBaconNumber({ stored: 2, won: true, steps: 4 })).toEqual({
      baconNumber: 2,
      shortestRoute: false,
    });
  });

  it('shows the player count when the win beats the stored number', () => {
    expect(displayBaconNumber({ stored: 3, won: true, steps: 2 })).toEqual({
      baconNumber: 2,
      shortestRoute: false,
    });
  });
});
