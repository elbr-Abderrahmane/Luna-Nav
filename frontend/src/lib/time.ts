/** "2027-01-10T00:00:00Z": ISO-8601 UTC, ends with Z, no milliseconds (README 5.1). */
export const toUtcString = (d: Date): string => d.toISOString().replace(/\.\d{3}Z$/, "Z");

/** Date input (YYYY-MM-DD) + time (HH:MM), read as UTC, to the contract string. */
export const utcFromParts = (date: string, time = "00:00"): string => toUtcString(new Date(`${date}T${time}:00Z`));

export const isUtcString = (s: string): boolean => /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(s);

export const dateOnly = (utc: string): string => utc.slice(0, 10);
