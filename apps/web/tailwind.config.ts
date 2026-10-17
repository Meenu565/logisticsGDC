import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0c0a09",
          soft: "#1c1917",
          warm: "#292524",
          border: "#2e2a27",
        },
        stone: {
          canvas: "#0c0a09",
          surface: "#141211",
          card: "#1a1816",
          hairline: "#292524",
          "hairline-soft": "#38332f",
          "hairline-strong": "#44403c",
        },
        pastel: {
          mint: "#a7e5d3",
          peach: "#f4c5a8",
          lavender: "#c8b8e0",
          sky: "#a8c8e8",
          rose: "#e8b8c4",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        editorial: ["Waldenburg", "serif"],
      },
      borderRadius: {
        pill: "9999px",
        xl: "16px",
        "2xl": "20px",
        "3xl": "28px",
      },
      boxShadow: {
        soft: "0 12px 40px rgba(0, 0, 0, 0.45)",
        card: "0 4px 20px rgba(0, 0, 0, 0.25)",
        glow: "0 0 35px rgba(200, 184, 224, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;
