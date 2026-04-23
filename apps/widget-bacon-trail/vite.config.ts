import path from 'node:path';
import fs from 'node:fs';
import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';

// Build output lands at the hub's root in `/widget-bacon-trail/` so the live URL
// is `https://626labs.dev/widget-bacon-trail/widget.js`. Mirrors the existing
// `sanduhr/` sub-app pattern. Dev mode serves the widget at port 3003 via
// `dev.html` for solo playthroughs.

const OUT_DIR = path.resolve(__dirname, '../../widget-bacon-trail');
const HUB_ROOT = path.resolve(__dirname, '../..');

// Dev-server middleware: the widget fetches shards from
// `/widget-bacon-trail/data/birthdays/MM-DD.json` at runtime (matches the
// production URL served by GitHub Pages). During `vite dev`, this plugin
// shims that path by reading directly from the hub repo's
// `widget-bacon-trail/data/birthdays/` directory.
function serveHubShards(): Plugin {
  return {
    name: 'widget-bacon-trail:serve-hub-shards',
    configureServer(server) {
      server.middlewares.use('/widget-bacon-trail/data/birthdays', (req, res, next) => {
        if (!req.url) return next();
        const filePath = path.join(HUB_ROOT, 'widget-bacon-trail/data/birthdays', req.url);
        if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
          return next();
        }
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Cache-Control', 'no-cache');
        fs.createReadStream(filePath).pipe(res);
      });
    },
  };
}

export default defineConfig(({ command }) => {
  const baseConfig = {
    plugins: [react(), serveHubShards()],
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
    define: {
      // Force React's production build. Vite's library mode otherwise ships
      // React's __DEV__-branched dev helpers, blowing past the 150 KB gz
      // budget.
      'process.env.NODE_ENV': JSON.stringify('production'),
    },
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
          passes: 2,
        },
      },
    },
  };
});
