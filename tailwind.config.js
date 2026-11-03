module.exports = {
  content: ["./templates/**/*.html", "./apps/**/*.py"],
  theme: {
    extend: {
      colors: {
        pine: {
          50: "#f2f8f4",
          100: "#dceee3",
          700: "#1f6b45",
          800: "#14532d",
          900: "#0f3d2e",
        },
      },
      fontFamily: {
        sans: ["Hind Siliguri", "Inter", "sans-serif"],
        latin: ["Inter", "Hind Siliguri", "sans-serif"],
      },
    },
  },
  plugins: [],
};
