// UMD/IIFE entry — exposes BaconTrailWidget.init/destroy on window.
// Stub for Item 1; real implementation lands in Item 5 once the components
// from Item 4 are ready. See docs/checklist.md.

import './styles/widget.css';

export interface BaconTrailWidgetConfig {
  container: HTMLElement;
  theme?: 'dark' | 'light';
  brandColor?: string;
  brandLogo?: string;
  ctaUrl?: string;
  ctaLabel?: string;
  firebaseConfig?: null;
}

export function init(config: BaconTrailWidgetConfig): void {
  console.info('[BaconTrailWidget] init — scaffold only, real mount lands in Item 5.', config);
}

export function destroy(container: HTMLElement): void {
  console.info('[BaconTrailWidget] destroy', container);
}

// Attach to window for IIFE consumers — the hub's `<script>` + inline init()
// call expects this shape.
if (typeof window !== 'undefined') {
  (window as unknown as { BaconTrailWidget: unknown }).BaconTrailWidget = { init, destroy };
}
