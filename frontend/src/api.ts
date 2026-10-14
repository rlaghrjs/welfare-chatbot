export const API_BASE_URL = (import.meta.env?.VITE_API_URL ||
  (globalThis.location?.hostname === "10.0.2.2" ? "http://10.0.2.2:8000" : "http://127.0.0.1:8000")).replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}
const KEY = "welfareInstallation";
type Installation = { installation_id: string; secret: string };
let registration: Promise<Installation> | undefined;

function localInstallation(): Installation {
  const stored = localStorage.getItem(KEY);
  if (stored) {
    const data = JSON.parse(stored) as Installation;
    if (typeof data.installation_id !== "string" || typeof data.secret !== "string") {
      throw new Error("앱 식별 정보를 읽을 수 없습니다.");
    }
    return data;
  }
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  const data = {
    installation_id: crypto.randomUUID(),
    secret: Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join(""),
  };
  localStorage.setItem(KEY, JSON.stringify(data));
  return data;
}

async function ensureInstallation(): Promise<Installation> {
  if (!registration) {
    registration = (async () => {
      const data = localInstallation();
      const response = await fetch(`${API_BASE_URL}/api/installations`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
      });
      if (!response.ok) throw new ApiError("앱 연결에 실패했습니다. 잠시 후 다시 시도해주세요.", response.status);
      return data;
    })().catch((error) => { registration = undefined; throw error; });
  }
  return registration;
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const data = await ensureInstallation();
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${data.installation_id}.${data.secret}`);
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    if (response.status === 401) registration = undefined;
    const body = await response.json().catch(() => ({}));
    throw new ApiError(typeof body.detail === "string" ? body.detail : "요청을 처리하지 못했습니다.", response.status);
  }
  return response;
}

export function clearLocalInstallation() {
  localStorage.removeItem(KEY);
  registration = undefined;
}
