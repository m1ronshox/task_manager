import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || (
    import.meta.env.DEV ? "http://127.0.0.1:8000/api" : "/api"
  ),
});

API.interceptors.request.use((request) => {
  const initData = window.Telegram?.WebApp?.initData;
  if (initData) request.headers.set("X-Telegram-Init-Data", initData);
  return request;
});

export const getTasks = () => {
  return API.get("/tasks");
};

export const createTask = (title) => {
  return API.post("/tasks", { title });
};

export const updateTask = (taskId, data) => {
  return API.patch(`/tasks/${taskId}`, data);
};

export const deleteTask = (taskId) => {
  return API.delete(`/tasks/${taskId}`);
};

export default API;
