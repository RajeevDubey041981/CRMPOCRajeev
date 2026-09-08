export const ORDER_ITEM_CSV_PREFIX = [
  "ID",
  "Item ID",
  "Item Name",
  "Item Code",
];

export const ORDER_ITEM_CSV_SUFFIX = [
  "PCB Warranty",
  "Component Warranty",
  "Machine Warranty",
  "Free Services",
  "Dry Free Services",
  "Wet Free Services",
  "Installation Status",
];

export const SERIAL_COLUMN_NAMES = ["Serial Number 1", "Serial Number 2"];

/** @deprecated Use buildOrderItemCsvColumns(serialColumnCount) */
export const ORDER_ITEM_IMPORT_EXPORT_COLUMNS = [
  ...ORDER_ITEM_CSV_PREFIX,
  ...SERIAL_COLUMN_NAMES,
  ...ORDER_ITEM_CSV_SUFFIX,
];

export function serialColumnsForCount(serialColumnCount) {
  const count = Math.max(0, Math.min(2, Number(serialColumnCount) || 0));
  return SERIAL_COLUMN_NAMES.slice(0, count);
}

export function buildOrderItemCsvColumns(serialColumnCount) {
  return [
    ...ORDER_ITEM_CSV_PREFIX,
    ...serialColumnsForCount(serialColumnCount),
    ...ORDER_ITEM_CSV_SUFFIX,
  ];
}

export function maxSerialCountForItems(items, itemCode = "") {
  const rows = (items || []).filter((item) => (
    !itemCode || (item.item_code || "") === itemCode
  ));
  if (rows.length === 0) return 0;
  return Math.max(...rows.map((item) => Number(item.serial_count ?? 1)));
}

export function parseOrderItemCsvHeader(headerRow) {
  const columns = (headerRow || []).map((value) => (value || "").trim());
  const prefixEnd = ORDER_ITEM_CSV_PREFIX.length;
  const suffixStart = columns.length - ORDER_ITEM_CSV_SUFFIX.length;

  if (suffixStart < prefixEnd) return null;
  if (!ORDER_ITEM_CSV_PREFIX.every((name, idx) => columns[idx] === name)) return null;
  if (!ORDER_ITEM_CSV_SUFFIX.every((name, idx) => columns[suffixStart + idx] === name)) {
    return null;
  }

  const serialColumns = columns.slice(prefixEnd, suffixStart);
  if (serialColumns.length > 2) return null;
  if (!serialColumns.every((name, idx) => name === SERIAL_COLUMN_NAMES[idx])) return null;

  return {
    columns,
    serialColumnCount: serialColumns.length,
  };
}

export function rowValuesToCells(columns, values) {
  return Object.fromEntries(columns.map((column, idx) => [column, values[idx] ?? ""]));
}
