import type { Metadata } from "next";

import { MainShell } from "@/components/MainShell";
import "./globals.css";

export const metadata: Metadata = {
  title: "A 股量化分析平台",
  description: "数据采集 / 指标计算 / 策略回测 / 风险评估 一站式平台",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-neutral-50">
        <MainShell>{children}</MainShell>
      </body>
    </html>
  );
}
