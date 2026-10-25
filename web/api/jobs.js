const { env, authorized } = require("./_lib");

module.exports = async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "Méthode non autorisée" });
  const cfg = env();
  if (!cfg) return res.status(500).json({ error: "Serveur mal configuré (variables d’environnement manquantes)" });
  if (!authorized(req, cfg.code)) return res.status(401).json({ error: "Code d’accès invalide" });

  const { prompt, size } = req.body || {};
  if (typeof prompt !== "string" || prompt.trim().length < 3 || prompt.length > 1000)
    return res.status(400).json({ error: "Le texte doit faire entre 3 et 1000 caractères" });

  try {
    const r = await fetch(`${cfg.base}/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": cfg.key },
      body: JSON.stringify({ prompt: prompt.trim(), size: size === "704*1280" ? "704*1280" : "1280*704" }),
    });
    const data = await r.json().catch(() => ({}));
    if (r.status === 429) return res.status(429).json({ error: "File d’attente pleine, réessayez plus tard" });
    if (!r.ok || typeof data.id !== "string" || !/^[0-9a-f]{32}$/.test(data.id))
      return res.status(502).json({ error: "Le serveur GPU n’a pas répondu correctement. Vérifiez GPU_API_URL et GPU_API_KEY." });
    return res.status(202).json({ id: data.id });
  } catch {
    return res.status(502).json({ error: "Serveur GPU injoignable" });
  }
};
