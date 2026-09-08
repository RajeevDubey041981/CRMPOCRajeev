import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { couriersApi } from "../../api/couriers.js";

export default function CourierCreate() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState("");
  const [form, setForm] = useState({
    courier_name: "",
    contact_name: "",
    contact_mobile: "",
    email: "",
    address: "",
  });

  function set(field, value) { setForm((f) => ({ ...f, [field]: value })); }

  async function submit(e) {
    e.preventDefault();
    setErr("");
    if (!form.courier_name.trim()) {
      setErr("Courier name is required");
      return;
    }
    setSubmitting(true);
    try {
      const body = {
        courier_name: form.courier_name.trim(),
        contact_name: form.contact_name.trim() || null,
        contact_mobile: form.contact_mobile.trim() || null,
        email: form.email.trim() || null,
        address: form.address.trim() || null,
      };
      const created = await couriersApi.create(body);
      navigate(`/couriers/${created.id}`, {
        state: { success: "Courier created successfully." },
      });
    } catch (e) {
      const detail = e.response?.data?.detail;
      setErr(Array.isArray(detail) ? detail.map((d) => d.msg).join("; ") : detail || "Failed to create courier");
    } finally {
      setSubmitting(false);
    }
  }

  const fieldClass = "w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500";
  const labelClass = "mb-1 block text-sm font-medium text-slate-700";

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-semibold text-slate-800">New Courier</h1>

      {err && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{err}</div>}

      <form onSubmit={submit} className="space-y-4 rounded-lg bg-white p-6 shadow-sm">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className={labelClass}>Courier Name *</label>
            <input
              required
              value={form.courier_name}
              onChange={(e) => set("courier_name", e.target.value)}
              className={fieldClass}
              placeholder="e.g. Blue Dart"
            />
          </div>
          <div>
            <label className={labelClass}>Contact Name</label>
            <input
              value={form.contact_name}
              onChange={(e) => set("contact_name", e.target.value)}
              className={fieldClass}
              placeholder="e.g. Ramesh Kumar"
            />
          </div>
          <div>
            <label className={labelClass}>Contact Mobile</label>
            <input
              value={form.contact_mobile}
              onChange={(e) => set("contact_mobile", e.target.value)}
              className={fieldClass}
              placeholder="e.g. 9876543210"
            />
          </div>
          <div>
            <label className={labelClass}>Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => set("email", e.target.value)}
              className={fieldClass}
              placeholder="e.g. contact@bluedart.com"
            />
          </div>
        </div>

        <div>
          <label className={labelClass}>Address</label>
          <textarea
            rows={3}
            value={form.address}
            onChange={(e) => set("address", e.target.value)}
            className={fieldClass}
            placeholder="Optional address"
          />
        </div>

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={() => navigate("/couriers")}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm"
          >Cancel</button>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {submitting ? "Saving…" : "Create Courier"}
          </button>
        </div>
      </form>
    </div>
  );
}
