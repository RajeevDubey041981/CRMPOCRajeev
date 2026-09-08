/** Canonical call-center installation workflow URL (scrolls to workflow on load). */
export function getInstallationWorkflowPath(installationId) {
  if (!installationId) return null;
  return `/installations/${installationId}?edit=1`;
}

/** Canonical service request workflow URL. */
export function getServiceRequestPath(serviceRequestId) {
  if (!serviceRequestId) return null;
  return `/services/${serviceRequestId}`;
}

/** Best full-page route when opening a complaint from list/dashboard/modal. */
export function getComplaintOpenPath(complaint, options = {}) {
  const { preferInstallationWorkflow = true, preferServiceWorkflow = true } = options;
  if (!complaint) return "/complaints";
  const queryType = (complaint.query_type || "").toLowerCase();
  if (
    preferInstallationWorkflow
    && queryType === "installation"
    && complaint.installation_request_id
  ) {
    return getInstallationWorkflowPath(complaint.installation_request_id);
  }
  if (
    preferServiceWorkflow
    && queryType === "service"
    && complaint.service_request_id
  ) {
    return getServiceRequestPath(complaint.service_request_id);
  }
  return `/complaints/${complaint.id}`;
}

/** Linked service or installation request for a complaint list/detail row. */
export function getLinkedRequestInfo(complaint) {
  if (!complaint) return null;

  const queryType = (complaint.query_type || "").toLowerCase();

  if (queryType === "installation" && complaint.installation_request_id) {
    return {
      kind: "installation",
      id: complaint.installation_request_id,
      label: `#${complaint.installation_request_id}`,
      path: getInstallationWorkflowPath(complaint.installation_request_id),
    };
  }

  if (complaint.service_request_id) {
    return {
      kind: "service",
      id: complaint.service_request_id,
      label: complaint.service_request_no || `#${complaint.service_request_id}`,
      path: getServiceRequestPath(complaint.service_request_id),
    };
  }

  if (complaint.installation_request_id) {
    return {
      kind: "installation",
      id: complaint.installation_request_id,
      label: `#${complaint.installation_request_id}`,
      path: getInstallationWorkflowPath(complaint.installation_request_id),
    };
  }

  return null;
}

export function linkedRequestColumnLabel(complaint) {
  const queryType = (complaint?.query_type || "").toLowerCase();
  if (queryType === "installation") return "Installation Request";
  if (queryType === "service") return "Service Request";
  return "Linked Request";
}

/** Lock reject/delete after admin assigns an engineer to an installation request. */
export function isInstallationEngineerAssigned(complaint) {
  if (!complaint) return false;
  if ((complaint.query_type || "").toLowerCase() !== "installation") return false;
  if (!complaint.installation_request_id) return false;
  return Boolean(complaint.assigned_engineer_name || complaint.assigned_engineer);
}
