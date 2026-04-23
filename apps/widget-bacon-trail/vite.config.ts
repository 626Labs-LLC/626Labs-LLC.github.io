import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Build output lands at the hub's root in `/widget-bacon-trail/` so the live URL
// is `https://626labs.dev/widget-bacon-trail/widget.js`. Mirrors the existing
// `sanduhr/` sub-app pattern. Dev mode serves the widget at port 3003 via
// `dev.html` for solo playthroughs.

const OUT_DIR = path.resolve(__dirname, '../../widget-bacon-trail');

export default defineConfig(({ command }) => {
  const baseConfig = {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 3003,
      host: '0.0.0.0',
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: ['./src/test-setup.ts'],
    },
  };

  if (command === 'serve') {
    return baseConfig;
  }

  // Library build — single IIFE bundle + companion CSS. Matches the shape the
  // hub's `index.html` will embed via `<script>` + `<link rel=stylesheet>`.
  return {
    ...baseConfig,
    build: {
      outDir: OUT_DIR,
      emptyOutDir: true,
      sourcemap: true,
      target: 'es2019',
      lib: {
        entry: path.resolve(__dirname, 'src/index.tsx'),
        name: 'BaconTrailWidget',
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
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: false,
        },
      },
    },
  };
});
