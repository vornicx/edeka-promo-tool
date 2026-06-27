import { NextRequest, NextResponse } from "next/server";

const AUTH_COOKIE = "edeka_promo_session";
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 12;

function getSecret() {
  return process.env.PROMO_AUTH_SECRET || process.env.PROMO_LOGIN_PASSWORD || "";
}

function isPublicPath(pathname: string) {
  return (
    pathname === "/" ||
    pathname === "/login" ||
    pathname.startsWith("/api/auth/") ||
    pathname.startsWith("/_next/") ||
    pathname === "/favicon.ico" ||
    pathname === "/waschbaer_logo.png" ||
    /\.[a-zA-Z0-9]+$/.test(pathname)
  );
}

function toBase64Url(buffer: ArrayBuffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

async function sign(payload: string, secret: string) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  return toBase64Url(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(payload)));
}

async function hasValidSession(request: NextRequest) {
  const secret = getSecret();
  const token = request.cookies.get(AUTH_COOKIE)?.value;
  if (!secret || !token) return false;

  const [issuedAt, signature] = token.split(".");
  if (!issuedAt || !signature) return false;

  const issuedAtSeconds = Number(issuedAt);
  const nowSeconds = Math.floor(Date.now() / 1000);
  if (!Number.isFinite(issuedAtSeconds) || nowSeconds - issuedAtSeconds > SESSION_MAX_AGE_SECONDS) {
    return false;
  }

  return (await sign(issuedAt, secret)) === signature;
}

export async function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const authenticated = await hasValidSession(request);

  if (pathname === "/login" && authenticated) {
    return NextResponse.redirect(new URL("/studio", request.url));
  }

  if (isPublicPath(pathname) || authenticated) {
    return NextResponse.next();
  }

  if (pathname.startsWith("/api/")) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }

  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("next", `${pathname}${search}`);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image).*)"],
};
