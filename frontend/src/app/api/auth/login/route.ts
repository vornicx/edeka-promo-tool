import { NextResponse } from "next/server";
import { AUTH_COOKIE, SESSION_MAX_AGE_SECONDS, createSessionToken, isLoginConfigured } from "@/lib/session";

export const runtime = "nodejs";

export async function POST(request: Request) {
  if (!isLoginConfigured()) {
    return NextResponse.json({ message: "Login ist noch nicht konfiguriert" }, { status: 503 });
  }

  const body = (await request.json().catch(() => null)) as { password?: string } | null;
  if (!body?.password || body.password !== process.env.PROMO_LOGIN_PASSWORD) {
    return NextResponse.json({ message: "Zugangscode ist nicht korrekt" }, { status: 401 });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set(AUTH_COOKIE, createSessionToken(), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
  });

  return response;
}
