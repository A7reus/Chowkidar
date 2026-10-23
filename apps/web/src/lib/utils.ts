import { clsx, type ClassValue } from "clsx";
import { format, formatDistanceToNow, parseISO } from "date-fns";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(value: string | Date | null | undefined, pattern = "dd MMM yyyy") {
  if (!value) return "—";
  try {
    const date = typeof value === "string" ? parseISO(value) : value;
    return format(date, pattern);
  } catch {
    return "—";
  }
}

export function formatDateTime(value: string | Date | null | undefined) {
  return formatDate(value, "dd MMM yyyy, HH:mm");
}

export function formatRelative(value: string | Date | null | undefined) {
  if (!value) return "—";
  try {
    const date = typeof value === "string" ? parseISO(value) : value;
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return "—";
  }
}

export function titleCase(value: string | null | undefined) {
  if (!value) return "";
  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function initials(name: string | null | undefined) {
  if (!name) return "?";
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function truncate(value: string, length = 80) {
  return value.length > length ? `${value.slice(0, length - 1)}…` : value;
}

export function formatNumber(value: number | null | undefined) {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatPercent(value: number | null | undefined, digits = 1) {
  if (value == null) return "—";
  return `${value.toFixed(digits)}%`;
}

export function shortHash(value: string | null | undefined, length = 10) {
  if (!value) return "—";
  return value.length <= length ? value : `${value.slice(0, length)}…`;
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function humanizeAction(action: string) {
  return action
    .replaceAll(".", " · ")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function pluralize(count: number, singular: string, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}
