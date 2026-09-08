import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../auth/AuthContext.jsx";

function isCallcenterAllowedPath(pathname) {
  if (pathname === "/dashboard") return true;
  if (pathname === "/complaints/new") return true;
  if (/^\/complaints\/\d+$/.test(pathname)) return true;
  return false;
}

export default function CallcenterGuard({ children }) {
  const { user } = useAuth();
  const { pathname } = useLocation();
  const role = user?.role?.toLowerCase?.() || "";

  if (role === "callcenter" && !isCallcenterAllowedPath(pathname)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
