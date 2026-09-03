import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Two library builds out of one app, selected by --mode:
//   vite build --mode boxoffice → ../../widget-box-office/{widget.js,widget.css}
//   vite build --mode tagline   → ../../widget-tag-that-line/{widget.js,widget.css}
// Output lands at the hub root so GitHub Pages serves it directly, mirroring
// the widget-bacon-trail pattern. Dev mode serves dev.html on port 3004 with
// both games mounted side by side.

const TARGETS = {
  boxoffice: {
    entry: 'src/box-office/index.tsx',
    name: 'BoxOfficeWidget',
    outDir: '../../widget-box-office',
  },
  tagline: {
    entry: 'src/tag-that-line/index.tsx',
    name: 'TagThatLineWidget',
    outDir: '../../widget-tag-that-line',
  },
} as const;

export default defineConfig(({ command, mode }) => {
  const baseConfig = {
    plugins: [react()],
    server: {
      port: 3004,
      host: '0.0.0.0',
    },
    test: {
      environment: 'node',
      globals: true,
    },
  };

  if (command === 'serve') {
    return baseConfig;
  }

  const target = TARGETS[mode as keyof typeof TARGETS];
  if (!target) {
    throw new Error(
      `Unknown build mode "${mode}" — use --mode boxoffice or --mode tagline.`
    );
  }

  return {
    ...baseConfig,
    define: {
      // Force React's production build; library mode otherwise ships the
      // __DEV__-branched helpers (same fix as widget-bacon-trail).
      'process.env.NODE_ENV': JSON.stringify('production'),
    },
    build: {
      outDir: path.resolve(__dirname, target.outDir),
      emptyOutDir: true,
      sourcemap: true,
      target: 'es2019',
      lib: {
        entry: path.resolve(__dirname, target.entry),
        name: target.name,
        fileName: () => 'widget.js',
        formats: ['iife'] as const,
      },
      rollupOptions: {
        output: {
          assetFileNames: (info) =>
            info.name && /\.css$/.test(info.name) ? 'widget.css' : '[name][extname]',
          extend: true,
        },
      },
      minify: 'terser' as const,
      terserOptions: {
        compress: {
          drop_console: false,
          passes: 2,
        },
      },
    },
  };
});
