"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { BacktestReport } from "@/components/BacktestReport";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Metric } from "@/components/ui/Metric";
import { ApiError, api } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type { BacktestDetailResponse, BacktestReport as ReportData } from "@/types";

export default function BacktestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<BacktestDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 报告状态
  const [report, setReport] = useState<ReportData | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    setReport(null);
    setReportError(null);
    api
      .getBacktest(id)
      .then((resp) => setData(resp))
      .catch((err) => {
        const msg = err instanceof ApiError ? err.detail : String(err);
        setError(msg);
      })
      .finally(() => setLoading(false));
  }, [id]);

  async function onGenerateReport() {
    if (!id) return;
    setReportLoading(true);
    setReportError(null);
    try {
      const resp = await api.getBacktestReport(id);
      setReport(resp);
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : String(err);
      setReportError(msg);
    } finally {
      setReportLoading(false);
    }
  }

  if (loading) {
    return <Card>加载中...</Card>;
  }
  if (error) {
    return (
      <Card>
        <div className="text-sm text-rose-600">加载失败：{error}</div>
        <a className="mt-3 inline-block text-sm text-blue-600 hover:underline" href="/backtest">
          ← 返回回测列表
        </a>
      </Card>
    );
  }
  if (!data) return null;

  const { metrics, trades, equity_curve } = data;

  return (
    <div className="space-y-6">
      <Card
        title={`回测 #${data.task_id} · ${data.stock_code}`}
        description={`${data.start_date} ~ ${data.end_date} · 初始 ${formatCurrency(
          data.initial_cash,
          0,
        )} · short=${(data.params as { short_window?: number }).short_window ?? "-"} / long=${
          (data.params as { long_window?: number }).long_window ?? "-"
        }`}
        actions={
          <span
            className={
              data.status === "success"
                ? "rounded bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700"
                : data.status === "failed"
                ? "rounded bg-rose-50 px-2 py-1 text-xs font-medium text-rose-700"
                : "rounded bg-neutral-100 px-2 py-1 text-xs font-medium text-neutral-700"
            }
          >
            {data.status}
          </span>
        }
      >
        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <Metric label="总收益" value={metrics.total_return} format="percent" signed />
          <Metric label="年化收益" value={metrics.annual_return} format="percent" signed />
          <Metric label="最大回撤" value={metrics.max_drawdown} format="percent" signed />
          <Metric label="夏普比率" value={metrics.sharpe_ratio} format="number" />
          <Metric label="胜率" value={metrics.win_rate} format="percent" />
          <Metric label="交易次数" value={metrics.trade_count} format="int" />
        </div>
      </Card>

      <Card
        title="智能分析报告"
        description={
          report
            ? `${report.provider} · 共 ${report.sections.length} 个分析维度`
            : "第一版基于回测指标按规则生成中文报告，不调用大模型"
        }
        actions={
          <Button
            type="button"
            variant={report ? "secondary" : "primary"}
            onClick={onGenerateReport}
            disabled={reportLoading}
          >
            {reportLoading ? "生成中..." : report ? "重新生成" : "生成报告"}
          </Button>
        }
      >
        {reportError && (
          <div className="mb-3 rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            生成失败：{reportError}
          </div>
        )}
        {report ? (
          <BacktestReport report={report} />
        ) : (
          <div className="rounded-lg border border-dashed border-neutral-300 bg-neutral-50 p-6 text-center text-sm text-neutral-500">
            点击右上方「生成报告」获取本次回测的中文分析（包含收益、回撤、过拟合提醒等）。
          </div>
        )}
      </Card>

      <Card title="净值曲线" description="按 trade_date 升序，▲ 买入 / ● 卖出">
        {equity_curve.length === 0 ? (
          <div className="text-sm text-neutral-500">暂无净值数据</div>
        ) : (
          <EquityCurveChart curve={equity_curve} trades={trades} />
        )}
      </Card>

      <Card title="交易明细" description={`共 ${trades.length} 条`}>
        {trades.length === 0 ? (
          <div className="text-sm text-neutral-500">本次回测未触发任何交易</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm tabular-nums">
              <thead className="bg-neutral-50 text-left text-xs uppercase tracking-wide text-neutral-500">
                <tr>
                  <th className="px-3 py-2">日期</th>
                  <th className="px-3 py-2">动作</th>
                  <th className="px-3 py-2">价格</th>
                  <th className="px-3 py-2">数量</th>
                  <th className="px-3 py-2">成交后现金</th>
                  <th className="px-3 py-2">成交后持仓</th>
                  <th className="px-3 py-2">原因</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((t, i) => (
                  <tr key={`${t.trade_date}-${i}`} className="border-t border-neutral-100">
                    <td className="px-3 py-2">{t.trade_date}</td>
                    <td className="px-3 py-2">
                      <span
                        className={
                          t.action === "BUY"
                            ? "rounded bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700"
                            : "rounded bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700"
                        }
                      >
                        {t.action}
                      </span>
                    </td>
                    <td className="px-3 py-2">{formatNumber(t.price, 3)}</td>
                    <td className="px-3 py-2">{t.quantity.toLocaleString()}</td>
                    <td className="px-3 py-2">{formatCurrency(t.cash_after)}</td>
                    <td className="px-3 py-2">{t.position_after.toLocaleString()}</td>
                    <td className="px-3 py-2 text-xs text-neutral-500">{t.reason ?? "—"}</td>
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
