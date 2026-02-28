// ESLint config for JS audit and cleanup
export default [
  {
    files: ["static/js/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
    },
    rules: {
      "no-unused-vars": "warn",
      "no-console": "warn",
      "no-debugger": "warn",
      "no-empty": "warn",
      "no-unreachable": "warn",
      "no-duplicate-imports": "warn",
      "no-var": "error",
      "prefer-const": "warn",
      "eqeqeq": "warn",
      "curly": "warn",
      "semi": ["warn", "always"],
      "quotes": ["warn", "single"],
    },
  },
];