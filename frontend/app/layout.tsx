import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { Providers } from "@/components/providers"
import "./theme-vars.css"
import "./globals.css"

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

export const metadata: Metadata = {
  title: "Traceplane Hub",
  description: "Telemetry-first AI agent observability — traces, costs, and health from real SDK data",
  icons: {
    icon: "/traceplane-icon-32.png",
    apple: "/traceplane-icon-180.png",
  },
}

const themeInitScript = `
  (function () {
    try {
      var root = document.documentElement;
      var t = localStorage.getItem('traceplane-theme') || 'dark';
      root.setAttribute('data-theme', t);
      root.style.colorScheme = t;
      if (t === 'dark') {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    } catch (e) {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.classList.add('dark');
    }
  })();
`

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className={`${inter.className} bg-canvas text-ink font-text min-h-screen antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}