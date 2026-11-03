module.exports = {
  content: ["./templates/**/*.html", "./apps/**/*.py", "./static/js/**/*.js"],
  theme: {
    extend: {
      colors: {
        pine: {
          50: "#E8F5EC",
          100: "#D7EEDF",
          700: "#0B592F",
          800: "#0B592F",
          900: "#084522",
        },
        gold: {
          50: "#FBF6E8",
          100: "#F4E7C3",
          500: "#C6A15B",
          600: "#A7843E",
          700: "#8C6A2F",
        },
      },
      fontFamily: {
        sans: ["Hind Siliguri", "Inter", "sans-serif"],
        latin: ["Inter", "Hind Siliguri", "sans-serif"],
      },
      boxShadow: {
        card: "0 10px 30px -18px rgba(8, 69, 34, 0.45)",
      },
    },
  },
  plugins: [],
};
