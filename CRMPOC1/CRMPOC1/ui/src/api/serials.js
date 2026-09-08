import { api } from "./client.js";

export const serialApi = {
  search: (query) => api.get(`/api/serials/search?query=${encodeURIComponent(query)}`),
  lookup: (serialNo) => api.get(`/api/serials/lookup?serial_no=${encodeURIComponent(serialNo)}`),
  historySearch: (query) => api.get(`/api/serials/history/search?query=${encodeURIComponent(query)}`),
  history: (serialNo) => api.get(`/api/serials/${encodeURIComponent(serialNo)}/history`),
};
