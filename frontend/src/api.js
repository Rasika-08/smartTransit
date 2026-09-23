const API_URL = "http://127.0.0.1:8000";

export const apiFetch = async (url, options = {}) => {
  const token = localStorage.getItem("access_token");

  const headers = {
    ...(options.headers || {})
  };

  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers
  });

  if (response.status === 401) {
    console.warn("Authentication expired or token missing.");
  }

  return response;
};

export { API_URL };