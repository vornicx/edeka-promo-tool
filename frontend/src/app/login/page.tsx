"use client";

import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

function LockIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M8 10V8a4 4 0 118 0v2m-9 0h10a1 1 0 011 1v8a1 1 0 01-1 1H7a1 1 0 01-1-1v-8a1 1 0 011-1z" />
    </svg>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const next = searchParams.get("next") || "/studio";

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });

      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as { message?: string } | null;
        throw new Error(body?.message || "Anmeldung fehlgeschlagen");
      }

      router.replace(next.startsWith("/") && !next.startsWith("//") ? next : "/studio");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Anmeldung fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="panel w-full max-w-md p-5 shadow-elevated" onSubmit={handleSubmit}>
      <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-edeka-blue">Anmelden / Registrieren</p>
      <h2 className="mt-2 text-2xl font-extrabold text-slate-950">Zugang zum Promo Studio</h2>
      <p className="mb-5 mt-2 text-sm font-medium leading-6 text-slate-600">
        Gib den Zugangscode ein. Danach öffnet sich die Web-App automatisch.
      </p>
      <label className="label" htmlFor="password">
        Zugangscode
      </label>
      <input
        id="password"
        name="password"
        type="password"
        autoComplete="current-password"
        className={`input ${error ? "input-error" : ""}`}
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        autoFocus
      />
      {error && <p className="field-error">{error}</p>}
      <button type="submit" className="btn-primary mt-4" disabled={busy || !password}>
        {busy ? (
          <span className="flex items-center gap-2">
            <span className="spinner" />
            Wird angemeldet
          </span>
        ) : (
          <span className="flex items-center gap-2">
            <LockIcon />
            Weiter zum Studio
          </span>
        )}
      </button>
      <p className="mt-4 text-xs font-medium leading-5 text-slate-500">
        Noch keinen Zugangscode? Bitte beim Team von EDEKA Mühlenbein anfragen.
      </p>
    </form>
  );
}

export default function LoginPage() {
  return (
    <main className="grid min-h-screen bg-app lg:grid-cols-[minmax(0,0.9fr)_minmax(420px,1.1fr)]">
      <section className="header-brand flex min-h-[280px] items-center px-6 py-10 text-white lg:min-h-screen lg:px-12">
        <div className="max-w-lg">
          <div className="grid h-16 w-16 place-items-center rounded-2xl bg-white shadow-sm">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/waschbaer_logo.png" alt="EDEKA Waschbär" className="h-14 w-14 object-contain" />
          </div>
          <p className="mt-8 text-xs font-bold uppercase tracking-[0.18em] text-edeka-yellow">EDEKA Mühlenbein</p>
          <h1 className="mt-3 text-3xl font-extrabold leading-tight text-white sm:text-4xl">Promo Studio</h1>
          <p className="mt-4 text-sm font-medium leading-6 text-white/80">
            Melde dich an, um Aktionsmotive direkt in der Web-App zu erstellen.
          </p>
        </div>
      </section>

      <section className="flex items-center justify-center px-5 py-10">
        <Suspense fallback={null}>
          <LoginForm />
        </Suspense>
      </section>
    </main>
  );
}
