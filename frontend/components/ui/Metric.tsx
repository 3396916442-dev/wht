import { classNames, formatPercent, formatNumber, formatInt } from "@/lib/format";

type Format = "percent" | "number" | "int" | "raw";

interface MetricProps {
  label: string;
  value: number | string | null | undefined;
  format?: Format;
  /** 当 format=percent / number 时启用：value > 0 显示绿色，< 0 显示红色 */
  signed?: boolean;
  hint?: string;
}

function formatValue(value: number | string | null | undefined, format: Format): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  switch (format) {
    case "percent":
      return formatPercent(value);
    case "number":
      return formatNumber(value, 4);
    case "int":
      return formatInt(value);
    case "raw":
    default:
      return String(value);
  }
}

export function Metric({ label, value, format = "number", signed = false, hint }: MetricProps) {
  const numeric = typeof value === "number" ? value : null;
  const positive = signed && numeric !== null && numeric > 0;
  const negative = signed && numeric !== null && numeric < 0;

  return (
    <div className="rounded-lg border border-neutral-200 bg-white px-4 py-3">
      <div className="text-xs uppercase tracking-wide text-neutral-500">{label}</div>
      <div
        className={classNames(
          "mt-1 text-2xl font-semibold tabular-nums",
          positive && "text-emerald-600",
          negative && "text-rose-600",
          !positive && !negative && "text-neutral-900",
        )}
      >
        {formatValue(value, format)}
      </div>
      {hint && <div className="mt-1 text-xs text-neutral-500">{hint}</div>}
    </div>
  );
}
