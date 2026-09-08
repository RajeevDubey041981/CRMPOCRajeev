import { useState } from "react";
import { useAuth } from "../auth/AuthContext.jsx";
import { NavLink } from "react-router-dom";
import { isIndcoolServiceRole, isOperationsAdminRole, isPartnerAdminRole, isSystemAdminRole } from "../utils/roles.js";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/vendor-dashboard", label: "Vendor Dashboard" },
  {
    label: "Admin",
    children: [
      { to: "/admin/users", label: "Users" },
      { to: "/admin/roles", label: "Roles" },
      { to: "/admin/permissions", label: "Permissions" },
      { to: "/admin/payments", label: "Payment History" },
      { to: "/admin/partner-registrations", label: "Partner Registrations" },
    ],
  },
  { to: "/complaints", label: "Complaints" },
  { to: "/services", label: "Service Requests" },
  { to: "/services/my-units", label: "My Assigned Units" },
  { to: "/items", label: "Item Masters" },
  { to: "/couriers", label: "Courier Masters" },
  { to: "/orders", label: "Order List" },
  { to: "/serials/history", label: "Serial History" },
  { to: "/installations", label: "Installation Requests" },
  { to: "/claims", label: "Claims" },
  {
    label: "Market Admin",
    children: [
      { to: "/market-admin/dashboard", label: "Dashboard" },
      { to: "/market-admin/users", label: "Users" },
      { to: "/market-admin/items", label: "Items" },
      { to: "/market-admin/orders", label: "Orders" },
      { to: "/market-admin/categories", label: "Categories" },
      { to: "/market-admin/vendors", label: "Vendor Registrations" },
      { to: "/market-admin/media", label: "Media Manager" },
    ],
  },
];

function LeafLink({ to, label, disabled }) {
  if (disabled) {
    return (
      <span className="block rounded-md px-3 py-2 text-sm text-slate-500 cursor-not-allowed select-none">
        {label}
      </span>
    );
  }
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `block rounded-md px-3 py-2 text-sm transition ${
          isActive
            ? "bg-brand-600 text-white"
            : "text-slate-200 hover:bg-slate-700 hover:text-white"
        }`
      }
    >
      {label}
    </NavLink>
  );
}

function Group({ label, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between rounded-md px-3 py-2 text-sm font-medium text-slate-100 hover:bg-slate-700"
      >
        <span>{label}</span>
        <span className="text-xs">{open ? "▾" : "▸"}</span>
      </button>
      {open && (
        <div className="ml-3 mt-1 space-y-0.5 border-l border-slate-700 pl-3">
          {children.map((c) => (
            <LeafLink key={c.to} to={c.to} label={c.label} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function Sidebar({ collapsed }) {
  const { user } = useAuth();
  const role = user?.role?.toLowerCase?.() || "";

  // Role-based visibility: vendors and engineers each see a small, focused menu.
  const isVendor = role === "vendor";
  const isEngineer = role === "engineer";
  const isCallcenter = role === "callcenter";
  const isIndcoolService = isIndcoolServiceRole(role);
  const isCourierAdmin = isOperationsAdminRole(role);

  const isPartnerAdmin = isPartnerAdminRole(user?.role);
  const isSystemAdmin = isSystemAdminRole(user?.role);

  const allowedPaths = isVendor
    ? new Set(["/vendor-dashboard", "/orders", "/installations", "/services"])
    : isEngineer
    ? new Set(["/dashboard", "/installations", "/services", "/services/my-units"])
    : isCallcenter
    ? new Set(["/dashboard"])
    : null;

  const filteredNav = NAV
    .filter((it) => {
      if (it.label === "Admin") {
        return isSystemAdmin || isPartnerAdmin;
      }
      return (isCourierAdmin || it.to !== "/couriers") && (isCourierAdmin || it.to !== "/serials/history");
    })
    .map((it) => {
      if (it.label === "Admin" && it.children) {
        const children = it.children.filter((child) => {
          if (child.to === "/admin/partner-registrations") return isPartnerAdmin;
          return isSystemAdmin;
        });
        if (children.length === 0) return null;
        return { ...it, children };
      }
      if (!allowedPaths) return it;
      if (it.children) {
        const children = it.children.filter((c) => allowedPaths.has(c.to));
        if (children.length === 0) return null;
        return { ...it, children };
      }
      return allowedPaths.has(it.to) ? it : null;
    })
    .filter(Boolean);

  return (
    <aside
      className={`relative shrink-0 h-full overflow-x-hidden overflow-y-auto bg-slate-800 transition-all ${
        collapsed ? "w-0 min-w-0 -ml-1" : "w-64 min-w-64"
      }`}
    >
      <div className="px-4 py-5">
        <div className="text-lg font-bold tracking-wide text-white">Indcool CRM</div>
        <div className="text-xs text-slate-400">Service & Operations</div>
      </div>
      <nav className="space-y-1 px-3 pb-6">
        {filteredNav.map((item) =>
          item.children ? (
            <Group key={item.label} label={item.label} children={item.children} />
          ) : (
            <LeafLink key={item.label} to={item.to} label={item.label} disabled={item.disabled} />
          ),
        )}
      </nav>
    </aside>
  );
}
