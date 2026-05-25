"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, TextInput } from "@/components/ui/Field";

const ENTRIES: Array<{ href: string; title: string; description: string }> = [
  {
    href: "/stocks/600519",
    title: "股票查询",
    description: "查看 K 线、MA 均线、最近行情；输入股票代码可切换。",
  },
  {
    href: "/backtest",
    title: "策略回测",
    description: "MA 双均线策略：金叉买、死叉卖；输出收益、回撤、胜率等指标。",
  },
  {
    href: "/data",
    title: "数据管理",
    description: "通过 akshare 同步指定股票指定区间的日线，自动去重 / 增量。",
  },
];

const FLOW: Array<{ step: string; detail: string }> = [
  { step: "数据采集", detail: "akshare 拉取 → MySQL upsert，自动去重" },
  { step: "指标计算", detail: "MA / RSI / MACD 实时计算，不入库" },
  { step: "策略回测", detail: "自研轻量引擎，避免未来函数，含费用 / 滑点" },
  { step: "风险评估", detail: "总收益 / 年化 / 最大回撤 / 夏普 / 胜率" },
];

export default function HomePage() {
  const router = useRouter();
  const [code, setCode] = useState("600519");

  function onJump(e: React.FormEvent) {
    e.preventDefault();
    const v = code.trim();
    if (v) router.push(`/stocks/${v}`);
  }

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold text-neutral-900">A 股量化分析平台</h1>
        <p className="text-neutral-600">
          一站式覆盖「数据 → 指标 → 策略 → 风险」全链路，第一版聚焦单股票 MA 双均线回测。
        </p>
      </header>

      <Card title="快捷查股" description="输入股票代码（不带前缀，如 600519、000001）">
        <form onSubmit={onJump} className="flex items-end gap-3">
          <Field label="股票代码" htmlFor="home-code" className="flex-1 max-w-xs">
            <TextInput
              id="home-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="600519"
              maxLength={20}
            />
          </Field>
          <Button type="submit">查看 →</Button>
        </form>
      </Card>

      <section className="grid gap-4 sm:grid-cols-3">
        {ENTRIES.map((entry) => (
          <a
            key={entry.href}
            href={entry.href}
            className="group rounded-xl border border-neutral-200 bg-white p-5 shadow-sm transition hover:border-blue-300 hover:shadow-md"
          >
            <div className="text-sm font-medium text-blue-600">{entry.title}</div>
            <p className="mt-2 text-sm text-neutral-600">{entry.description}</p>
            <span className="mt-4 inline-block text-xs font-medium text-neutral-400 group-hover:text-blue-600">
              进入 →
            </span>
          </a>
        ))}
      </section>

      <Card title="平台流程" description="第一版的执行链路">
        <ol className="grid gap-3 sm:grid-cols-4">
          {FLOW.map((step, i) => (
            <li
              key={step.step}
              className="rounded-lg bg-neutral-50 p-4 text-sm"
            >
              <div className="text-xs font-semibold uppercase tracking-wide text-blue-600">
                Step {i + 1}
              </div>
              <div className="mt-1 font-medium text-neutral-900">{step.step}</div>
              <div className="mt-1 text-neutral-600">{step.detail}</div>
            </li>
          ))}
        </ol>
      </Card>
    </div>
  );
}
