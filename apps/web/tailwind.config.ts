import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#101418",
        muted: "#5b6673",
        line: "#d7dde5",
        panel: "#f7f8fa",
        accent: "#0f766e"
      }
    }
  },
  plugins: []
};

export default config;
