import { api } from "./client.js";

export const projectsApi = {
  list: (params) => api.get("/api/projects", { params }).then((r) => r.data),
  get: (id) => api.get(`/api/projects/${id}`).then((r) => r.data),
  create: (body) => api.post("/api/projects", body).then((r) => r.data),
  update: (id, body) => api.patch(`/api/projects/${id}`, body).then((r) => r.data),
  remove: (id) => api.delete(`/api/projects/${id}`),

  addTask: (projectId, body) =>
    api.post(`/api/projects/${projectId}/tasks`, body).then((r) => r.data),
  updateTask: (projectId, taskId, body) =>
    api.patch(`/api/projects/${projectId}/tasks/${taskId}`, body).then((r) => r.data),
  deleteTask: (projectId, taskId) =>
    api.delete(`/api/projects/${projectId}/tasks/${taskId}`),
  runTask: (projectId, taskId, inputOverride) =>
    api.post(`/api/projects/${projectId}/tasks/${taskId}/run`, inputOverride || null).then((r) => r.data),
  resetTask: (projectId, taskId) =>
    api.post(`/api/projects/${projectId}/tasks/${taskId}/reset`).then((r) => r.data),

  runProject: (projectId, resume = false) =>
    api.post(`/api/projects/${projectId}/run`, null, { params: { resume } }).then((r) => r.data),
};
