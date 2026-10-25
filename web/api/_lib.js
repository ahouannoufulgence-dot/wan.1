// Utilitaires partagés par les fonctions Vercel (le fichier _lib n'est pas exposé comme route).
const crypto = require("crypto");

function env() {
  const { GPU_API_URL, GPU_API_KEY, ACCESS_CODE } = process.env;
  if (!GPU_API_URL || !GPU_API_KEY || !ACCESS_CODE) return null;
  return { base: GPU_API_URL.replace(/\/+$/, ""), key: GPU_API_KEY, code: ACCESS_CODE };
}

function authorized(req, code) {
  const given = String(req.headers["x-access-code"] || "");
  const a = crypto.createHash("sha256").update(given).digest();
  const b = crypto.createHash("sha256").update(code).digest();
  return crypto.timingSafeEqual(a, b);
}

module.exports = { env, authorized };
