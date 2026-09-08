export const WORKFLOW_ACTIONS = ["Ask for Invoice", "Request Sent", "Documents Received"];

export const WORKFLOW_ACTION_STYLE = {
  "Ask for Invoice": "bg-yellow-400 text-yellow-950 border-yellow-400",
  "Request Sent": "bg-blue-500 text-white border-blue-500",
  "Documents Received": "bg-emerald-600 text-white border-emerald-600",
};

/** Linked service/installation workflow status for complaint grid rows. */
export function getComplaintWorkflowStatus(complaint) {
  if (!complaint) return null;
  return complaint.service_request_status || complaint.installation_request_status || null;
}

/** Derive invoice/document workflow button state for complaint grid rows. */
export function getComplaintWorkflowAction(complaint) {
  if (!complaint) return "Ask for Invoice";

  if (
    complaint.customer_documents_received
    || complaint.last_action_taken === "Documents Received"
  ) {
    return "Documents Received";
  }

  if (
    complaint.document_link_sent
    || complaint.last_action_taken === "Request Sent"
  ) {
    return "Request Sent";
  }

  if (complaint.last_action_taken === "Ask for Invoice") {
    return "Ask for Invoice";
  }

  return "Ask for Invoice";
}
