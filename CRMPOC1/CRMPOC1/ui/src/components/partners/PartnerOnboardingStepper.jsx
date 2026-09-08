export default function PartnerOnboardingStepper({ steps = [] }) {
  if (!steps.length) return null;

  return (
    <div className="mt-6 overflow-x-auto">
      <div className="flex min-w-[720px] items-center justify-between px-2">
        {steps.map((step, index) => {
          const isLast = index === steps.length - 1;
          const circleClass = step.done
            ? "border-sky-600 bg-sky-600 text-white"
            : step.current
              ? "border-sky-600 bg-white text-sky-700 ring-4 ring-sky-100"
              : "border-slate-300 bg-white text-slate-400";
          const lineClass = step.done ? "bg-sky-600" : "bg-slate-300";
          const labelClass = step.current
            ? "text-sky-700 font-semibold"
            : step.done
              ? "text-sky-700"
              : "text-slate-500";

          return (
            <div key={step.label} className="flex flex-1 items-center">
              <div className="flex flex-col items-center text-center">
                <div className={`flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-semibold ${circleClass}`}>
                  {step.done ? "✓" : index + 1}
                </div>
                <div className={`mt-2 max-w-[120px] text-[11px] uppercase tracking-wide ${labelClass}`}>
                  {step.label}
                </div>
              </div>
              {!isLast && (
                <div className={`mx-2 h-1 flex-1 rounded ${lineClass}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
