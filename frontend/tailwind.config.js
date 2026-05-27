/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        display: ["'Bricolage Grotesque'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      colors: {
        background: "#030712", // Very dark blue/black
        surface: "#0B1120",
        surfaceAlt: "#111827",
        primary: "#3B82F6", // Glowing blue
        primaryGlow: "#60A5FA",
        secondary: "#8B5CF6",
        accent: "#06B6D4", // Cyan
        alert: "#EF4444",
        warning: "#F59E0B",
        success: "#10B981",
        mint: "#2DD4BF", // Mint Green
        gold: "#FBBF24", // Gold Yellow
        textMain: "#F8FAFC",
        textSub: "#94A3B8"
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 10px rgba(59, 130, 246, 0.5)' },
          '100%': { boxShadow: '0 0 25px rgba(59, 130, 246, 0.8)' },
        }
      }
    }
  },
  plugins: []
};
