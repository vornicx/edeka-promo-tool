import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        edeka: {
          blue: "#004C96",
          yellow: "#FFD600",
          darkblue: "#003366",
          lightblue: "#E8F0FE",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        pill: "9999px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04)",
        elevated: "0 16px 40px rgba(0,76,150,0.14)",
        brand: "0 10px 24px rgba(0,76,150,0.18)",
        modal: "0 20px 60px rgba(0,0,0,0.12)",
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.25s ease-out",
        "scale-in": "scaleIn 0.2s ease-out",
        "shake": "shake 0.3s ease-in-out",
        "confetti-fall": "confettiFall 2s ease-out forwards",
        "toast-in": "toastIn 0.2s ease-out",
        "toast-out": "toastOut 0.2s ease-in forwards",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.96)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shake: {
          "0%,100%": { transform: "translateX(0)" },
          "25%": { transform: "translateX(-3px)" },
          "75%": { transform: "translateX(3px)" },
        },
        confettiFall: {
          "0%": { opacity: "1", transform: "translateY(0) rotate(0deg)" },
          "100%": { opacity: "0", transform: "translateY(300px) rotate(720deg)" },
        },
        toastIn: {
          "0%": { opacity: "0", transform: "translateY(-8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        toastOut: {
          "0%": { opacity: "1" },
          "100%": { opacity: "0", transform: "translateY(-8px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
