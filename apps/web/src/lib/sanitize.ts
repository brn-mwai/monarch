/**
 * Input sanitization for scan text.
 * Prevents XSS via injected HTML, script tags, event handlers,
 * and encoded payloads. Defense-in-depth: the server re-validates.
 */

export function stripHTML(input: string): string {
  return input
    .replace(/<[^>]*>/g, "")
    .replace(/javascript:/gi, "")
    .replace(/data:text\/html/gi, "")
    .replace(/on\w+\s*=/gi, "")
    .replace(/expression\s*\(/gi, "")
    .trim();
}

export function validateTextInput(input: string): string {
  let clean = input.replace(/\0/g, "");
  clean = clean.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, "");
  clean = clean.replace(/[\u200E\u200F\u202A-\u202E\u2066-\u2069]/g, "");
  clean = clean.normalize("NFC");
  return clean;
}

export function sanitizeScanInput(input: string): string {
  let text = validateTextInput(input);
  text = stripHTML(text);
  if (text.length > 10000) text = text.slice(0, 10000);
  return text;
}
