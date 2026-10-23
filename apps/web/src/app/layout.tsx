import type { Metadata, Viewport } from "next";
import { Inter, Noto_Sans_Bengali, Space_Grotesk } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";

import { Providers } from "./providers";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const notoBengali = Noto_Sans_Bengali({
  subsets: ["bengali"],
  variable: "--font-bengali",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Chowkidar — See the risk. Approve the fix.",
    template: "%s · Chowkidar",
  },
  description:
    "Agentic compliance risk intelligence for export supply chains. Monitor regulatory and supplier signals, prioritize evidence-backed risks, and approve remediation with a human in the loop.",
  applicationName: "Chowkidar",
  authors: [{ name: "JU_StackMind" }],
  keywords: [
    "compliance",
    "supply chain",
    "risk intelligence",
    "CSDDD",
    "UFLPA",
    "Bangladesh",
    "RMG",
  ],
};

export const viewport: Viewport = {
  themeColor: "#060a12",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html
      lang={locale}
      className={`${inter.variable} ${spaceGrotesk.variable} ${notoBengali.variable} dark`}
      suppressHydrationWarning
    >
      <body className={locale === "bn" ? "bengali" : undefined}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <Providers>{children}</Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
