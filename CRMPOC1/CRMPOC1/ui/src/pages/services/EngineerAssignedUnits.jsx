import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { servicesApi } from "../../api/services.js";

function serialCell(value) {
  return value ? <span className="font-mono text-xs">{value}</span> : <span className="text-slate-400">—</span>;
}

export default function EngineerAssignedUnits() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    setLoading(true);
    setErr("");
    servicesApi.myAssignedUnits()
      .then(setGroups)
      .catch((error) => setErr(error.response?.data?.detail || "Failed to load assigned units"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">My Assigned Service Units</h1>
          <p className="text-sm text-slate-500">Units grouped by service request and item code.</p>
        </div>
        <Link to="/services" className="rounded-md border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50">
          All service requests
        </Link>
      </div>

      {err && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{err}</div>}
      {loading && <div className="text-sm text-slate-500">Loading…</div>}

      {!loading && groups.length === 0 && (
        <div className="rounded-lg bg-white p-6 text-sm text-slate-500 shadow-sm">No units assigned to you yet.</div>
      )}

      <div className="space-y-4">
        {groups.map((group) => (
          <section key={`${group.service_request_id}-${group.item_code}`} className="rounded-lg bg-white shadow-sm">
            <div className="border-b border-slate-200 px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <Link to={`/services/${group.service_request_id}`} className="font-mono text-sm text-brand-600 hover:underline">
                  {group.request_no}
                </Link>
                <span className="text-sm text-slate-500">{group.order_no || "No order"}</span>
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{group.status}</span>
              </div>
              <div className="mt-1 text-sm text-slate-700">{group.customer_name}</div>
              <div className="text-xs text-slate-500">{group.customer_address || "—"}</div>
              <div className="mt-2 text-sm font-medium text-slate-800">
                {group.item_code} — {group.item_name} ({group.assigned_quantity} units)
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-100 text-left text-slate-700">
                  <tr>
                    <th className="px-3 py-2">Qty</th>
                    {(group.serial_labels?.length ? group.serial_labels : ["Serial Number"]).map((label) => (
                      <th key={label} className="px-3 py-2">{label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {group.units.map((unit, idx) => (
                    <tr key={unit.id}>
                      <td className="px-3 py-2">{idx + 1}</td>
                      {(unit.serial_values?.length ? unit.serial_values : [unit.serial_no]).map((value, colIdx) => (
                        <td key={colIdx} className="px-3 py-2">{serialCell(value)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
