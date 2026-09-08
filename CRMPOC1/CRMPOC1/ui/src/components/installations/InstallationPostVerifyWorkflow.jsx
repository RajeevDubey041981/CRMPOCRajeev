import { useEffect, useState } from "react";

import { api } from "../../api/client.js";
import { installationsApi } from "../../api/installations.js";
import { toDownloadUrl } from "../../utils/downloadUrl.js";
import { formatApiError } from "../../utils/apiError.js";
import { installationSerialReady, isAssignedToUser } from "../../utils/installationWorkflowSteps.js";
import WorkflowStepSection from "./WorkflowStepSection.jsx";

const PAYMENT_TYPES = ["Cash", "UPI"];

function resolveInstallationId(installation) {
  return installation?.id ?? installation?.installation_request_id ?? null;
}

function resolveQrPath(installation, installationId) {
  if (installation?.payment_qr_code_path) return installation.payment_qr_code_path;
  if (installationId) return `/api/installations/${installationId}/payment-qr`;
  return null;
}

function isImagePath(path) {
  return /\.(png|jpe?g|gif|webp)$/i.test(path || "");
}

function PaymentQrPreview({ path, label = "QR code" }) {
  const [objectUrl, setObjectUrl] = useState("");
  const [isImage, setIsImage] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);

  useEffect(() => {
    if (!path) {
      setObjectUrl("");
      setIsImage(false);
      setLoadFailed(false);
      return undefined;
    }

    let active = true;
    let nextObjectUrl = "";

    async function loadQr() {
      setLoadFailed(false);
      try {
        const response = await api.get(path, { responseType: "blob" });
        nextObjectUrl = URL.createObjectURL(response.data);
        if (active) {
          setObjectUrl(nextObjectUrl);
          setIsImage(response.data.type?.startsWith("image/") || isImagePath(path));
        }
      } catch {
        if (active) {
          setObjectUrl("");
          setIsImage(false);
          setLoadFailed(true);
        }
      }
    }

    loadQr();

    return () => {
      active = false;
      if (nextObjectUrl) URL.revokeObjectURL(nextObjectUrl);
    };
  }, [path]);

  if (!path) return null;

  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      {objectUrl && isImage && (
        <img
          src={objectUrl}
          alt={label}
          className="mt-2 max-h-72 rounded border border-slate-200 bg-white object-contain"
        />
      )}
      {objectUrl && !isImage && (
        <p className="mt-2 text-xs text-slate-600">QR file uploaded. Use download to open it.</p>
      )}
      {loadFailed && (
        <p className="mt-2 text-xs text-rose-600">Unable to preview QR code. Try the download link below.</p>
      )}
      <a
        href={objectUrl || toDownloadUrl(path)}
        download
        target="_blank"
        rel="noreferrer"
        className="mt-2 inline-block text-sm font-medium text-sky-700 underline"
      >
        Download QR code
      </a>
    </div>
  );
}

function Field({ label, value, mono = false }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-0.5 text-sm text-slate-800 ${mono ? "font-mono" : ""}`}>{value || "—"}</div>
    </div>
  );
}

function toDateInputValue(value) {
  if (!value) return new Date().toISOString().slice(0, 10);
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return new Date().toISOString().slice(0, 10);
  return date.toISOString().slice(0, 10);
}

export default function InstallationPostVerifyWorkflow({
  installation,
  isEngineer,
  isAdminLike,
  userId,
  onUpdated,
  onError,
  onBusy,
  workflowSteps = null,
}) {
  const [completeForm, setCompleteForm] = useState({
    installation_date: toDateInputValue(installation.installation_date),
    work_report: installation.work_report || "",
    proof_document: null,
  });
  const [paymentForm, setPaymentForm] = useState({
    payment_amount: installation.payment_amount_requested || "",
    payment_type: installation.payment_type_requested || "Cash",
    work_report: installation.work_report || "",
    qr_code: null,
  });
  const [adminForm, setAdminForm] = useState({
    payment_amount: installation.payment_amount_requested || "",
    payment_type: installation.payment_type_paid || installation.payment_type_requested || "Cash",
    proof_document: null,
  });

  const [submitMsg, setSubmitMsg] = useState("");
  const [completeErr, setCompleteErr] = useState("");
  const [approvalErr, setApprovalErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [engineerQrPreviewUrl, setEngineerQrPreviewUrl] = useState("");

  const installationId = resolveInstallationId(installation);
  const engineerQrPath = resolveQrPath(installation, installationId);
  const fieldClass = "w-full rounded-md border border-slate-300 px-3 py-2 text-sm";
  const step7 = workflowSteps?.steps?.[7];
  const step8 = workflowSteps?.steps?.[8];
  const step9 = workflowSteps?.steps?.[9];
  const step10 = workflowSteps?.steps?.[10];
  const isAssignedEngineer = isEngineer && isAssignedToUser(installation, userId);
  const serialReady = installationSerialReady(installation);
  const canComplete = isAssignedEngineer
    && serialReady
    && ["Assigned", "In Progress", "Returned"].includes(installation.status);
  const needsResume = isAssignedEngineer && installation.status === "Rejected";
  const paymentPhaseReached = Boolean(step8?.done)
    || ["Installation Completed", "Payment Pending", "Completed"].includes(installation.status);
  const showRaisePaymentStep = serialReady
    && paymentPhaseReached
    && (isAssignedEngineer || isAdminLike);
  const canRaisePayment = isAssignedEngineer
    && installation.status === "Installation Completed";
  const canApproveCompletion = isAdminLike && installation.status === "Completion Pending Approval";
  const canApprovePayment = isAdminLike && installation.status === "Payment Pending";
  const isUpiPaymentApproval = canApprovePayment && adminForm.payment_type === "UPI";
  const showSubmittedPaymentQr = installation.payment_type_requested === "UPI"
    && installation.status === "Payment Pending"
    && Boolean(engineerQrPath);

  useEffect(() => {
    if (!paymentForm.qr_code) {
      setEngineerQrPreviewUrl("");
      return undefined;
    }
    const nextUrl = URL.createObjectURL(paymentForm.qr_code);
    setEngineerQrPreviewUrl(nextUrl);
    return () => URL.revokeObjectURL(nextUrl);
  }, [paymentForm.qr_code]);

  async function approvePayment() {
    setApprovalErr("");
    onError?.("");
    setSubmitMsg("");

    if (!adminForm.payment_amount && adminForm.payment_amount !== 0 && adminForm.payment_amount !== "0") {
      const message = "Approved payment amount is required";
      setApprovalErr(message);
      onError?.(message);
      return;
    }
    if (
      isUpiPaymentApproval
      && !adminForm.proof_document
      && !installation.payment_proof_file_path
    ) {
      const message = "Upload Payment Proof / Document is required when payment type is UPI";
      setApprovalErr(message);
      onError?.(message);
      return;
    }

    setBusy(true);
    onBusy?.(true);
    try {
      const fd = new FormData();
      fd.append("new_status", "Completed");
      fd.append("payment_amount", String(adminForm.payment_amount));
      fd.append("payment_type", adminForm.payment_type);
      if (adminForm.proof_document) fd.append("document", adminForm.proof_document);
      await installationsApi.updateStatus(installationId, fd);
      setSubmitMsg("Payment approved. Installation completed.");
      if (onUpdated) await onUpdated();
    } catch (error) {
      const message = formatApiError(error, "Failed to approve payment");
      setApprovalErr(message);
      onError?.(message);
    } finally {
      setBusy(false);
      onBusy?.(false);
    }
  }

  async function run(action) {
    setBusy(true);
    onBusy?.(true);
    onError?.("");
    setSubmitMsg("");
    try {
      await action();
      if (onUpdated) await onUpdated();
    } catch (error) {
      onError?.(formatApiError(error, "Action failed"));
    } finally {
      setBusy(false);
      onBusy?.(false);
    }
  }

  async function reviewCompletion(decision) {
    const remarks = window.prompt(`${decision} installation completion remarks (optional):`, "");
    if (remarks === null) return;
    await run(async () => {
      const body = new FormData();
      body.append("decision", decision);
      if (remarks.trim()) body.append("remarks", remarks.trim());
      await installationsApi.reviewCompletion(installationId, body);
      setSubmitMsg(decision === "Approve" ? "Completion approved. Payment request is now available." : "Returned to engineer for correction.");
    });
  }

  if (!serialReady || !installationId) return null;

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-slate-200 bg-white p-4">
        <div className="text-sm font-medium text-slate-800">Verified unit details</div>
        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
          <Field label="Item code" value={installation.item_code} mono />
          <Field label="Serial" value={installation.serial_no} mono />
          <Field label="Serial 2" value={installation.serial_no_2} mono />
          <Field label="Billing" value={installation.admin_billing_type || "Free"} />
          <Field label="Status" value={installation.status} />
        </div>
        {installation.parent_installation_id && (
          <p className="mt-2 text-xs text-slate-500">
            Split from installation request #{installation.parent_installation_id}
          </p>
        )}
      </div>

      {(installation.status === "Returned" || installation.status === "Rejected") && isAssignedEngineer && (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          <div className="font-medium">Admin returned this installation for correction</div>
          <p className="mt-1 text-xs text-rose-800">
            {installation.admin_approval_remark
              ? installation.admin_approval_remark
              : "Review the admin feedback, fix the installation details, and resubmit completion proof."}
          </p>
          {needsResume && (
            <button
              type="button"
              disabled={busy}
              onClick={() => run(async () => {
                await installationsApi.resumeWorkflow(installationId);
                setSubmitMsg("Installation reopened. Update proof and resubmit completion.");
              })}
              className="mt-3 rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              Resume installation workflow
            </button>
          )}
        </div>
      )}

      {(canComplete || step7?.done) && (
        <WorkflowStepSection
          title="Step 7 — Complete installation"
          done={Boolean(step7?.done)}
          locked={Boolean(step7?.locked)}
          borderClass="border-emerald-200"
          bgClass="bg-emerald-50"
          summary={installation.work_report_file_path
            ? `Installation completed on ${installation.installation_date ? new Date(installation.installation_date).toLocaleDateString() : "—"}.`
            : "Installation completion recorded."}
        >
          <p className="text-xs text-emerald-800">
            Upload installation proof (required) and record the installation date.
            Admin must approve completion before you can raise a payment request.
          </p>
          <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <label className="text-xs uppercase tracking-wide text-slate-500">Installation date</label>
              <input
                type="date"
                value={completeForm.installation_date}
                onChange={(e) => setCompleteForm((current) => ({ ...current, installation_date: e.target.value }))}
                className={`${fieldClass} mt-1`}
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
                  setCompleteErr("");
                  onError?.("");
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
                className={`${fieldClass} mt-1`}
                placeholder="Summary of installation work completed"
              />
            </div>
          </div>
          {completeErr && (
            <p className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{completeErr}</p>
          )}
          <button
            type="button"
            disabled={busy || !completeForm.proof_document}
            onClick={() => {
              if (!completeForm.proof_document) {
                const message = "Installation proof is required before submitting completion.";
                setCompleteErr(message);
                onError?.(message);
                return;
              }
              run(async () => {
                setCompleteErr("");
                const fd = new FormData();
                fd.append("installation_date", completeForm.installation_date);
                if (completeForm.work_report) fd.append("work_report", completeForm.work_report);
                fd.append("proof_document", completeForm.proof_document);
                await installationsApi.completeInstallation(installationId, fd);
                setSubmitMsg("Installation completion submitted. Waiting for admin approval.");
              });
            }}
            className="mt-3 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            Submit installation completion
          </button>
        </WorkflowStepSection>
      )}

      {installation.work_report_file_path && (
        <div className="rounded-md border border-slate-200 bg-white p-4 text-sm">
          <div className="font-medium text-slate-800">Submitted installation proof</div>
          <a
            href={toDownloadUrl(installation.work_report_file_path)}
            download
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-block text-sky-700 underline"
          >
            Download installation proof
          </a>
        </div>
      )}

      {canApproveCompletion && (
        <WorkflowStepSection
          title="Step 8 — Review installation completion"
          done={false}
          borderClass="border-emerald-200"
          bgClass="bg-emerald-50"
          summary="Engineer completion is waiting for Admin/Indcool approval before payment."
        >
          <p className="text-xs text-emerald-800">
            Review the submitted installation proof and work report, then approve or reject.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button type="button" onClick={() => reviewCompletion("Reject")} disabled={busy} className="rounded-md border border-rose-300 px-4 py-2 text-sm text-rose-700 disabled:opacity-50">Return to engineer</button>
            <button type="button" onClick={() => reviewCompletion("Approve")} disabled={busy} className="rounded-md bg-emerald-600 px-4 py-2 text-sm text-white disabled:opacity-50">Approve completion</button>
          </div>
        </WorkflowStepSection>
      )}

      {!canApproveCompletion && step8?.done && (
        <WorkflowStepSection
          title="Step 8 — Review installation completion"
          done
          borderClass="border-emerald-200"
          bgClass="bg-emerald-50"
          summary="Admin approved installation completion. Engineer can raise payment request."
        />
      )}

      {installation.status === "Completion Pending Approval" && isAssignedEngineer && (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Installation completion submitted. Waiting for admin to approve before you can raise payment.
        </div>
      )}

      {installation.payment_proof_file_path && (isAssignedEngineer || isAdminLike) && (
        <div className="rounded-md border border-indigo-200 bg-indigo-50 p-4 text-sm">
          <div className="font-medium text-indigo-900">Payment proof</div>
          <p className="mt-1 text-xs text-indigo-800">
            UPI payment screenshot or receipt uploaded when payment was approved.
          </p>
          <a
            href={toDownloadUrl(installation.payment_proof_file_path)}
            download
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-block font-medium text-sky-700 underline"
          >
            View / download payment proof
          </a>
        </div>
      )}

      {showRaisePaymentStep && (
        <WorkflowStepSection
          title="Step 9 — Raise payment request"
          done={Boolean(step9?.done)}
          locked={Boolean(step9?.locked)}
          borderClass="border-amber-200"
          bgClass="bg-amber-50"
          summary={installation.payment_amount_requested
            ? `Payment request raised: ${installation.payment_amount_requested} (${installation.payment_type_requested || "—"}).`
            : "Payment request submitted."}
        >
          <p className="text-xs text-amber-800">
            {canRaisePayment
              ? "Submit the payment amount requested. Admin will decide the final approved amount."
              : "Waiting for admin to approve installation completion (Step 8) before you can raise payment."}
          </p>
          <div className={`mt-3 grid grid-cols-1 gap-3 md:grid-cols-2 ${canRaisePayment ? "" : "opacity-70"}`}>
            <div>
              <label className="text-xs uppercase tracking-wide text-slate-500">Payment amount</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={paymentForm.payment_amount}
                onChange={(e) => setPaymentForm((current) => ({ ...current, payment_amount: e.target.value }))}
                className={`${fieldClass} mt-1`}
                disabled={!canRaisePayment}
              />
            </div>
            <div>
              <label className="text-xs uppercase tracking-wide text-slate-500">Payment type</label>
              <select
                value={paymentForm.payment_type}
                onChange={(e) => setPaymentForm((current) => ({ ...current, payment_type: e.target.value }))}
                className={`${fieldClass} mt-1`}
                disabled={!canRaisePayment}
              >
                {PAYMENT_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}
              </select>
            </div>
            {paymentForm.payment_type === "UPI" && (
              <div className="md:col-span-2 space-y-2">
                <div>
                  <label className="text-xs uppercase tracking-wide text-slate-500">UPI QR code</label>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => setPaymentForm((current) => ({ ...current, qr_code: e.target.files?.[0] || null }))}
                    className="mt-1 block w-full text-sm"
                    disabled={!canRaisePayment}
                  />
                </div>
                {engineerQrPreviewUrl && (
                  <img
                    src={engineerQrPreviewUrl}
                    alt="Selected UPI QR code"
                    className="max-h-64 rounded border border-slate-200 bg-white object-contain"
                  />
                )}
              </div>
            )}
          </div>
          <button
            type="button"
            disabled={!canRaisePayment}
            onClick={() => run(async () => {
              if (paymentForm.payment_amount === "" || paymentForm.payment_amount === null) {
                throw new Error("Payment amount is required");
              }
              if (Number(paymentForm.payment_amount) < 0) {
                throw new Error("Payment amount cannot be negative");
              }
              if (paymentForm.payment_type === "UPI" && !paymentForm.qr_code && !installation.payment_qr_code_path) {
                throw new Error("UPI QR code is required");
              }
              const fd = new FormData();
              fd.append("payment_amount", String(paymentForm.payment_amount));
              fd.append("payment_type", paymentForm.payment_type);
              if (paymentForm.work_report) fd.append("work_report", paymentForm.work_report);
              if (paymentForm.qr_code) fd.append("qr_code", paymentForm.qr_code);
              await installationsApi.requestPayment(installationId, fd);
              setSubmitMsg("Payment request submitted. Waiting for admin approval.");
            })}
            className="mt-3 rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            Raise payment request
          </button>
        </WorkflowStepSection>
      )}

      {(canApprovePayment || (step10?.done && isAdminLike)) && (
        <WorkflowStepSection
          title="Step 10 — Approve payment"
          done={Boolean(step10?.done)}
          locked={Boolean(step10?.locked)}
          borderClass="border-indigo-200"
          bgClass="bg-indigo-50"
          summary={installation.status === "Completed"
            ? `Payment approved. Amount paid: ${installation.payment_amount_paid ?? installation.payment_amount_requested ?? "—"}.`
            : "Payment approval completed."}
        >
          <p className="text-xs text-indigo-800">
            Review the engineer payment request. You can change the approved amount before completing payment.
          </p>
          <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
            <Field label="Requested amount" value={installation.payment_amount_requested} />
            <Field label="Requested type" value={installation.payment_type_requested} />
            {(installation.payment_type_requested === "UPI" || adminForm.payment_type === "UPI") && engineerQrPath && (
              <div className="md:col-span-2">
                <PaymentQrPreview path={engineerQrPath} label="Engineer UPI QR code" />
              </div>
            )}
            <div>
              <label className="text-xs uppercase tracking-wide text-slate-500">Approved amount</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={adminForm.payment_amount}
                onChange={(e) => setAdminForm((current) => ({ ...current, payment_amount: e.target.value }))}
                className={`${fieldClass} mt-1`}
              />
            </div>
            <div>
              <label className="text-xs uppercase tracking-wide text-slate-500">Payment type</label>
              <select
                value={adminForm.payment_type}
                onChange={(e) => setAdminForm((current) => ({ ...current, payment_type: e.target.value }))}
                className={`${fieldClass} mt-1`}
              >
                {PAYMENT_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}
              </select>
            </div>
            {adminForm.payment_type === "UPI" && (
              <div className="md:col-span-2">
                <label className="text-xs uppercase tracking-wide text-slate-500">
                  Payment proof <span className="text-rose-600">*</span>
                </label>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                  onChange={(e) => {
                    setApprovalErr("");
                    setAdminForm((current) => ({ ...current, proof_document: e.target.files?.[0] || null }));
                  }}
                  className="mt-1 block w-full text-sm"
                />
                <p className="mt-1 text-xs text-slate-500">
                  Upload the UPI payment screenshot or receipt before approving.
                </p>
              </div>
            )}
          </div>
          {approvalErr && (
            <div className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {approvalErr}
            </div>
          )}
          <button
            type="button"
            disabled={busy}
            onClick={approvePayment}
            className="mt-3 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? "Approving..." : "Approve payment"}
          </button>
          {installation.status === "Completed" && isAdminLike && (
            <button
              type="button"
              disabled={busy || adminForm.payment_amount === ""}
              onClick={() => run(async () => {
                await installationsApi.updatePaymentAmount(installationId, {
                  payment_amount_requested: Number(adminForm.payment_amount),
                  payment_amount_paid: Number(adminForm.payment_amount),
                  payment_type_requested: adminForm.payment_type,
                  payment_type_paid: adminForm.payment_type,
                });
                setSubmitMsg("Payment amount updated.");
              })}
              className="mt-3 ml-2 rounded-md border border-indigo-300 bg-white px-4 py-2 text-sm font-medium text-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Update approved amount
            </button>
          )}
        </WorkflowStepSection>
      )}

      {submitMsg && (
        <div className="rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-800">
          {submitMsg}
        </div>
      )}

      {showSubmittedPaymentQr && isAssignedEngineer && (
        <PaymentQrPreview path={engineerQrPath} label="Submitted UPI QR code" />
      )}

      {installation.status === "Payment Pending" && isAssignedEngineer && !canRaisePayment && (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Payment request submitted. Waiting for admin approval.
        </div>
      )}

      {installation.status === "Completed" && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
          Installation completed and payment approved.
        </div>
      )}
    </div>
  );
}
