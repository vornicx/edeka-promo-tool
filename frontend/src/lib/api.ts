const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/promo";
const API_ROOT = API_BASE.replace(/\/api\/promo\/?$/, "");
const SETTINGS_API_BASE = `${API_ROOT}/api/settings`;
const PRODUCTS_API_BASE = `${API_ROOT}/api/products`;

export interface PromotionData {
  campaign_kind: "product" | "event";
  product: string;
  category?: string;
  price: string;
  old_price?: string;
  validity: string;
  origin?: string;
  claim?: string;
  event_description?: string;
  product_image?: string;
  format: string;
  style: string;
  tone: string;
  differentiation_level: string;
  use_ai_planning: boolean;
}

export interface Motif {
  value: string;
  name: string;
  category: string;
  image_url: string;
  source: "builtin" | "custom";
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
  generation_mode: "ai" | "local" | "local_fallback";
  generation_note: string;
}

export interface ComposeResponse {
  session_id: string;
  image_url: string;
  direction: string;
}

export interface AISettings {
  api_key: string;
  selected_model: string;
  image_model: string;
  enabled: boolean;
  has_api_key: boolean;
  masked_api_key: string;
  settings_path: string;
}

export interface AIModelInfo {
  id: string;
  name: string;
  provider: string;
  vision: boolean;
  free: boolean;
  cost_est_design: string;
  quality: number;
  context: string;
  description: string;
}

export interface SaveAISettingsPayload {
  api_key?: string;
  selected_model: string;
  image_model?: string;
  enabled: boolean;
}

async function handleResponse<T>(res: Response, errorMsg: string): Promise<T> {
  if (!res.ok) {
    let detail = errorMsg;
    try {
      const err = await res.json();
      detail = err.detail || err.message || errorMsg;
    } catch {
      detail = `HTTP-Fehler ${res.status}`;
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

function getNetworkErrorMessage() {
  return "Der Promo-Server konnte nicht erreicht werden. Bitte laden Sie die Seite neu oder informieren Sie den Kundendienst.";
}

export async function createPromo(data: PromotionData): Promise<CreatePromoResponse> {
  try {
    const res = await fetch(`${API_BASE}/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return handleResponse<CreatePromoResponse>(res, "Promotion konnte nicht erstellt werden");
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(getNetworkErrorMessage());
    }
    throw error;
  }
}

export async function composePromo(
  sessionId: string,
  directionIndex: number
): Promise<ComposeResponse> {
  try {
    const res = await fetch(`${API_BASE}/compose`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, direction_index: directionIndex }),
    });
    return handleResponse<ComposeResponse>(res, "Promotion konnte nicht gestaltet werden");
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(getNetworkErrorMessage());
    }
    throw error;
  }
}

export async function exportPromo(
  sessionId: string,
  format: string
): Promise<Blob> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, format }),
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(getNetworkErrorMessage());
    }
    throw error;
  }
  if (!res.ok) {
    let detail = "Export konnte nicht erstellt werden";
    try {
      const err = await res.json();
      detail = err.detail || err.message || detail;
    } catch {
      detail = `HTTP-Fehler ${res.status}`;
    }
    throw new Error(detail);
  }
  return res.blob();
}

export function getImageUrl(sessionId: string): string {
  return `${API_BASE}/image/${sessionId}`;
}

export async function getAISettings(): Promise<AISettings> {
  const res = await fetch(SETTINGS_API_BASE);
  return handleResponse<AISettings>(res, "KI-Einstellungen konnten nicht geladen werden");
}

export async function getAIModels(): Promise<AIModelInfo[]> {
  const res = await fetch(`${SETTINGS_API_BASE}/models`);
  return handleResponse<AIModelInfo[]>(res, "KI-Modelle konnten nicht geladen werden");
}

export async function saveAISettings(data: SaveAISettingsPayload): Promise<AISettings> {
  const res = await fetch(SETTINGS_API_BASE, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<AISettings>(res, "KI-Einstellungen konnten nicht gespeichert werden");
}

export interface CustomProduct {
  id: string;
  name: string;
  category: string;
  image_url: string;
  created: string;
}

export interface CreateProductPayload {
  name: string;
  category?: string;
  image_base64: string;
}

export function getProductImageUrl(product: CustomProduct): string {
  return `${API_ROOT}${product.image_url}`;
}

export async function listProducts(): Promise<CustomProduct[]> {
  const res = await fetch(PRODUCTS_API_BASE);
  return handleResponse<CustomProduct[]>(res, "Produkte konnten nicht geladen werden");
}

export async function listMotifs(): Promise<Motif[]> {
  const res = await fetch(`${PRODUCTS_API_BASE}/catalog`);
  return handleResponse<Motif[]>(res, "Motive konnten nicht geladen werden");
}

export function getMotifImageUrl(motif: Motif): string {
  return `${API_ROOT}${motif.image_url}`;
}

export interface ExampleParams {
  campaign_kind?: "product" | "event";
  style: string;
  tone: string;
  level: string;
  format?: string;
  product?: string;
  price?: string;
  old_price?: string;
  validity?: string;
  claim?: string;
  origin?: string;
  category?: string;
  product_image?: string;
}

// Cache-buster fixed per page load: each reload fetches fresh previews
// (so design changes show up), but identical thumbnails stay cached within a
// session. Avoids the browser serving stale previews after a redesign.
const PREVIEW_BUST = Date.now().toString(36);

export function exampleImageUrl(p: ExampleParams): string {
  const params = new URLSearchParams();
  Object.entries(p).forEach(([k, v]) => {
    if (v) params.set(k, String(v));
  });
  params.set("_", PREVIEW_BUST);
  return `${API_ROOT}/api/examples?${params.toString()}`;
}

export async function createProduct(data: CreateProductPayload): Promise<CustomProduct> {
  const res = await fetch(PRODUCTS_API_BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<CustomProduct>(res, "Produkt konnte nicht gespeichert werden");
}

export async function deleteProduct(id: string): Promise<void> {
  const res = await fetch(`${PRODUCTS_API_BASE}/${id}`, { method: "DELETE" });
  await handleResponse<{ status: string }>(res, "Produkt konnte nicht gelöscht werden");
}
