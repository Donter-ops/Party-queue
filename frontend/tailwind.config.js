/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        cream: "#f7f1e3",
        vinyl: "#1f1d36",
        coral: "#ff7f50",
        mint: "#8dd3c7",
        gold: "#f2c14e",
      },
      fontFamily: {
        sans: ["Space Grotesk", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        party: "0 24px 80px rgba(31, 29, 54, 0.18)",
      },
    },
  },
  plugins: [],
};
