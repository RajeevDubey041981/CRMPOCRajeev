export function isMissingItemCode(itemCode) {
  const value = String(itemCode || "").trim();
  return !value || value === "-";
}
