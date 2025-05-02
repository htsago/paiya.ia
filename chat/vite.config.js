import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    open: false,
    allowedHosts: ['it-services-team-paiya.gen-ai.software', 'www.gen-ai.software', 'it-services-team-paiya-gcp.gen-ai.software']
  }
})

