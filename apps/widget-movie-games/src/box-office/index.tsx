// IIFE entry — exposes BoxOfficeWidget.init/destroy on window.
// Same contract as BaconTrailWidget (see widget-bacon-trail/src/index.tsx).
import { createRoot, type Root } from 'react-dom/client';
import { StrictMode } from 'react';
import { Widget } from './Widget';
import './widget.css';

type Config = { container: HTMLElement };

const roots = new WeakMap<HTMLElement, Root>();

export function init(config: Config): void {
  const { container } = config;
  if (!container || !(container instanceof HTMLElement)) {
    console.warn('[BoxOfficeWidget] init: invalid container, no-op.');
    return;
  }
  if (!container.isConnected) {
    console.warn('[BoxOfficeWidget] init: container is not attached to the DOM, no-op.');
    return;
  }
  const prior = roots.get(container);
  if (prior) {
    prior.unmount();
    roots.delete(container);
  }
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <Widget />
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

if (typeof window !== 'undefined') {
  (window as unknown as { BoxOfficeWidget: { init: typeof init; destroy: typeof destroy } })
    .BoxOfficeWidget = { init, destroy };
}
