"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DateInput, Field, NumberInput, TextInput } from "@/components/ui/Field";
import { ApiError, api } from "@/lib/api";
import { formatPercent } from "@/lib/format";
import type { BacktestTaskListItem } from "@/types";

interface FormState {
  stock_code: string;
  start_date: string;
  end_date: string;
  initial_cash: number;
  short_window: number;
  long_window: number;
  commission_rate: number;
  stamp_tax_rate: number;
  slippage_rate: number;
}

const INITIAL: FormState = {
  stock_code: "600519",
  start_date: "2023-01-01",
  end_date: "2024-12-31",
  initial_cash: 500000,
  short_window: 5,
  long_window: 20,
  commission_rate: 0.0003,
  stamp_tax_rate: 0.001,
  slippage_rate: 0.0005,
};

export default function BacktestPage() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(INITIAL);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<BacktestTaskListItem[]>([]);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function loadHistory() {
    try {
      const resp = await api.listBacktestTasks(20);
      setHistory(resp.items);
    } catch {
      // 失败不致命，忽略
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setRunning(true);
    setError(null);
    try {
      const result = await api.runMaCross({
        stock_code: form.stock_code.trim(),
        start_date: form.start_date,
        end_date: form.end_date,
        initial_cash: form.initial_cash,
        short_window: form.short_window,
        long_window: form.long_window,
        commission_rate: form.commission_rate,
        stamp_tax_rate: form.stamp_tax_rate,
        slippage_rate: form.slippage_rate,
      });
      router.push(`/backtest/${result.task_id}`);
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : String(err);
      setError(msg);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card
        title="MA 双均线回测"
        description="MA(short) 上穿 MA(long) 买入，下穿卖出；单股票全仓"
      >
        <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-3">
          <Field label="股票代码">
            <TextInput
              required
              value={form.stock_code}
              onChange={(e) => update("stock_code", e.target.value)}
              placeholder="600519"
            />
          </Field>
          <Field label="开始日期">
            <DateInput
              required
              value={form.start_date}
              onChange={(e) => update("start_date", e.target.value)}
            />
          </Field>
          <Field label="结束日期">
            <DateInput
              required
              value={form.end_date}
              onChange={(e) => update("end_date", e.target.value)}
            />
          </Field>

          <Field label="初始资金（元）">
            <NumberInput
              min={1000}
              step={1000}
              value={form.initial_cash}
              onChange={(e) => update("initial_cash", Number(e.target.value))}
            />
          </Field>
          <Field label="short window（快线）">
            <NumberInput
              min={1}
              max={120}
              value={form.short_window}
              onChange={(e) => update("short_window", Number(e.target.value))}
            />
          </Field>
          <Field label="long window（慢线）">
            <NumberInput
              min={2}
              max={250}
              value={form.long_window}
              onChange={(e) => update("long_window", Number(e.target.value))}
            />
          </Field>

          <Field label="手续费率" hint="默认 0.0003（万三）">
            <NumberInput
              step={0.0001}
              min={0}
              max={0.01}
              value={form.commission_rate}
              onChange={(e) => update("commission_rate", Number(e.target.value))}
            />
          </Field>
          <Field label="印花税率" hint="仅卖出，默认 0.001（千一）">
            <NumberInput
              step={0.0001}
              min={0}
              max={0.01}
              value={form.stamp_tax_rate}
              onChange={(e) => update("stamp_tax_rate", Number(e.target.value))}
            />
          </Field>
          <Field label="滑点率" hint="买入加 / 卖出减">
            <NumberInput
              step={0.0001}
              min={0}
              max={0.01}
              value={form.slippage_rate}
              onChange={(e) => update("slippage_rate", Number(e.target.value))}
            />
          </Field>

          <div className="md:col-span-3 flex items-center gap-3">
            <Button type="submit" disabled={running}>
              {running ? "运行中..." : "运行回测"}
            </Button>
            {error && <span className="text-sm text-rose-600">{error}</span>}
          </div>
        </form>
      </Card>

      <Card title="最近回测" description="最多展示 20 条历史任务">
        {history.length === 0 ? (
          <div className="text-sm text-neutral-500">暂无任务，运行一次回测后会出现在这里。</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm tabular-nums">
              <thead className="bg-neutral-50 text-left text-xs uppercase tracking-wide text-neutral-500">
                <tr>
                  <th className="px-3 py-2">Task</th>
                  <th className="px-3 py-2">股票</th>
                  <th className="px-3 py-2">区间</th>
                  <th className="px-3 py-2">状态</th>
                  <th className="px-3 py-2">总收益</th>
                  <th className="px-3 py-2">交易次数</th>
                  <th className="px-3 py-2">创建时间</th>
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {history.map((t) => (
                  <tr key={t.task_id} className="border-t border-neutral-100">
                    <td className="px-3 py-2 font-medium">#{t.task_id}</td>
                    <td className="px-3 py-2">{t.stock_code}</td>
                    <td className="px-3 py-2 text-xs text-neutral-500">
                      {t.start_date} ~ {t.end_date}
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={
                          t.status === "success"
                            ? "rounded bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700"
                            : t.status === "failed"
                            ? "rounded bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700"
                            : "rounded bg-neutral-100 px-2 py-0.5 text-xs font-medium text-neutral-700"
                        }
                      >
                        {t.status}
                      </span>
                    </td>
                    <td
                      className={
                        (t.total_return ?? 0) > 0
                          ? "px-3 py-2 text-emerald-600"
                          : (t.total_return ?? 0) < 0
                          ? "px-3 py-2 text-rose-600"
                          : "px-3 py-2 text-neutral-500"
                      }
                    >
                      {formatPercent(t.total_return)}
                    </td>
                    <td className="px-3 py-2">{t.trade_count}</td>
                    <td className="px-3 py-2 text-xs text-neutral-500">
                      {t.created_at.replace("T", " ").slice(0, 19)}
                    </td>
                    <td className="px-3 py-2">
                      <a
                        className="text-xs font-medium text-blue-600 hover:underline"
                        href={`/backtest/${t.task_id}`}
                      >
                        查看 →
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
