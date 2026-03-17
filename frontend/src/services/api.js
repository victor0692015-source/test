const API_URL = import.meta.env.VITE_API_URL || '/api';

function buildErrorMessage(errorBody, fallback) {
  if (typeof errorBody === 'string' && errorBody.trim()) return errorBody;
  if (errorBody?.message) return errorBody.message;
  return fallback;
}

export async function request(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers
    });
  } catch (networkError) {
    throw new Error('Backend недоступен. Проверьте, что API запущен на порту 4000.');
  }

  if (!response.ok) {
    const text = await response.text();
    let parsed;
    try {
      parsed = text ? JSON.parse(text) : null;
    } catch {
      parsed = text;
    }

    throw new Error(buildErrorMessage(parsed, `HTTP ${response.status}`));
  }

  if (response.status === 204) return null;
  return response.json();
}
