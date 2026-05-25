"use client";

import Link from "next/link";

interface AuthShellProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export function AuthShell({ title, subtitle, children, footer }: AuthShellProps) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.18),_transparent_55%)]" />
      <div className="pointer-events-none absolute -left-24 top-24 h-72 w-72 rounded-full bg-blue-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 bottom-24 h-72 w-72 rounded-full bg-violet-500/10 blur-3xl" />

      <div className="relative mx-auto flex min-h-screen max-w-6xl items-center justify-center px-4 py-10">
        <div className="grid w-full max-w-5xl overflow-hidden rounded-3xl border border-slate-800/80 bg-slate-900/70 shadow-2xl backdrop-blur-xl lg:grid-cols-[1.05fr_1fr]">
          <aside className="hidden flex-col justify-between border-r border-slate-800/80 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 p-10 lg:flex">
            <div>
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-300">
                Quant Platform
              </div>
              <h1 className="text-3xl font-semibold tracking-tight text-white">
                A 股量化分析平台
              </h1>
              <p className="mt-4 max-w-sm text-sm leading-7 text-slate-400">
                数据采集、指标计算、策略回测与风险评估。注册账户后可安全保存你的研究配置与回测记录。
              </p>
            </div>
            <p className="text-xs text-slate-500">
              本平台仅供量化研究与学习，不构成任何投资建议。
            </p>
          </aside>

          <section className="p-6 sm:p-10">
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-white">{title}</h2>
              <p className="mt-2 text-sm text-slate-400">{subtitle}</p>
            </div>
            {children}
            {footer ? <div className="mt-6 text-center text-sm text-slate-400">{footer}</div> : null}
          </section>
        </div>
      </div>

      <div className="absolute left-4 top-4 lg:hidden">
        <Link href="/" className="text-sm font-medium text-slate-400 hover:text-white">
          ← 返回首页
        </Link>
      </div>
    </div>
  );
}
