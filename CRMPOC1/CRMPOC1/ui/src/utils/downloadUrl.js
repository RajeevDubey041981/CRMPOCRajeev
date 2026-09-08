export function toDownloadUrl(path) {
  if (!path) return "#";
  try {
    if (/^https?:\/\//i.test(path)) return path;
    const apiBase = import.meta.env.VITE_API_BASE_URL || window.location.origin;
    return new URL(path, apiBase).toString();
  } catch {
    return "#";
  }
}
