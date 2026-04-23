// Brand constants — typed mirrors of the CSS custom properties in
// styles/tokens.css. For places where JS logic needs a color value
// (e.g., inline style overrides for user-configurable brandColor) or
// where TypeScript wants to be explicit about design-system constants.

export const BRAND = {
  cyan: '#17d4fa',
  magenta: '#f22f89',
  navy0: '#0f1f31',
  navy1: '#192e44',
  navy2: '#223a54',
  navy3: '#2a3649',
  success: '#2bd99a',
  warning: '#ffb454',
  danger: '#ff5472',
} as const;

export const MOTION = {
  easeOut: 'cubic-bezier(0.2, 0.7, 0.2, 1)',
  fast: 120,
  med: 220,
  slow: 380,
} as const;
