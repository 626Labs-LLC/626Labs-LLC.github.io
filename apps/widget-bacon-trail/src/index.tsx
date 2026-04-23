// UMD/IIFE entry — exposes BaconTrailWidget.init/destroy on window.
// Per docs/spec.md > Widget config API.

import { createRoot, type Root } from 'react-dom/client';
import { StrictMode } from 'react';
import { Widget } from './Widget';
import type { BaconTrailWidgetConfig } from './types';
import './styles/widget.css';

// Track mounted React roots keyed by their container so `init(sameContainer)`
// can cleanly unmount a previous tree first, and `destroy(container)` can find
// the right root to tear down.
const roots = new WeakMap<HTMLElement, Root>();

export function init(config: BaconTrailWidgetConfig): void {
  const { container, theme, brandColor, brandLogo, ctaUrl, ctaLabel } = config;

  if (!container || !(container instanceof HTMLElement)) {
    console.warn('[BaconTrailWidget] init: invalid container, no-op.');
    return;
  }
  if (!container.isConnected) {
    console.warn('[BaconTrailWidget] init: container is not attached to the DOM, no-op.');
    return;
  }

  // If we already mounted into this container, tear down first so re-init is
  // idempotent.
  const prior = roots.get(container);
  if (prior) {
    prior.unmount();
    roots.delete(container);
  }

  if (theme === 'light') {
    console.info('[BaconTrailWidget] "light" theme requested; v1 renders dark regardless.');
  }

  const root = createRoot(container);
  root.render(
    <StrictMode>
      <Widget
        theme={theme ?? 'dark'}
        brandColor={brandColor}
        brandLogo={brandLogo}
        ctaUrl={ctaUrl}
        ctaLabel={ctaLabel}
      />
    </StrictMode>
  );
  roots.set(container, root);
}

export function destroy(container: HTMLElement): void {
  if (!container) return;
  const root = roots.get(container);
  if (!root) return;
  root.unmount();
  roots.delete(container);
}

// Attach to window for IIFE consumers — the hub's `<script>` + inline init()
// call expects this shape.
if (typeof window !== 'undefined') {
  (window as unknown as { BaconTrailWidget: { init: typeof init; destroy: typeof destroy } })
    .BaconTrailWidget = { init, destroy };
}
