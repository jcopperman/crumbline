/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        'crumb': {
          'bg': '#0f0f0f',
          'text': '#e5e5e5',
          'muted': '#999999',
          'accent': {
            'light': '#e0c8b0',
            'medium': '#c37b7b',
            'dark': '#555555',
            'orange': '#FF9052' // Color from the logo
          }
        }
      },
      fontFamily: {
        'serif': ['Playfair Display', 'Georgia', 'serif'],
        'sans': ['Inter', 'Source Sans Pro', 'sans-serif']
      },
      maxWidth: {
        'content': '700px'
      },
      lineHeight: {
        'relaxed': '1.8'
      }
    }
  },
  plugins: []
} 