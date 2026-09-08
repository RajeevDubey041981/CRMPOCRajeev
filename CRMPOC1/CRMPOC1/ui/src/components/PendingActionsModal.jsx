import { useNavigate } from "react-router-dom";

import Modal from "./Modal.jsx";

const MODULE_LABELS = {
  complaints: "Complaint",
  installations: "Installation",
  services: "Service",
  orders: "Order",
  claims: "Claim",
  calls: "Call",
};

function formatWhen(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const diffMs = Date.now() - date.getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleString();
}

export default function PendingActionsModal({
  open,
  onClose,
  items = [],
  total = 0,
  onMarkRead,
}) {
  const navigate = useNavigate();

  function handleDismiss() {
    onMarkRead?.(items.map((item) => item.id));
    onClose?.();
  }

  function openAction(item) {
    onMarkRead?.([item.id]);
    onClose?.();
    navigate(item.href);
  }

  return (
    <Modal
      open={open}
      onClose={handleDismiss}
      title={`Actions pending for you${total ? ` (${total})` : ""}`}
      maxWidth="max-w-2xl"
    >
      {items.length === 0 ? (
        <p className="text-sm text-slate-600">No pending actions right now.</p>
      ) : (
        <ul className="space-y-3">
          {items.map((item) => (
            <li
              key={item.id}
              className={`rounded-lg border p-4 ${item.is_read ? "border-slate-200 bg-white" : "border-amber-200 bg-amber-50"}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium uppercase tracking-wide text-slate-600">
                      {MODULE_LABELS[item.module] || item.module}
                    </span>
                    <span className="text-xs text-slate-500">{formatWhen(item.occurred_at)}</span>
                  </div>
                  <div className="mt-1 text-sm font-semibold text-slate-900">{item.title}</div>
                  <p className="mt-1 text-sm text-slate-700">{item.message}</p>
                  <p className="mt-1 text-xs text-slate-500">Status: {item.entity_status}</p>
                </div>
                <button
                  type="button"
                  onClick={() => openAction(item)}
                  className="shrink-0 rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-700"
                >
                  {item.action_label}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-5 flex justify-end">
        <button
          type="button"
          onClick={handleDismiss}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
        >
          Dismiss
        </button>
      </div>
    </Modal>
  );
}
