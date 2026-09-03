import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI 聊天助手",
  description: "基于 Next.js + Vercel AI SDK 的 AI 聊天应用",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
