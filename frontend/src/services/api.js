import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Attach Supabase Auth Bearer token if present
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("supabase_auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail || error.message || "An unexpected error occurred.";
    console.error("API Error:", message);
    return Promise.reject(new Error(message));
  }
);

export default api;
