"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { KLineChart } from "@/components/charts/KLineChart";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DateInput, Field, TextInput } from "@/components/ui/Field";
import { ApiError, api } from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";
import type { DailyResponse } from "@/types";

function defaultRange() {
  const today = new Date();
  const start = new Date();
  start.setFullYear(today.getFullYear() - 1);
  return {
    start: start.toISOString().slice(0, 10),
    end: today.toISOString().slice(0, 10),
  };
}

export default function StockDetailPage() {
  const router = useRouter();
  const { code } = useParams<{ code: string }>();
  const range = defaultRange();

  const [searchCode, setSearchCode] = useState(code);
  const [startDate, setStartDate] = useState(range.start);
  const [endDate, setEndDate] = useState(range.end);
  const [data, setData] = useState<DailyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  async function load(c: string, s: string, e: string) {
    setLoading(true);
    setError(null);
    setSyncMessage(null);
    try {
      const resp = await api.getDaily(c, {
        start_date: s,
        end_date: e,
        indicators: true,
        limit: 5000,
      });
      setData(resp);
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : String(err);
      setError(msg);
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (code) {
      setSearchCode(code);
      load(code, startDate, endDate);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code]);

  function onSwitch(e: React.FormEvent) {
    e.preventDefault();
    const v = searchCode.trim();
    if (!v) return;
    if (v !== code) {
      router.push(`/stocks/${v}`);
    } else {
      load(v, startDate, endDate);
    }
  }

  function onApplyRange(e: React.FormEvent) {
    e.preventDefault();
    if (code) load(code, startDate, endDate);
  }

  async function syncCurrentRange() {
    const c = (code ?? searchCode).trim();
    if (!c || !startDate || !endDate) return;
    setSyncing(true);
    setError(null);
    setSyncMessage(null);
    try {
      const resp = await api.syncDaily({
        stock_code: c,
        start_date: startDate,
        end_date: endDate,
        adjust: "",
      });
      setSyncMessage(`已成功同步 ${resp.fetched.toLocaleString()} 条日线数据`);
      await load(c, startDate, endDate);
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : String(err);
      setError(msg);
      setData(null);
    } finally {
      setSyncing(false);
    }
  }

  const items = data?.items ?? [];
  const recent = [...items].slice(-20).reverse();

  return (
    <div className="space-y-6">
      <Card title="股票详情" description="支持切换代码与时间区间">
        <form onSubmit={onSwitch} className="flex flex-wrap items-end gap-3">
          <Field label="股票代码" htmlFor="code" className="w-40">
            <TextInput
              id="code"
              value={searchCode}
              onChange={(e) => setSearchCode(e.target.value)}
              placeholder="600519"
            />
          </Field>
          <Button type="submit" variant="secondary">
            切换
          </Button>
        </form>
        <form onSubmit={onApplyRange} className="mt-4 flex flex-wrap items-end gap-3">
          <Field label="开始日期" htmlFor="start" className="w-44">
            <DateInput id="start" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </Field>
          <Field label="结束日期" htmlFor="end" className="w-44">
            <DateInput id="end" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </Field>
          <Button type="submit" disabled={loading}>
            {loading ? "加载中..." : "刷新"}
          </Button>
        </form>
      </Card>

      {error && (
        <Card>
          <div className="text-sm text-rose-600">加载失败：{error}</div>
          <div className="mt-2 text-xs text-neutral-500">
            提示：如果是首次访问，请先到「数据管理」同步该股票的日线数据。
          </div>
        </Card>
      )}

      {!error && data && items.length > 0 && (
        <>
          <Card
            title={`${code} K 线（含 MA5 / MA10 / MA20）`}
            description={`共 ${data.count} 行，区间 ${data.start_date ?? "-"} ~ ${data.end_date ?? "-"}`}
          >
            <KLineChart items={items} maLines={[5, 10, 20]} />
          </Card>

          <Card title="最近 20 个交易日" description="按 trade_date 倒序">
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm tabular-nums">
                <thead className="bg-neutral-50 text-left text-xs uppercase tracking-wide text-neutral-500">
                  <tr>
                    <th className="px-3 py-2">日期</th>
                    <th className="px-3 py-2">开</th>
                    <th className="px-3 py-2">高</th>
                    <th className="px-3 py-2">低</th>
                    <th className="px-3 py-2">收</th>
                    <th className="px-3 py-2">涨跌幅</th>
                    <th className="px-3 py-2">成交量(手)</th>
                    <th className="px-3 py-2">MA5</th>
                    <th className="px-3 py-2">MA20</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((it) => (
                    <tr key={it.trade_date} className="border-t border-neutral-100">
                      <td className="px-3 py-2">{it.trade_date}</td>
                      <td className="px-3 py-2">{formatNumber(it.open, 3)}</td>
                      <td className="px-3 py-2">{formatNumber(it.high, 3)}</td>
                      <td className="px-3 py-2">{formatNumber(it.low, 3)}</td>
                      <td className="px-3 py-2 font-medium">{formatNumber(it.close, 3)}</td>
                      <td
                        className={
                          (it.pct_change ?? 0) > 0
                            ? "px-3 py-2 text-rose-600"
                            : (it.pct_change ?? 0) < 0
                            ? "px-3 py-2 text-emerald-600"
                            : "px-3 py-2 text-neutral-500"
                        }
                      >
                        {it.pct_change === null || it.pct_change === undefined
                          ? "—"
                          : `${(it.pct_change as number).toFixed(2)}%`}
                      </td>
                      <td className="px-3 py-2">{it.volume.toLocaleString()}</td>
                      <td className="px-3 py-2">{formatNumber(it.ma5 ?? null, 3)}</td>
                      <td className="px-3 py-2">{formatNumber(it.ma20 ?? null, 3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}

      {!error && data && items.length === 0 && (
        <Card title="暂无本地数据">
          <div className="text-sm text-neutral-600">
            未找到 <span className="font-medium text-neutral-900">{code}</span> 在{" "}
            <span className="tabular-nums">
              {startDate} ~ {endDate}
            </span>{" "}
            区间内的日线。可从 akshare 拉取并写入本地数据库后展示 K 线与指标。
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button type="button" onClick={syncCurrentRange} disabled={syncing || loading}>
              {syncing ? "同步中（请稍候）..." : "同步当前区间数据"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => router.push("/data")}
              disabled={syncing}
            >
              去数据管理
            </Button>
          </div>
          {syncMessage && (
            <div className="mt-3 text-sm text-emerald-700">{syncMessage}</div>
          )}
        </Card>
      )}
    </div>
  );
}
