import type { Metadata } from "next";
import "./globals.css";
import { Bricolage_Grotesque } from "next/font/google";

const bricolage = Bricolage_Grotesque({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "EduInsight | Automated Tool",
  description: "Ease your process with our automated tool",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link
        rel="stylesheet"
        type="text/css"
        href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/regular/style.css"/>
      </head>
      <body className={bricolage.className}>
      <div className="fixed top-4 left-0 right-0 flex justify-center z-50">
          {/* <FloatingDockDemo /> */}
        </div>
        <main className="flex min-h-screen flex-col items-center justify-center">{children}</main>
      </body>
    </html>
  );
}