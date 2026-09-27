import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Relative paths so the site works under GitHub Pages' /Carolina-Data-Challenge/ address.
  base: './',
  // The song pool and world map are bundled on purpose (no server needed).
  build: { chunkSizeWarningLimit: 1200 },
})
