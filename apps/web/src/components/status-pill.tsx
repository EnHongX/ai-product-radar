type StatusPillProps = {
  status: "ok" | "degraded" | string;
  label: string;
};

export function StatusPill({ status, label }: StatusPillProps) {
  const className =
    status === "ok"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : "border-amber-200 bg-amber-50 text-amber-800";

  return (
    <span className={`inline-flex h-8 items-center rounded-md border px-3 text-sm font-medium ${className}`}>
      {label}
    </span>
  );
}
