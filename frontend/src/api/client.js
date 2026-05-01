import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  timeout: 30000
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response) {
      const { status, statusText, data } = error.response;
      const detail = data?.detail || data?.message || JSON.stringify(data);
      error.message = `${status} ${statusText}: ${detail}`;
    }
    return Promise.reject(error);
  }
);

export default api;
