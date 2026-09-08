import { useEffect, useState } from "react";

import Modal from "../../components/Modal.jsx";
import { installationsApi } from "../../api/installations.js";
import { ENGINEER_ASSIGNMENT_HINT, formatEngineerOptionLabel } from "../../utils/engineerAssignment.js";

export default function BulkAssignModal({ rows, onClose, onSaved }) {
  const [engineers, setEngineers] = useState([]);
  const [perRowEngineer, setPerRowEngineer] = useState({});
  const [applyAll, setApplyAll] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    installationsApi.engineerAssignmentOptions()
      .then(setEngineers)
      .catch(() => setEngineers([]));
  }, []);

  function setRow(id, engineerId) {
    setPerRowEngineer((prev) => ({ ...prev, [id]: engineerId }));
  }

  function applyToAll(engineerId) {
    setApplyAll(engineerId);
    if (!engineerId) return;
    const next = {};
    rows.forEach((r) => { next[r.id] = engineerId; });
    setPerRowEngineer(next);
  }

  async function submit() {
    const assignments = rows
      .filter((r) => perRowEngineer[r.id])
      .map((r) => ({ installation_id: r.id, engineer_id: Number(perRowEngineer[r.id]) }));

    if (assignments.length === 0) {
      setErr("Select an engineer for at least one row");
      return;
    }

    setErr("");
    setBusy(true);
    try {
      await installationsApi.bulkAssign(assignments);
      onSaved?.();
    } catch (e) {
      const detail = e.response?.data?.detail;
      setErr(Array.isArray(detail) ? detail.map((d) => d.msg).join("; ") : detail || "Failed to assign");
    } finally {
      setBusy(false);
    }
  }

  const fieldClass = "w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm";

  return (
    <Modal open={true} onClose={onClose} title={`Bulk Assign Engineer (${rows.length} row${rows.length === 1 ? "" : "s"})`} maxWidth="max-w-2xl">
      <div className="space-y-4">
        {err && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{err}</div>}

        <div className="flex items-center gap-2 rounded-md bg-slate-50 p-3">
          <span className="text-sm text-slate-600">Apply to all:</span>
          <select value={applyAll} onChange={(e) => applyToAll(e.target.value)} className={fieldClass + " max-w-xs"}>
            <option value="">-- Choose engineer --</option>
            {engineers.map((u) => (
              <option key={u.id} value={u.id}>{formatEngineerOptionLabel(u)}</option>
            ))}
          </select>
        </div>

        <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
          {ENGINEER_ASSIGNMENT_HINT}
        </div>

        <div className="max-h-80 overflow-y-auto rounded-md border border-slate-200">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-left text-slate-600">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">Serial 1</th>
                <th className="px-3 py-2">Serial 2</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Engineer</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="px-3 py-2 text-slate-500">{r.id}</td>
                  <td className="px-3 py-2 font-mono text-xs">{r.serial_no || "--"}</td>
                  <td className="px-3 py-2 font-mono text-xs">{r.serial_no_2 || "--"}</td>
                  <td className="px-3 py-2">{r.status}</td>
                  <td className="px-3 py-2">
                    <select
                      value={perRowEngineer[r.id] || ""}
                      onChange={(e) => setRow(r.id, e.target.value)}
                      className={fieldClass}
                    >
                      <option value="">-- Unassigned --</option>
                      {engineers.map((u) => (
                        <option key={u.id} value={u.id}>{formatEngineerOptionLabel(u)}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-md border border-slate-300 px-3 py-2 text-sm">
            Cancel
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={busy}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {busy ? "Assigning..." : "Assign"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
