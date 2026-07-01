// Trigger a browser download for in-memory content.
export function downloadBlob(content, filename, type = 'text/plain') {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// YYYY-MM-DD stamp for filenames.
export function todayStamp() {
  return new Date().toISOString().slice(0, 10);
}
