"use client";

import { useEffect, useMemo, useRef } from "react";
import * as echarts from "echarts";

import type { BacktestTrade, EquityPoint } from "@/types";

interface EquityCurveChartProps {
  curve: EquityPoint[];
  trades?: BacktestTrade[];
  height?: number;
}

export function EquityCurveChart({ curve, trades = [], height = 360 }: EquityCurveChartProps) {
  const ref = useRef<HTMLDivElement | null>(null);

  const option = useMemo(() => buildOption(curve, trades), [curve, trades]);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    chart.setOption(option);

    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.dispose();
    };
  }, [option]);

  return <div ref={ref} className="w-full" style={{ height }} />;
}

function buildOption(
  curve: EquityPoint[],
  trades: BacktestTrade[],
): echarts.EChartsOption {
  const dates = curve.map((p) => p.trade_date);
  const equity = curve.map((p) => p.equity);

  // 把 trades 标在曲线上：BUY 红圆 / SELL 绿圆
  const dateToEquity = new Map(curve.map((p) => [p.trade_date, p.equity]));
  const markPoints = trades
    .map((t) => {
      const eq = dateToEquity.get(t.trade_date);
      if (eq === undefined) return null;
      return {
        coord: [t.trade_date, eq],
        value: t.action,
        itemStyle: { color: t.action === "BUY" ? "#ef4444" : "#10b981" },
        symbolSize: 12,
      };
    })
    .filter(Boolean) as echarts.MarkPointComponentOption["data"];

  return {
    animation: false,
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(255,255,255,0.95)",
      borderColor: "#e5e7eb",
      textStyle: { color: "#0f172a" },
      valueFormatter: (v) => Number(v).toLocaleString("zh-CN", { maximumFractionDigits: 2 }),
    },
    grid: { left: 64, right: 24, top: 24, bottom: 56 },
    xAxis: {
      type: "category",
      data: dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: "#cbd5e1" } },
      axisLabel: { color: "#64748b" },
    },
    yAxis: {
      scale: true,
      axisLabel: { color: "#64748b" },
      splitLine: { lineStyle: { color: "#f1f5f9" } },
    },
    dataZoom: [
      { type: "inside", start: 0, end: 100 },
      { type: "slider", height: 18, bottom: 16, start: 0, end: 100 },
    ],
    series: [
      {
        name: "净值",
        type: "line",
        data: equity,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: "#2563eb" },
        areaStyle: { color: "rgba(37,99,235,0.08)" },
        markPoint: markPoints && markPoints.length > 0 ? { data: markPoints, label: { show: false } } : undefined,
      },
    ],
  };
}
