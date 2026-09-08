import { api } from "./client.js";

export const usersAdminApi = {
  list: (params) => api.get("/api/users", { params }).then((r) => r.data),
  get: (id) => api.get(`/api/users/${id}`).then((r) => r.data),
  create: (body) => api.post("/api/users", body).then((r) => r.data),
  update: (id, body) => api.put(`/api/users/${id}`, body).then((r) => r.data),
  deactivate: (id) => api.delete(`/api/users/${id}`),
  resetPassword: (id, new_password) =>
    api.put(`/api/users/${id}/reset-password`, { new_password }),
};

export const rolesApi = {
  list: () => api.get("/api/roles").then((r) => r.data),
  get: (id) => api.get(`/api/roles/${id}`).then((r) => r.data),
  create: (body) => api.post("/api/roles", body).then((r) => r.data),
  update: (id, body) => api.put(`/api/roles/${id}`, body).then((r) => r.data),
  remove: (id) => api.delete(`/api/roles/${id}`),
  setPermissions: (id, permissions) =>
    api.put(`/api/roles/${id}/permissions`, { permissions }).then((r) => r.data),
  modules: () => api.get("/api/roles/modules").then((r) => r.data),
  matrix: () => api.get("/api/roles/matrix").then((r) => r.data),
};
