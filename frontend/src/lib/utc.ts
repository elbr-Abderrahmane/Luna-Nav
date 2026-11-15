/** "2027-01-10T21:36:48Z" -> "2027-01-10 21:36 UTC" */
export const formatUtc = (utc: string): string => utc.slice(0, 16).replace("T", " ") + " UTC";
