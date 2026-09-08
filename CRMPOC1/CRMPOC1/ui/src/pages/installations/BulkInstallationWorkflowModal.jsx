import { useEffect, useMemo, useState } from "react";

import Modal from "../../components/Modal.jsx";
import { installationsApi } from "../../api/installations.js";
import { canUseBulkInstallationWorkflow } from "../../utils/installationWorkflowSteps.js";
import { useAuth } from "../../auth/AuthContext.jsx";

function todayInputValue() {
  return new Date().toISOString().slice(0, 10);
}

export default function BulkInstallationWorkflowModal({ rows, onClose, onSaved }) {
  const { user } = useAuth();
  const [workflowRows, setWorkflowRows] = useState(rows);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [completeForm, setCompleteForm] = useState({
    installation_date: todayInputValue(),
    work_report: "",
    proof_document: null,
  });

  useEffect(() => {
    setWorkflowRows(rows);
  }, [rows]);

  const eligibleRows = useMemo(
    () => workflowRows.filter((row) => canUseBulkInstallationWorkflow(row, user?.id, user?.name)),
    [workflowRows, user?.id, user?.name],
  );
  const assignedRows = useMemo(
    () => eligibleRows.filter((row) => row.status === "Assigned"),
    [eligibleRows],
  );
  const rejectedRows = useMemo(
    () => eligibleRows.filter((row) => row.status === "Rejected"),
    [eligibleRows],
  );
  const completionRows = useMemo(
    () => eligibleRows.filter((row) => ["In Progress", "Returned", "Rejected"].includes(row.status)),
    [eligibleRows],
  );

  async function startAllVisits() {
    if (!assignedRows.length) return;
    setBusy(true);
    setErr("");
    setMsg("");
    try {
      const results = await Promise.allSettled(
        assignedRows.map(async (row) => {
          const body = new FormData();
          body.append("new_status", "In Progress");
          await installationsApi.updateStatus(row.id, body);
        }),
      );
      const failed = results.filter((result) => result.status === "rejected").length;
      if (failed > 0) {
        setErr(`${failed} of ${assignedRows.length} visit(s) could not be started.`);
      }
      setMsg(`Engineer visit started for ${assignedRows.length - failed} unit(s).`);
      onSaved?.();
    } catch (error) {
      setErr(error.response?.data?.detail || error.message || "Failed to start visits");
    } finally {
      setBusy(false);
    }
  }

  async function resumeAllRejected() {
    if (!rejectedRows.length) return;
    setBusy(true);
    setErr("");
    setMsg("");
    try {
      const results = await Promise.allSettled(
        rejectedRows.map((row) => installationsApi.resumeWorkflow(row.id)),
      );
      const failed = results.filter((result) => result.status === "rejected").length;
      if (failed > 0) {
        setErr(`${failed} of ${rejectedRows.length} unit(s) could not be resumed.`);
      }
      setMsg(`Resumed ${rejectedRows.length - failed} unit(s). Upload new proof and resubmit completion.`);
      setWorkflowRows((current) => current.map((row) => (
        row.status === "Rejected" ? { ...row, status: "Returned" } : row
      )));
      onSaved?.();
    } catch (error) {
      setErr(error.response?.data?.detail || error.message || "Failed to resume installations");
    } finally {
      setBusy(false);
    }
  }

  async function completeAll() {
    if (!completionRows.length) return;
    if (!completeForm.proof_document) {
      setErr("Installation proof is required for bulk completion.");
      return;
    }
    setBusy(true);
    setErr("");
    setMsg("");
    try {
      const results = await Promise.allSettled(
        completionRows.map(async (row) => {
          if (row.status === "Rejected") {
            await installationsApi.resumeWorkflow(row.id);
          }
          const body = new FormData();
          body.append("installation_date", completeForm.installation_date);
          body.append("work_report", completeForm.work_report || "");
          body.append("proof_document", completeForm.proof_document);
          await installationsApi.completeInstallation(row.id, body);
        }),
      );
      const failed = results.filter((result) => result.status === "rejected").length;
      if (failed > 0) {
        setErr(`${failed} of ${completionRows.length} unit(s) could not be completed.`);
      }
      setMsg(`Installation resubmitted for ${completionRows.length - failed} unit(s). Waiting for admin approval.`);
      onSaved?.();
    } catch (error) {
      setErr(error.response?.data?.detail || error.message || "Failed to complete installations");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal open onClose={onClose} title="Bulk installation workflow" maxWidth="max-w-3xl">
      <div className="space-y-4">
        <p className="text-sm text-slate-600">
          Process multiple vendor units from the same item code group — start visits and complete installations together.
        </p>

        <div className="overflow-x-auto rounded-md border border-slate-200">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-left text-slate-700">
              <tr>
                <th className="px-3 py-2">Request</th>
                <th className="px-3 py-2">Serial</th>
                <th className="px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {eligibleRows.map((row) => (
                <tr key={row.id}>
                  <td className="px-3 py-2 font-medium">#{row.id}</td>
                  <td className="px-3 py-2 font-mono text-xs">{row.serial_no || "—"}</td>
                  <td className="px-3 py-2">{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {rejectedRows.length > 0 && (
          <div className="rounded-md border border-rose-200 bg-rose-50 p-4">
            <div className="text-sm font-medium text-rose-900">Admin returned for correction</div>
            <p className="mt-1 text-xs text-rose-800">
              {rejectedRows.length} unit(s) were rejected or returned by admin. Resume them, fix the issue, then resubmit installation proof below.
            </p>
            <button
              type="button"
              onClick={resumeAllRejected}
              disabled={busy}
              className="mt-3 rounded-md bg-amber-600 px-3 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50"
            >
              Resume {rejectedRows.length} unit(s)
            </button>
          </div>
        )}

        {assignedRows.length > 0 && (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-4">
            <div className="text-sm font-medium text-amber-900">Step 1 — Start engineer visit</div>
            <p className="mt-1 text-xs text-amber-800">
              {assignedRows.length} unit(s) are still Assigned and can be moved to In Progress together.
            </p>
            <button
              type="button"
              onClick={startAllVisits}
              disabled={busy}
              className="mt-3 rounded-md bg-amber-600 px-3 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50"
            >
              Start visit for {assignedRows.length} unit(s)
            </button>
          </div>
        )}

        {completionRows.length > 0 && (
          <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 space-y-3">
            <div>
              <div className="text-sm font-medium text-emerald-900">
                {rejectedRows.length > 0 ? "Resubmit installation" : "Step 2 — Complete installation"}
              </div>
              <p className="mt-1 text-xs text-emerald-800">
                {rejectedRows.length > 0
                  ? `Fix and resubmit installation proof for ${completionRows.length} unit(s). Rejected units are resumed automatically before submission.`
                  : `Apply the same installation date, work report, and proof to ${completionRows.length} unit(s).`}
              </p>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <label className="text-xs uppercase tracking-wide text-slate-500">Installation date</label>
                <input
                  type="date"
                  value={completeForm.installation_date}
                  onChange={(e) => setCompleteForm((current) => ({ ...current, installation_date: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs uppercase tracking-wide text-slate-500">
                  Installation proof <span className="text-rose-600">*</span>
                </label>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                  required
                  onChange={(e) => {
                    setErr("");
                    setCompleteForm((current) => ({ ...current, proof_document: e.target.files?.[0] || null }));
                  }}
                  className="mt-1 block w-full text-sm"
                />
              </div>
              <div className="md:col-span-2">
                <label className="text-xs uppercase tracking-wide text-slate-500">Work report</label>
                <textarea
                  rows={3}
                  value={completeForm.work_report}
                  onChange={(e) => setCompleteForm((current) => ({ ...current, work_report: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  placeholder="Summary applied to all selected units"
                />
              </div>
            </div>
            <button
              type="button"
              onClick={completeAll}
              disabled={busy || !completeForm.proof_document}
              className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {rejectedRows.length > 0
                ? `Resubmit ${completionRows.length} unit(s)`
                : `Complete ${completionRows.length} unit(s)`}
            </button>
          </div>
        )}

        {err && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{err}</div>}
        {msg && <div className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{msg}</div>}

        <div className="flex justify-end">
          <button type="button" onClick={onClose} className="rounded-md border border-slate-300 px-3 py-2 text-sm">
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
}
