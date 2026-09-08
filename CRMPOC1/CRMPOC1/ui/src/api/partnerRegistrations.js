import { api } from "./client.js";

export const partnerRegistrationsApi = {
  meta: () => api.get("/api/partner-registrations/meta").then((r) => r.data),
  list: (params) => api.get("/api/partner-registrations", { params }).then((r) => r.data),
  get: (id) => api.get(`/api/partner-registrations/${id}`).then((r) => r.data),
  resendEmail: (id) => api.post(`/api/partner-registrations/${id}/resend-email`).then((r) => r.data),
  invite: (body) => api.post("/api/partner-registrations/invite", body).then((r) => r.data),
  update: (id, body) => api.put(`/api/partner-registrations/${id}`, body).then((r) => r.data),
  delete: (id) => api.delete(`/api/partner-registrations/${id}`),
};
