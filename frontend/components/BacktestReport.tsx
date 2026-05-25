import { classNames } from "@/lib/format";
import type { BacktestReport as ReportData, ReportLevel } from "@/types";

interface ReportProps {
  report: ReportData;
}

const LEVEL_STYLE: Record<ReportLevel, { badge: string; border: string; bg: string }> = {
  info: {
    badge: "bg-neutral-100 text-neutral-700",
    border: "border-neutral-200",
    bg: "bg-white",
  },
  good: {
    badge: "bg-emerald-100 text-emerald-700",
    border: "border-emerald-200",
    bg: "bg-emerald-50/40",
  },
  warning: {
    badge: "bg-amber-100 text-amber-700",
    border: "border-amber-200",
    bg: "bg-amber-50/40",
  },
  danger: {
    badge: "bg-rose-100 text-rose-700",
    border: "border-rose-200",
    bg: "bg-rose-50/40",
  },
};

const LEVEL_LABEL: Record<ReportLevel, string> = {
  info: "提示",
  good: "良好",
  warning: "注意",
  danger: "警示",
};

export function BacktestReport({ report }: ReportProps) {
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-neutral-100 pb-3">
        <p className="text-base font-semibold text-neutral-900">{report.summary}</p>
        <span className="text-xs text-neutral-500">
          provider: <code className="rounded bg-neutral-100 px-1 py-0.5">{report.provider}</code>{" "}
          · {report.generated_at.replace("T", " ")}
        </span>
      </div>

      <ol className="space-y-3">
        {report.sections.map((section) => {
          const style = LEVEL_STYLE[section.level] ?? LEVEL_STYLE.info;
          return (
            <li
              key={section.title}
              className={classNames(
                "rounded-lg border p-4",
                style.border,
                style.bg,
              )}
            >
              <div className="flex items-baseline justify-between gap-3">
                <h3 className="text-sm font-semibold text-neutral-900">{section.title}</h3>
                <span
                  className={classNames(
                    "rounded px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide",
                    style.badge,
                  )}
                >
                  {LEVEL_LABEL[section.level] ?? section.level}
                </span>
              </div>
              <ul className="mt-2 space-y-1.5 text-sm leading-relaxed text-neutral-700">
                {section.content.map((line, i) => (
                  <li key={i}>{line}</li>
                ))}
              </ul>
            </li>
          );
        })}
      </ol>

      <p className="rounded-lg border border-neutral-200 bg-neutral-50 p-3 text-xs leading-relaxed text-neutral-600">
        {report.disclaimer}
      </p>
    </div>
  );
}
