import { api } from "./client.js";

export const marketApi = {
  dashboard: () => api.get("/api/market/dashboard").then((r) => r.data),

  // Users
  listUsers: (params) => api.get("/api/market/users", { params }).then((r) => r.data),
  getUser: (id) => api.get(`/api/market/users/${id}`).then((r) => r.data),
  createUser: (body) => api.post("/api/market/users", body).then((r) => r.data),
  updateUser: (id, body) => api.put(`/api/market/users/${id}`, body).then((r) => r.data),
  deleteUser: (id) => api.delete(`/api/market/users/${id}`),
  lookupUsers: () => api.get("/api/market/users/lookup").then((r) => r.data),

  // Categories
  listCategories: () => api.get("/api/market/categories").then((r) => r.data),
  createCategory: (body) => api.post("/api/market/categories", body).then((r) => r.data),
  updateCategory: (id, body) =>
    api.put(`/api/market/categories/${id}`, body).then((r) => r.data),
  deleteCategory: (id) => api.delete(`/api/market/categories/${id}`),

  // Items
  listItems: (params) => api.get("/api/market/items", { params }).then((r) => r.data),
  getItem: (id) => api.get(`/api/market/items/${id}`).then((r) => r.data),
  createItem: (body) => api.post("/api/market/items", body).then((r) => r.data),
  updateItem: (id, body) => api.put(`/api/market/items/${id}`, body).then((r) => r.data),
  deleteItem: (id) => api.delete(`/api/market/items/${id}`),

  // Orders
  listOrders: (params) => api.get("/api/market/orders", { params }).then((r) => r.data),
  getOrder: (id) => api.get(`/api/market/orders/${id}`).then((r) => r.data),
  createOrder: (body) => api.post("/api/market/orders", body).then((r) => r.data),
  updateOrder: (id, body) => api.put(`/api/market/orders/${id}`, body).then((r) => r.data),
  deleteOrder: (id) => api.delete(`/api/market/orders/${id}`),
};
