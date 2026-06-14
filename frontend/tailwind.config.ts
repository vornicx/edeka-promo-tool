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
        glass: {
          white: "rgba(255, 255, 255, 0.6)",
          "white-heavy": "rgba(255, 255, 255, 0.8)",
          border: "rgba(255, 255, 255, 0.3)",
          "border-light": "rgba(255, 255, 255, 0.15)",
        },
      },
      fontFamily: {
        sans: ["Open Sans", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 2px 12px rgba(0, 0, 0, 0.08)",
        "card-hover": "0 8px 30px rgba(0, 0, 0, 0.12)",
        elevated: "0 4px 24px rgba(0, 76, 150, 0.15)",
        glass: "0 8px 32px rgba(0, 0, 0, 0.08)",
        "glass-lg": "0 16px 48px rgba(0, 0, 0, 0.12)",
        "glass-blue": "0 8px 32px rgba(0, 76, 150, 0.12)",
        inner: "inset 0 2px 4px rgba(0, 0, 0, 0.04)",
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
        "blob-float": "blobFloat 20s ease-in-out infinite",
        "blob-float-2": "blobFloat2 25s ease-in-out infinite",
        "blob-float-3": "blobFloat3 18s ease-in-out infinite",
        "glass-shimmer": "glassShimmer 3s ease-in-out infinite",
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
        blobFloat: {
          "0%, 100%": { transform: "translate(0, 0) scale(1) rotate(0deg)" },
          "25%": { transform: "translate(30px, -40px) scale(1.1) rotate(5deg)" },
          "50%": { transform: "translate(-20px, 20px) scale(0.95) rotate(-3deg)" },
          "75%": { transform: "translate(40px, 30px) scale(1.05) rotate(4deg)" },
        },
        blobFloat2: {
          "0%, 100%": { transform: "translate(0, 0) scale(1) rotate(0deg)" },
          "33%": { transform: "translate(-50px, 30px) scale(1.15) rotate(-8deg)" },
          "66%": { transform: "translate(30px, -50px) scale(0.9) rotate(6deg)" },
        },
        blobFloat3: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "50%": { transform: "translate(40px, 40px) scale(1.2)" },
        },
        glassShimmer: {
          "0%, 100%": { opacity: "0.5" },
          "50%": { opacity: "0.8" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
