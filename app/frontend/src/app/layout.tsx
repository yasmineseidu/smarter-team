import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Smarter Team",
  description: "Multi-Agent AI Agency Automation",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
