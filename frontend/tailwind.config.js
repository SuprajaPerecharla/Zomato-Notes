/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#fff5f0",
          100: "#ffe8dd",
          200: "#ffc9b0",
          300: "#ffa07a",
          400: "#ff6b35",
          500: "#e8430a",
          600: "#c23608",
          700: "#9c2c06",
          800: "#7a2208",
          900: "#5c1a06",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};
