import { useEffect, useMemo, useRef, useState } from "react";

const fieldClass =
  "w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500";

/**
 * options: [{ value, label }]
 * value: current selected value (string/number) or ""
 */
export default function SearchableSelect({
  options,
  value,
  onChange,
  placeholder = "Search…",
  disabled = false,
  className = "",
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const rootRef = useRef(null);

  const selected = useMemo(
    () => options.find((o) => String(o.value) === String(value)) || null,
    [options, value]
  );

  useEffect(() => {
    function onDocClick(e) {
      if (rootRef.current && !rootRef.current.contains(e.target)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const filtered = useMemo(() => {
    if (!query.trim()) return options;
    const q = query.toLowerCase();
    return options.filter((o) => o.label.toLowerCase().includes(q));
  }, [options, query]);

  return (
    <div className={`relative ${className}`} ref={rootRef}>
      <input
        type="text"
        disabled={disabled}
        className={fieldClass}
        placeholder={placeholder}
        value={open ? query : selected?.label || ""}
        onFocus={() => {
          setOpen(true);
          setQuery("");
        }}
        onChange={(e) => setQuery(e.target.value)}
        readOnly={disabled}
      />
      {open && !disabled && (
        <div className="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-md border border-slate-200 bg-white shadow-lg">
          {filtered.length === 0 && (
            <div className="px-3 py-2 text-sm text-slate-400">No matches</div>
          )}
          {filtered.map((o) => (
            <div
              key={o.value}
              onClick={() => {
                onChange(o.value);
                setOpen(false);
                setQuery("");
              }}
              className="cursor-pointer px-3 py-2 text-sm hover:bg-brand-50"
            >
              {o.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
