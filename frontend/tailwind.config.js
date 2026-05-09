/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          700: '#1e3a5f',
          800: '#1a2540',
          900: '#0f1729',
          950: '#0a0f1e',
        },
        alert: {
          normal: '#10b981',
          waspada: '#f59e0b',
          siaga: '#f97316',
          darurat: '#ef4444',
        },
        cv: {
          online: '#10b981',
          offline: '#64748b',
          queued: '#3b82f6',
        },
      },
      animation: {
        'pulse-green': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
