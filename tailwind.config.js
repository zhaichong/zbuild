/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './mini.html', './src/**/*.{ts,vue}'],
  theme: {
    extend: {
      colors: {
        'bg-base': 'var(--color-bg-base)',
        surface: 'var(--color-surface)',
        primary: 'var(--color-primary)',
        'primary-light': 'var(--color-primary-light)',
        success: 'var(--color-success)',
        'success-light': 'var(--color-success-light)',
        error: 'var(--color-error)',
        'error-light': 'var(--color-error-light)',
        warning: 'var(--color-warning)',
        'warning-light': 'var(--color-warning-light)',
        terminal: 'var(--color-terminal)',
        border: 'var(--color-border)',
        'border-light': 'var(--color-border-light)',
        'text-1': 'var(--color-text-1)',
        'text-2': 'var(--color-text-2)',
        'text-3': 'var(--color-text-3)',
      },
    },
  },
  plugins: [],
}
