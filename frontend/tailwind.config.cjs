/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: '#080c14',
          card: '#0f172a',
          cardHover: '#1e293b',
          border: '#1e293b',
          borderLight: '#334155',
          cyan: '#00f2fe',
          blue: '#38bdf8',
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#ef4444',
          purple: '#a855f7'
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif']
      }
    },
  },
  plugins: [],
};
