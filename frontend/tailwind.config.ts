import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "rgb(var(--tp-canvas) / <alpha-value>)",
        surface: {
          1: "rgb(var(--tp-surface-1) / <alpha-value>)",
          2: "rgb(var(--tp-surface-2) / <alpha-value>)",
          3: "rgb(var(--tp-surface-3) / <alpha-value>)",
          4: "rgb(var(--tp-surface-4) / <alpha-value>)",
        },
        hairline: {
          DEFAULT: "rgb(var(--tp-hairline) / <alpha-value>)",
          strong: "rgb(var(--tp-hairline-strong) / <alpha-value>)",
          tertiary: "rgb(var(--tp-hairline-tertiary) / <alpha-value>)",
        },
        ink: {
          DEFAULT: "rgb(var(--tp-ink) / <alpha-value>)",
          muted: "rgb(var(--tp-ink-muted) / <alpha-value>)",
          subtle: "rgb(var(--tp-ink-subtle) / <alpha-value>)",
          tertiary: "rgb(var(--tp-ink-tertiary) / <alpha-value>)",
        },
        primary: {
          DEFAULT: "rgb(var(--tp-primary) / <alpha-value>)",
          hover: "rgb(var(--tp-primary-hover) / <alpha-value>)",
          focus: "rgb(var(--tp-primary-focus) / <alpha-value>)",
        },
        "on-primary": "rgb(var(--tp-on-primary) / <alpha-value>)",
        success: "rgb(var(--tp-success) / <alpha-value>)",
        "brand-secure": "rgb(var(--tp-brand-secure) / <alpha-value>)",
        danger: "rgb(var(--tp-danger) / <alpha-value>)",
        warning: "rgb(var(--tp-warning) / <alpha-value>)",
      },
      fontFamily: {
        display: ["Inter", "SF Pro Display", "-apple-system", "system-ui", "Segoe UI", "Roboto", "sans-serif"],
        text: ["Inter", "SF Pro Display", "-apple-system", "system-ui", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "Geist Mono", "ui-monospace", "SF Mono", "Menlo", "monospace"],
      },
      fontSize: {
        "display-xl": ["80px", { lineHeight: "1.05", letterSpacing: "-3px", fontWeight: "600" }],
        "display-lg": ["56px", { lineHeight: "1.10", letterSpacing: "-1.8px", fontWeight: "600" }],
        "display-md": ["40px", { lineHeight: "1.15", letterSpacing: "-1px", fontWeight: "600" }],
        "headline": ["28px", { lineHeight: "1.20", letterSpacing: "-0.6px", fontWeight: "600" }],
        "card-title": ["22px", { lineHeight: "1.25", letterSpacing: "-0.4px", fontWeight: "500" }],
        "subhead": ["20px", { lineHeight: "1.40", letterSpacing: "-0.2px", fontWeight: "400" }],
        "body-lg": ["18px", { lineHeight: "1.50", letterSpacing: "-0.1px", fontWeight: "400" }],
        "body": ["16px", { lineHeight: "1.50", letterSpacing: "-0.05px", fontWeight: "400" }],
        "body-sm": ["14px", { lineHeight: "1.50", letterSpacing: "0", fontWeight: "400" }],
        "caption": ["12px", { lineHeight: "1.40", letterSpacing: "0", fontWeight: "400" }],
        "button": ["14px", { lineHeight: "1.20", letterSpacing: "0", fontWeight: "500" }],
        "eyebrow": ["13px", { lineHeight: "1.30", letterSpacing: "0.4px", fontWeight: "500" }],
        "mono": ["13px", { lineHeight: "1.50", letterSpacing: "0", fontWeight: "400" }],
      },
      borderRadius: {
        "xs": "4px",
        "sm": "6px",
        "md": "8px",
        "lg": "12px",
        "xl": "16px",
        "xxl": "24px",
        "pill": "9999px",
      },
      spacing: {
        "xxs": "4px",
        "xs": "8px",
        "sm": "12px",
        "md": "16px",
        "lg": "24px",
        "xl": "32px",
        "xxl": "48px",
        "section": "96px",
      },
      maxWidth: {
        "content": "1280px",
      },
      boxShadow: {
        "none": "none",
      },
    },
  },
  plugins: [],
}

export default config
