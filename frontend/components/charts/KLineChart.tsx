"use client";

import { useEffect, useMemo, useRef } from "react";
import * as echarts from "echarts";

import type { DailyBarItem } from "@/types";

interface KLineChartProps {
  items: DailyBarItem[];
  /** 显示哪些 MA 线，默认 [5, 10, 20] */
  maLines?: number[];
  height?: number;
}

const MA_COLOR: Record<number, string> = {
  5: "#f59e0b",   // 琥珀
  10: "#3b82f6",  // 蓝
  20: "#a855f7",  // 紫
  60: "#10b981",  // 翠绿
};

// A 股惯例：红涨绿跌
const UP_COLOR = "#ef4444";
const DOWN_COLOR = "#10b981";

export function KLineChart({ items, maLines = [5, 10, 20], height = 480 }: KLineChartProps) {
  const ref = useRef<HTMLDivElement | null>(null);

  const option = useMemo(() => buildOption(items, maLines), [items, maLines]);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    chart.setOption(option);

    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.dispose();
    };
  }, [option]);

  return <div ref={ref} className="w-full" style={{ height }} />;
}

function buildOption(items: DailyBarItem[], maLines: number[]): echarts.EChartsOption {
  const dates = items.map((it) => it.trade_date);
  // ECharts 蜡烛图顺序：[open, close, low, high]
  const ohlc = items.map((it) => [it.open, it.close, it.low, it.high]);
  const volumes = items.map((it, i) => ({
    value: it.volume,
    itemStyle: {
      color: it.close >= it.open ? UP_COLOR : DOWN_COLOR,
    },
  }));

  const maSeries = maLines.map((n) => ({
    name: `MA${n}`,
    type: "line" as const,
    data: items.map((it) => {
      const v = it[`ma${n}` as keyof DailyBarItem] as number | null | undefined;
      return v ?? null;
    }),
    smooth: true,
    showSymbol: false,
    lineStyle: { width: 1.2, color: MA_COLOR[n] ?? "#64748b" },
  }));

  return {
    animation: false,
    legend: {
      top: 8,
      data: ["K 线", ...maLines.map((n) => `MA${n}`)],
      textStyle: { color: "#475569" },
    },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      backgroundColor: "rgba(255,255,255,0.95)",
      borderColor: "#e5e7eb",
      textStyle: { color: "#0f172a" },
    },
    grid: [
      { left: 50, right: 24, top: 40, height: "60%" },
      { left: 50, right: 24, top: "78%", height: "16%" },
    ],
    xAxis: [
      {
        type: "category",
        data: dates,
        boundaryGap: true,
        axisLine: { lineStyle: { color: "#cbd5e1" } },
        axisLabel: { color: "#64748b" },
        splitLine: { show: false },
      },
      {
        type: "category",
        gridIndex: 1,
        data: dates,
        boundaryGap: true,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
      },
    ],
    yAxis: [
      {
        scale: true,
        splitLine: { lineStyle: { color: "#f1f5f9" } },
        axisLabel: { color: "#64748b" },
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { color: "#94a3b8", fontSize: 10 },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      { type: "inside", xAxisIndex: [0, 1], start: 60, end: 100 },
      { type: "slider", xAxisIndex: [0, 1], top: "95%", height: 18, start: 60, end: 100 },
    ],
    series: [
      {
        name: "K 线",
        type: "candlestick",
        data: ohlc,
        itemStyle: {
          color: UP_COLOR,
          color0: DOWN_COLOR,
          borderColor: UP_COLOR,
          borderColor0: DOWN_COLOR,
        },
      },
      ...maSeries,
      {
        name: "Volume",
        type: "bar",
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
      },
    ],
  };
}
