/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './mini.html', './src/**/*.{ts,vue}'],
  theme: {
    extend: {
      colors: {
        'bg-base': 'var(--color-bg-base)',
        surface: 'var(--color-surface)',
        primary: 'var(--color-primary)',
        success: 'var(--color-success)',
        error: 'var(--color-error)',
        warning: 'var(--color-warning)',
        terminal: 'var(--color-terminal)',
      },
    },
  },
  plugins: [],
}
