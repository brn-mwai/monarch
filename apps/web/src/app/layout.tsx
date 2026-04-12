import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";

import { Header } from "@/components/Header";
import { ConvexClientProvider } from "@/lib/convex-provider";
import { ScanProvider } from "@/lib/scan-provider";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Monarch - Neural Processing Scanner",
  description:
    "Monarch uses AI-predicted brain scans and statistical physics to show you whether a piece of content is designed to make you feel before you think.",
  icons: { icon: "/favicon.png" },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} bg-black text-white antialiased`}
      >
        <ClerkProvider
          appearance={{
            baseTheme: dark,
            elements: {
              card: "bg-[#111] border border-white/10",
              formButtonPrimary: "bg-white text-black hover:bg-white/90",
            },
          }}
        >
          <ConvexClientProvider>
            <ScanProvider>
              <Header />
              <main className="pt-16">{children}</main>
            </ScanProvider>
          </ConvexClientProvider>
        </ClerkProvider>
      </body>
    </html>
  );
}
