import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// In development, calls to /api go to the Python backend on port 8000.
// VITE_BASE is set by the GitHub Pages workflow (site lives under /<repo>/); locally it stays '/'.
export default defineConfig(({ mode }) => ({
  base: loadEnv(mode, '.', '').VITE_BASE || '/',
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://localhost:8000' } },
}));
