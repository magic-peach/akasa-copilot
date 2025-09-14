/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f0ff',
          100: '#e5e5ff',
          200: '#d0d0ff',
          300: '#b3b3ff',
          400: '#9999ff',
          500: '#6C63FF',
          600: '#5a52e6',
          700: '#4a42cc',
          800: '#3d35b3',
          900: '#332a99',
        },
        dark: {
          50: '#f8f8f8',
          100: '#e5e5e5',
          200: '#cccccc',
          300: '#b3b3b3',
          400: '#999999',
          500: '#666666',
          600: '#4d4d4d',
          700: '#333333',
          800: '#1a1a1a',
          900: '#121212',
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'neon-glow': 'linear-gradient(135deg, rgba(108, 99, 255, 0.1) 0%, rgba(108, 99, 255, 0.05) 100%)',
      },
      boxShadow: {
        'neon': '0 0 20px rgba(108, 99, 255, 0.5)',
        'neon-lg': '0 0 40px rgba(108, 99, 255, 0.3)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 10px 15px -3px rgba(108, 99, 255, 0.1), 0 4px 6px -2px rgba(108, 99, 255, 0.05)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(108, 99, 255, 0.5)' },
          '100%': { boxShadow: '0 0 30px rgba(108, 99, 255, 0.8)' },
        }
      }
    },
  },
  plugins: [],
  darkMode: 'class',
}