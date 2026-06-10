import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VenueOps Agent",
  description: "AI operations copilot for retail and event venues"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
