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
          "blue-20": "rgba(0, 76, 150, 0.2)",
          "yellow-20": "rgba(255, 214, 0, 0.2)",
        },
        confetti: {
          "1": "#FFD600",
          "2": "#FF6B6B",
          "3": "#4ECDC4",
          "4": "#45B7D1",
          "5": "#96CEB4",
          "6": "#FFEAA7",
          "7": "#DDA0DD",
          "8": "#98D8C8",
        },
      },
      fontFamily: {
        sans: ["Open Sans", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 2px 12px rgba(0, 0, 0, 0.08)",
        "card-hover": "0 8px 30px rgba(0, 0, 0, 0.12)",
        elevated: "0 4px 24px rgba(0, 76, 150, 0.15)",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
        "slide-down": "slideDown 0.4s ease-out",
        "pulse-slow": "pulse 3s infinite",
        "bounce-in": "bounceIn 0.5s ease-out",
        "shake": "shake 0.5s ease-in-out",
        "confetti-fall": "confettiFall 2.5s ease-out forwards",
        "toast-in": "toastIn 0.4s ease-out",
        "toast-out": "toastOut 0.3s ease-in forwards",
        "stagger-in": "staggerIn 0.5s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideDown: {
          "0%": { opacity: "0", transform: "translateY(-20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        bounceIn: {
          "0%": { opacity: "0", transform: "scale(0.9)" },
          "50%": { transform: "scale(1.02)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shake: {
          "0%, 100%": { transform: "translateX(0)" },
          "10%, 30%, 50%, 70%, 90%": { transform: "translateX(-4px)" },
          "20%, 40%, 60%, 80%": { transform: "translateX(4px)" },
        },
        confettiFall: {
          "0%": { opacity: "1", transform: "translateY(0) rotate(0deg) scale(1)" },
          "100%": { opacity: "0", transform: "translateY(400px) rotate(720deg) scale(0.5)" },
        },
        toastIn: {
          "0%": { opacity: "0", transform: "translateX(100%) scale(0.9)" },
          "100%": { opacity: "1", transform: "translateX(0) scale(1)" },
        },
        toastOut: {
          "0%": { opacity: "1", transform: "translateX(0) scale(1)" },
          "100%": { opacity: "0", transform: "translateX(100%) scale(0.9)" },
        },
        staggerIn: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
