import { Link } from "react-router-dom";

import { getLinkedRequestInfo } from "../../utils/complaintLinks.js";

export default function LinkedRequestCell({ complaint, onClick, plainInstallationLink = false }) {
  const linked = getLinkedRequestInfo(complaint);
  if (!linked) {
    return <span className="text-slate-400">—</span>;
  }

  if (plainInstallationLink && linked.kind === "installation") {
    return <span className="font-mono text-slate-600">{linked.label}</span>;
  }

  return (
    <Link
      to={linked.path}
      onClick={(e) => {
        e.stopPropagation();
        onClick?.(e);
      }}
      className="font-mono text-brand-600 underline decoration-brand-300 underline-offset-2 hover:text-brand-700"
    >
      {linked.label}
    </Link>
  );
}
