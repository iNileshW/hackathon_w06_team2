import type { Decision, FoiRequest } from "../types";

// Relative API base so calls resolve under whatever path the app is served
// from -- mirrors how ./assets resolve. The lab proxy mounts the app under a
// sub-path, so an absolute "/api" would miss it (404). import.meta.env.BASE_URL
// is "./" (set by vite `base`), giving "./api"; in dev it resolves to
// localhost:5173/api and is proxied to the backend (see vite.config.ts).
const BASE = `${import.meta.env.BASE_URL}api`;

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export function fetchRequests(): Promise<FoiRequest[]> {
  return fetch(`${BASE}/requests`).then(json<FoiRequest[]>);
}

export function fetchRequest(id: string): Promise<FoiRequest> {
  return fetch(`${BASE}/requests/${id}`).then(json<FoiRequest>);
}

export function processRequest(id: string): Promise<FoiRequest> {
  return fetch(`${BASE}/requests/${id}/process`, { method: "POST" }).then(
    json<FoiRequest>,
  );
}

export function decideRequest(
  id: string,
  decision: Decision,
  notes: string,
): Promise<FoiRequest> {
  return fetch(`${BASE}/requests/${id}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, notes }),
  }).then(json<FoiRequest>);
}
