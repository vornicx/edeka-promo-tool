const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/_/backend/api/promo";

export interface PromotionData {
  product: string;
  category?: string;
  price: string;
  old_price?: string;
  validity: string;
  origin?: string;
  claim?: string;
  format: string;
  tone: string;
  differentiation_level: string;
}

export interface CreativeDirection {
  name: string;
  intent: string;
  composition: string;
  palette: string[];
  text_safe_area: string;
  boldness: string;
  waschbaer_presence: string;
}

export interface CreatePromoResponse {
  session_id: string;
  spec: Record<string, unknown>;
  enrichment: Record<string, unknown>;
  directions: CreativeDirection[];
}

export interface ComposeResponse {
  session_id: string;
  image_url: string;
  direction: string;
}

async function handleResponse<T>(res: Response, errorMsg: string): Promise<T> {
  if (!res.ok) {
    let detail = errorMsg;
    try {
      const err = await res.json();
      detail = err.detail || err.message || errorMsg;
    } catch {
      detail = `Error HTTP ${res.status}`;
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function createPromo(data: PromotionData): Promise<CreatePromoResponse> {
  const res = await fetch(`${API_BASE}/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<CreatePromoResponse>(res, "Error al crear promoción");
}

export async function composePromo(
  sessionId: string,
  directionIndex: number
): Promise<ComposeResponse> {
  const res = await fetch(`${API_BASE}/compose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, direction_index: directionIndex }),
  });
  return handleResponse<ComposeResponse>(res, "Error al componer");
}

export async function exportPromo(
  sessionId: string,
  format: string
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, format }),
  });
  if (!res.ok) {
    let detail = "Error al exportar";
    try {
      const err = await res.json();
      detail = err.detail || err.message || detail;
    } catch {
      detail = `Error HTTP ${res.status}`;
    }
    throw new Error(detail);
  }
  return res.blob();
}

export function getImageUrl(sessionId: string): string {
  return `${API_BASE}/image/${sessionId}`;
}
