"use client";

interface AuthAlertProps {
  type?: "error" | "success";
  message: string;
}

export function AuthAlert({ type = "error", message }: AuthAlertProps) {
  const styles =
    type === "error"
      ? "border-rose-500/30 bg-rose-500/10 text-rose-300"
      : "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";

  return (
    <div className={`rounded-xl border px-4 py-3 text-sm ${styles}`}>{message}</div>
  );
}
