import { describe, expect, it } from 'vitest';
import { displayBaconNumber } from '../lib/baconNumber';

describe('displayBaconNumber', () => {
  it('hides the line when the stored number is unknown', () => {
    for (const stored of [undefined, null, -1, 2.5, '2', NaN]) {
      expect(displayBaconNumber({ stored, won: true, steps: 2 })).toEqual({
        baconNumber: null,
        shortestRoute: false,
        notHere: false,
      });
    }
  });

  it('shows the stored number on a loss, never shortest', () => {
    expect(displayBaconNumber({ stored: 2, won: false, steps: 6 })).toEqual({
      baconNumber: 2,
      shortestRoute: false,
      notHere: false,
    });
  });

  it('calls a win that matches the stored number the shortest route', () => {
    expect(displayBaconNumber({ stored: 2, won: true, steps: 2 })).toEqual({
      baconNumber: 2,
      shortestRoute: true,
      notHere: false,
    });
  });

  it('shows the stored number on a longer win, not shortest', () => {
    expect(displayBaconNumber({ stored: 2, won: true, steps: 4 })).toEqual({
      baconNumber: 2,
      shortestRoute: false,
      notHere: false,
    });
  });

  it('shows the player count when the win beats the stored number', () => {
    expect(displayBaconNumber({ stored: 3, won: true, steps: 2 })).toEqual({
      baconNumber: 2,
      shortestRoute: false,
      notHere: false,
    });
  });

  it('notHere on a loss when unreachable', () => {
    expect(displayBaconNumber({ stored: 2, won: false, steps: 6, hubReachable: false })).toEqual({
      baconNumber: 2,
      shortestRoute: false,
      notHere: true,
    });
  });

  it('notHere on a longer win when unreachable', () => {
    expect(displayBaconNumber({ stored: 2, won: true, steps: 4, hubReachable: false }).notHere).toBe(true);
  });

  it('a win at the stored number overrides the cache', () => {
    expect(displayBaconNumber({ stored: 2, won: true, steps: 2, hubReachable: false })).toEqual({
      baconNumber: 2,
      shortestRoute: true,
      notHere: false,
    });
  });

  it('a win under the stored number shows the player count with no caveat, whatever the cache says', () => {
    expect(displayBaconNumber({ stored: 3, won: true, steps: 2, hubReachable: false })).toEqual({
      baconNumber: 2,
      shortestRoute: false,
      notHere: false,
    });
  });

  it('unknown reach makes no claim', () => {
    expect(displayBaconNumber({ stored: 2, won: false, steps: 6 }).notHere).toBe(false);
  });

  it('no number, no caveat', () => {
    expect(displayBaconNumber({ stored: undefined, won: false, steps: 6, hubReachable: false })).toEqual({
      baconNumber: null,
      shortestRoute: false,
      notHere: false,
    });
  });
});
