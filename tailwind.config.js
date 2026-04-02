/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        'clinical': {
          50: '#f0f4ff',
          100: '#e0e9ff',
          200: '#c7d6fe',
          300: '#a4b8fc',
          400: '#818cf8',
          500: '#1b3a6b',
          600: '#162f57',
          700: '#112545',
          800: '#0d1b33',
          900: '#091222',
        },
        'navy': {
          50: '#f0f3ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#6366f1',
          500: '#1e3a5f',
          600: '#1a3353',
          700: '#152b47',
          800: '#10223b',
          900: '#0b1a2f',
        },
        'teal': {
          50: '#e6fffa',
          100: '#b2f5ea',
          200: '#81e6d9',
          300: '#4fd1c5',
          400: '#38b2ac',
          500: '#2c9f93',
          600: '#1a7a6f',
        },
        'sidebar': '#0f1d40',
        'sidebar-hover': '#1a2d5a',
        'accent-blue': '#2563eb',
        'accent-teal': '#0d9488',
        'light-bg': '#f5f7fb',
        'card-border': '#e2e8f0',
        'label-color': '#374151',
        'input-bg': '#f8fafc',
        'input-border': '#d1d5db',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.05)',
        'card-hover': '0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05)',
        'sidebar': '2px 0 8px rgb(0 0 0 / 0.1)',
      },
    },
  },
  plugins: [],
}
