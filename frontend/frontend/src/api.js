import axios from "axios";

const apiUrl = import.meta.env.VITE_API_URL || (
  import.meta.env.DEV ? "http://127.0.0.1:8000" : "https://task-manager-turl.onrender.com"
);
const baseURL = apiUrl.trim().replace(/\/+$/, "").replace(/\/api$/, "") + "/api";
const API = axios.create({ baseURL });
const authAPI = axios.create({ baseURL });

let telegramSession;

API.interceptors.request.use(async (request) => {
  const initData = window.Telegram?.WebApp?.initData;
  if (!initData) return request;

  if (telegramSession?.initData !== initData) {
    const session = {
      initData,
      token: authAPI.post("/auth/telegram", { init_data: initData })
        .then(({ data }) => data.access_token)
        .catch((error) => {
          if (telegramSession === session) telegramSession = undefined;
          throw error;
        }),
    };
    telegramSession = session;
  }

  request.headers.set("Authorization", `Bearer ${await telegramSession.token}`);
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
