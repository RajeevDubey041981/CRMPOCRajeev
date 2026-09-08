import { api } from "./client.js";

export async function fetchPendingActions(limit = 15) {
  const { data } = await api.get("/api/pending-actions", { params: { limit } });
  return data;
}

export async function markPendingActionsRead(ids = null) {
  const { data } = await api.post("/api/pending-actions/mark-read", { ids });
  return data;
}
