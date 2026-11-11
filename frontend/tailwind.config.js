/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    // Flat design: every box shadow utility is disabled.  Depth comes from
    // borders and surface contrast, never from a glow.
    boxShadow: {
      DEFAULT: "none",
    },
    extend: {
      colors: {
        brand: {
          // Deep Charcoal / Slate — application background
          base: "#18181B",
          // Midnight Navy — cards, modals, elevated surfaces
          surface: "#0F172A",
          // Flat borders (no glow)
          edge: "#1E293B",
          "edge-strong": "#334155",
          // Vivid Amber / Yellow — XP progress + primary accents
          accent: "#F59E0B",
          "accent-soft": "#FBBF24",
          "accent-dim": "#B45309",
          // Deep Slate Blue — action buttons + challenge highlights
          action: "#3B82F6",
          "action-dark": "#2563EB",
          "action-soft": "#1D4ED8",
        },
      },
    },
  },
  plugins: [],
};
