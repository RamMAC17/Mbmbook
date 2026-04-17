import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://10.10.13.242:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://10.10.13.242:8000',
        ws: true,
      },
    },
  },
})
