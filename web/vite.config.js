import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // The song pool and world map are bundled on purpose (no server needed).
  build: { chunkSizeWarningLimit: 1200 },
})
