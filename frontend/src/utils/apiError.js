export function formatApiError(error) {
  if (error?.response) {
    const { status, statusText, data } = error.response;
    const detail = data?.detail || data?.message || JSON.stringify(data);
    return `${status} ${statusText}: ${detail}`;
  }
  return error?.message || "Error desconocido al conectar con el backend.";
}
