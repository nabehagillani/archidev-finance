/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0B1220',
          900: '#111A2E',
          800: '#1B2740',
          700: '#293552',
          600: '#3C4A6B',
        },
        paper: '#FAF9F6',
        ledger: {
          50: '#EDF6F1',
          200: '#BFE0CF',
          500: '#1F7A53',
          600: '#186142',
          700: '#124932',
        },
        rust: {
          500: '#B4472B',
          600: '#8F3A24',
        },
        amber: {
          500: '#B8862E',
        },
      },
      fontFamily: {
        serif: ['"Source Serif 4"', 'Georgia', 'serif'],
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
