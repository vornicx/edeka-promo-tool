#!/usr/bin/env node
/**
 * Arranca el backend (FastAPI/uvicorn) en segundo plano antes de levantar el
 * frontend. Se ejecuta automáticamente vía el hook `predev` de npm.
 *
 * - Si el backend ya responde en :8000, no hace nada.
 * - Si no, lo lanza desacoplado (detached) y deja que el proceso de npm siga
 *   con `next dev`. La salida del backend se escribe en backend/backend.log.
 */
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const PORT = 8000;
const ROOT = path.resolve(__dirname, "..", "..");
const BACKEND_DIR = path.join(ROOT, "backend");

function isBackendUp() {
  return new Promise((resolve) => {
    const req = http.get(
      { host: "127.0.0.1", port: PORT, path: "/health", timeout: 800 },
      (res) => {
        res.resume();
        resolve(res.statusCode === 200);
      }
    );
    req.on("error", () => resolve(false));
    req.on("timeout", () => {
      req.destroy();
      resolve(false);
    });
  });
}

function resolvePython() {
  const candidates = [
    path.join(BACKEND_DIR, ".venv", "bin", "python"),
    path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe"),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  return process.platform === "win32" ? "python" : "python3";
}

async function main() {
  if (await isBackendUp()) {
    console.log(`[backend] ya está corriendo en http://localhost:${PORT}`);
    return;
  }

  const python = resolvePython();
  console.log(`[backend] iniciando en http://localhost:${PORT} (${python})...`);

  const logPath = path.join(BACKEND_DIR, "backend.log");
  const out = fs.openSync(logPath, "a");

  const child = spawn(
    python,
    ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", String(PORT)],
    {
      cwd: BACKEND_DIR,
      detached: true,
      stdio: ["ignore", out, out],
    }
  );

  child.on("error", (err) => {
    console.error(`[backend] no se pudo iniciar: ${err.message}`);
    console.error(`[backend] revisa que exista el venv o instala deps en ${BACKEND_DIR}`);
  });

  // Desacoplar para que `next dev` arranque sin esperar al backend.
  child.unref();
  console.log(`[backend] logs en ${logPath}`);
}

main();
