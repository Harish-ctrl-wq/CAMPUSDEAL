/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: { 950: "#0d1b2a", 900: "#14283b", 800: "#1d3850" },
        mint: { 50: "#effaf4", 100: "#d9f3e4", 500: "#35a66f", 600: "#258758" },
      },
      boxShadow: { card: "0 8px 30px rgba(13, 27, 42, .06)" },
    },
  },
  plugins: [],
};
