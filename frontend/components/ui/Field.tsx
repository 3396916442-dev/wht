import { classNames } from "@/lib/format";

interface FieldProps {
  label: string;
  htmlFor?: string;
  hint?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}

export function Field({ label, htmlFor, hint, className, children }: FieldProps) {
  return (
    <label htmlFor={htmlFor} className={classNames("flex flex-col gap-1", className)}>
      <span className="text-sm font-medium text-neutral-700">{label}</span>
      {children}
      {hint && <span className="text-xs text-neutral-500">{hint}</span>}
    </label>
  );
}

export function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={classNames(
        "rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 shadow-sm",
        "placeholder:text-neutral-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500",
        "disabled:bg-neutral-50 disabled:text-neutral-400",
        props.className,
      )}
    />
  );
}

export function NumberInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <TextInput type="number" {...props} />;
}

export function DateInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <TextInput type="date" {...props} />;
}
