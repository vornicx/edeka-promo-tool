import crypto from "crypto";

export const AUTH_COOKIE = "edeka_promo_session";
export const SESSION_MAX_AGE_SECONDS = 60 * 60 * 12;

function getAuthSecret() {
  return process.env.PROMO_AUTH_SECRET || process.env.PROMO_LOGIN_PASSWORD || "";
}

export function isLoginConfigured() {
  return Boolean(process.env.PROMO_LOGIN_PASSWORD && getAuthSecret());
}

function sign(payload: string) {
  return crypto.createHmac("sha256", getAuthSecret()).update(payload).digest("base64url");
}

export function createSessionToken() {
  const issuedAt = Math.floor(Date.now() / 1000).toString();
  return `${issuedAt}.${sign(issuedAt)}`;
}

export function verifySessionToken(token?: string) {
  if (!token || !getAuthSecret()) return false;

  const [issuedAt, signature] = token.split(".");
  if (!issuedAt || !signature) return false;

  const issuedAtSeconds = Number(issuedAt);
  const nowSeconds = Math.floor(Date.now() / 1000);
  if (!Number.isFinite(issuedAtSeconds) || nowSeconds - issuedAtSeconds > SESSION_MAX_AGE_SECONDS) {
    return false;
  }

  const expected = sign(issuedAt);
  const expectedBuffer = Buffer.from(expected);
  const signatureBuffer = Buffer.from(signature);
  return expectedBuffer.length === signatureBuffer.length && crypto.timingSafeEqual(expectedBuffer, signatureBuffer);
}
