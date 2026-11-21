import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// In development the Django API (and uploaded media) are proxied, so no CORS setup is needed.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const backend = env.BACKEND_URL || 'http://localhost:8000';
  return {
    plugins: [react()],
    server: {
      port: 4321,
      proxy: {
        '/api': { target: backend, changeOrigin: true },
        '/media': { target: backend, changeOrigin: true },
      },
    },
    preview: { port: 4321 },
    build: { chunkSizeWarningLimit: 900 },
  };
});
