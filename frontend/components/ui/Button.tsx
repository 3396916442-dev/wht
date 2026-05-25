import { classNames } from "@/lib/format";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const VARIANT_STYLES: Record<Variant, string> = {
  primary:
    "bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed",
  secondary:
    "border border-neutral-300 bg-white text-neutral-800 hover:bg-neutral-50 disabled:opacity-60",
  ghost:
    "text-neutral-700 hover:bg-neutral-100 disabled:opacity-60",
};

export function Button({
  variant = "primary",
  className,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      className={classNames(
        "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-blue-500/50",
        VARIANT_STYLES[variant],
        className,
      )}
    />
  );
}
