import axios from "axios";

const configuredBase = (import.meta.env.VITE_API_BASE_URL || "").trim();
const baseURL = configuredBase && (!import.meta.env.DEV && /localhost|127\.0\.0\.1/i.test(configuredBase))
  ? window.location.origin
  : configuredBase || (import.meta.env.DEV ? "http://localhost:8010" : window.location.origin);

export const api = axios.create({ baseURL, timeout: 60000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("indcool_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("indcool_token");
      localStorage.removeItem("indcool_user");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  },
);
