export function formatApiError(error, fallback = "Something went wrong") {
  if (!error) return fallback;
  if (typeof error === "string") return error;

  const detail = error.response?.data?.detail ?? error.detail ?? error;

  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg || item?.message || JSON.stringify(item)).join("; ");
  }
  if (detail && typeof detail === "object") {
    return detail.message || detail.msg || JSON.stringify(detail);
  }
  if (typeof detail === "string") return detail;
  if (typeof error.message === "string") return error.message;
  return fallback;
}
