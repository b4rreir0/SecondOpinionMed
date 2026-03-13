/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.{html,js}",
    "./apps/**/*.{html,js}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: "#1392ec",
        "primary-dark": "#0e7ccb",
        "primary-light": "rgba(19, 146, 236, 0.1)",
        "background-light": "#f6f7f8",
        "background-dark": "#101a22",
        "surface-light": "#ffffff",
        "surface-dark": "#182430",
        "border-light": "#e2e8f0",
        "border-dark": "#2d3b48",
        success: "#10b981",
        warning: "#f59e0b",
        danger: "#ef4444",
        info: "#3b82f6",
        urgent: "#f87171",
        pending: "#fbbf24",
        completed: "#34d399",
      },
      fontFamily: {
        display: ["Manrope", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
