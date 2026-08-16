import type { Metadata } from "next";
import "./local-fonts.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "偉人チャット",
  description: "偉人のペルソナと対話できるアプリ",
};

const RootLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => {
  return (
    <html lang="ja" className="h-full antialiased">
      <body className="h-full flex flex-col">{children}</body>
    </html>
  );
};

export default RootLayout;
