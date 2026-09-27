import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Relative paths so the site works under a GitHub Pages sub-address (/DJ-Panda/).
  base: './',
  // The song pool and world map are bundled on purpose (no server needed).
  build: { chunkSizeWarningLimit: 1200 },
})
