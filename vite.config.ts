import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  base: './',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        mini: resolve(__dirname, 'mini.html'),
        setup: resolve(__dirname, 'setup.html'),
      },
    },
  },
  css: {
    postcss: './postcss.config.js',
  },
})
