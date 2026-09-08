import { api } from "./client.js";

export const claimsApi = {
  list: (params) => api.get("/api/claims", { params }).then((r) => r.data),
  get: (id) => api.get(`/api/claims/${id}`).then((r) => r.data),
  create: (body) => api.post("/api/claims", body).then((r) => r.data),
  update: (id, body) => api.put(`/api/claims/${id}`, body).then((r) => r.data),
  updateStatus: (id, body) => api.put(`/api/claims/${id}/status`, body).then((r) => r.data),
  remove: (id) => api.delete(`/api/claims/${id}`),
  exportUrl: (params) => {
    const u = new URL("/api/claims/export", api.defaults.baseURL);
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") u.searchParams.set(k, v);
    });
    return u.toString();
  },
};
