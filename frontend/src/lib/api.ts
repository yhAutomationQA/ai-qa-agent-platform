import axios from "axios";

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export async function fetchAgents() {
  const { data } = await apiClient.get("/agents");
  return data;
}

export async function fetchTestCases() {
  const { data } = await apiClient.get("/tests");
  return data;
}

export async function fetchRuns() {
  const { data } = await apiClient.get("/runs");
  return data;
}

export async function fetchPrompts() {
  const { data } = await apiClient.get("/prompts");
  return data;
}

export default apiClient;
