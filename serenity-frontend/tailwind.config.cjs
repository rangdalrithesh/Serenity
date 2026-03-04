/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Poppins', 'system-ui', 'sans-serif'],
      },
      colors: {
        sky: {
          serenity: '#7CC6FE',
        },
        lavender: {
          serenity: '#C3B6FF',
        },
        peach: {
          serenity: '#FFB38A',
        },
        teal: {
          serenity: '#6ED3CF',
        },
      },
      boxShadow: {
        soft: '0 18px 45px rgba(0,0,0,0.08)',
      },
      backgroundImage: {
        'serenity-gradient':
          'radial-gradient(circle at top left, #7CC6FE 0, transparent 55%), radial-gradient(circle at top right, #C3B6FF 0, transparent 55%), radial-gradient(circle at bottom, #FFB38A 0, transparent 55%)',
        'serenity-glass':
          'linear-gradient(135deg, rgba(255,255,255,0.28), rgba(255,255,255,0.12))',
      },
    },
  },
  plugins: [],
};

