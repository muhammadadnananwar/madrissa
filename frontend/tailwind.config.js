/** @type {import('tailwindcss').Config} */
// Palette taken directly from the official UMS crest (logo.svg):
//   royal purple #3B1E6D, deep purple #25104A, light purple #6B45A8, gold #E9BE3B
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#F5F1FB',
          100: '#EAE2F6',
          200: '#D3C3EC',
          300: '#B39ADC',
          400: '#8D6CC6',
          500: '#6B45A8',
          600: '#55348F',
          700: '#3B1E6D',
          800: '#2E1659',
          900: '#25104A',
          950: '#170830',
          DEFAULT: '#3B1E6D',
        },
        gold: {
          50: '#FDF9EB',
          100: '#FAF0C8',
          200: '#F5E191',
          300: '#EFD062',
          400: '#E9BE3B',
          500: '#D4A52A',
          600: '#AE8320',
          700: '#84621C',
          DEFAULT: '#E9BE3B',
        },
        surface: '#F7F8FA',
        ink: '#1C1530',
      },
      fontFamily: {
        // Urdu text automatically falls back to Noto Nastaliq Urdu
        display: ['"Cormorant Garamond"', '"Noto Nastaliq Urdu"', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', '"Noto Nastaliq Urdu"', 'system-ui', 'sans-serif'],
        urdu: ['"Noto Nastaliq Urdu"', 'serif'],
      },
      boxShadow: {
        soft: '0 2px 10px -2px rgba(37, 16, 74, 0.08), 0 8px 24px -8px rgba(37, 16, 74, 0.10)',
        lift: '0 18px 40px -16px rgba(37, 16, 74, 0.35)',
        gold: '0 10px 30px -10px rgba(233, 190, 59, 0.55)',
      },
      backgroundImage: {
        'crest-pattern': "radial-gradient(circle at 1px 1px, rgba(233,190,59,0.18) 1px, transparent 0)",
      },
      keyframes: {
        marquee: { '0%': { transform: 'translateX(0)' }, '100%': { transform: 'translateX(-50%)' } },
      },
      animation: {
        marquee: 'marquee 35s linear infinite',
      },
    },
  },
  plugins: [],
};
