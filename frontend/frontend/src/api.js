import axios from "axios";

const address = import.meta.env.VITE_API_URL || (
  import.meta.env.DEV ? "http://127.0.0.1:8000" : "https://task-manager-turl.onrender.com"
);
const baseURL = address.trim().replace(/\/+$/, "").replace(/\/api$/, "") + "/api";
const API = axios.create({ baseURL });
const sessionAPI = axios.create({ baseURL });
let session;

API.interceptors.request.use(async (request) => {
  const initData = window.Telegram?.WebApp?.initData;
  if (!initData || request.url === "/auto/catalog") return request;
  if (session?.initData !== initData) {
    const current = {
      initData,
      token: sessionAPI.post("/auth/telegram", { init_data: initData })
        .then(({ data }) => data.access_token)
        .catch((error) => {
          if (session === current) session = undefined;
          throw error;
        }),
    };
    session = current;
  }
  request.headers.set("Authorization", `Bearer ${await session.token}`);
  return request;
});

export async function request(path, method = "get", data, params) {
  return (await API({ url: "/auto" + path, method, data, params })).data;
}

export function errorText(error) {
  const detail = error.response?.data?.detail;
  if (error.response?.status === 401) return "Ilovani Telegram bot orqali oching yoki qayta oching.";
  return typeof detail === "string" ? detail
    : Array.isArray(detail) ? "Kiritilgan maydonlarni tekshiring."
    : "Server bilan bog‘lanib bo‘lmadi. Qayta urinib ko‘ring.";
}
