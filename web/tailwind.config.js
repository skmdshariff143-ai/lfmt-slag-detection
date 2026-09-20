/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        navy: {
          900: "#0b1329",
          800: "#101d42",
          700: "#1a2e66",
        },
        steel: {
          500: "#64748b",
          400: "#94a3b8",
          300: "#cbd5e1",
        },
        thermal: {
          amber: "#f59e0b",
          cyan: "#06b6d4",
          emerald: "#10b981",
          rose: "#f43f5e",
        }
      },
    },
  },
  plugins: [],
};