/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        'btbg-dark': '#1a1a2e',
        'btbg-darker': '#16213e',
        'btbg-accent': '#0f3460',
        'btbg-highlight': '#e94560',
      },
    },
  },
  plugins: [],
};
