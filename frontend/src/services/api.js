import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 120000
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Automatically inject active document_id query parameter
    const docId = localStorage.getItem("document_id");
    if (docId) {
      config.params = config.params || {};
      if (config.params.document_id === undefined) {
        config.params.document_id = docId;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to catch 401 Unauthorized and redirect to login page
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      localStorage.removeItem("document_id");
      localStorage.removeItem("analysis");
      // Redirect to login page
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
