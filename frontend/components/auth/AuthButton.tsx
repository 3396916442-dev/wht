"use client";

interface AuthButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
  loading?: boolean;
}

export function AuthButton({
  variant = "primary",
  loading = false,
  className = "",
  children,
  disabled,
  ...props
}: AuthButtonProps) {
  const styles =
    variant === "primary"
      ? "bg-blue-600 text-white hover:bg-blue-500 disabled:bg-blue-900/60"
      : "border border-slate-700 bg-slate-900 text-slate-200 hover:border-slate-600 hover:bg-slate-800 disabled:opacity-60";

  return (
    <button
      className={`inline-flex w-full items-center justify-center rounded-xl px-4 py-3 text-sm font-medium transition disabled:cursor-not-allowed ${styles} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? "处理中..." : children}
    </button>
  );
}
