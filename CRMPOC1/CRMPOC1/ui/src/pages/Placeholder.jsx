export default function Placeholder({ title }) {
  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-semibold text-slate-800">{title}</h1>
      <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center text-slate-500">
        <div className="text-lg font-medium">Coming in a future sprint</div>
        <p className="mt-2 text-sm">
          This module is scaffolded but not implemented yet. The backend schema and route stubs
          are in place — UI and full endpoints land in sprints 2–5.
        </p>
      </div>
    </div>
  );
}
