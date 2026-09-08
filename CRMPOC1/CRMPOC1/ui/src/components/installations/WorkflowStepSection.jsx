export default function WorkflowStepSection({
  title,
  done = false,
  locked = false,
  summary = null,
  children,
  footer = null,
  borderClass = "border-slate-200",
  bgClass = "bg-white",
}) {
  const showReadOnly = locked && done;

  return (
    <div className={`rounded-md border p-4 ${borderClass} ${showReadOnly ? "bg-slate-50" : bgClass}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-medium text-slate-900">{title}</div>
        {done && (
          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
            Completed
          </span>
        )}
        {locked && !done && (
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
            Waiting
          </span>
        )}
      </div>
      {showReadOnly ? (
        <div className="mt-2 text-sm text-slate-700">{summary}</div>
      ) : (
        <div className={locked ? "pointer-events-none mt-3 opacity-60" : "mt-3"}>
          {children}
        </div>
      )}
      {footer && <div className="mt-3">{footer}</div>}
    </div>
  );
}
