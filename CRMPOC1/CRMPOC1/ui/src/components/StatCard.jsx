const TONES = {
  orange: "bg-orange-500",
  green: "bg-emerald-500",
  blue: "bg-sky-500",
  red: "bg-rose-500",
  grey: "bg-slate-600",
};

export default function StatCard({ label, value, tone = "blue" }) {
  return (
    <div className={`rounded-lg p-4 text-white shadow-sm ${TONES[tone] || TONES.blue}`}>
      <div className="text-sm font-medium opacity-90">{label}</div>
      <div className="mt-1 text-3xl font-semibold">{value ?? "—"}</div>
    </div>
  );
}
