const { env, authorized } = require("../_lib");

module.exports = async function handler(req, res) {
  if (req.method !== "GET") return res.status(405).json({ error: "Méthode non autorisée" });
  const cfg = env();
  if (!cfg) return res.status(500).json({ error: "Serveur mal configuré" });
  if (!authorized(req, cfg.code)) return res.status(401).json({ error: "Code d’accès invalide" });

  const id = String(req.query.id || "");
  if (!/^[0-9a-f]{32}$/.test(id)) return res.status(400).json({ error: "Identifiant invalide" });

  try {
    const r = await fetch(`${cfg.base}/jobs/${id}`, { headers: { "X-API-Key": cfg.key } });
    if (r.status === 404) return res.status(404).json({ error: "Génération introuvable" });
    if (!r.ok) return res.status(502).json({ error: "Erreur du serveur GPU" });
    const j = await r.json();
    return res.status(200).json({
      status: j.status,
      error: j.error,
      videoUrl: j.video_path ? cfg.base + j.video_path : undefined,
    });
  } catch {
    return res.status(502).json({ error: "Serveur GPU injoignable" });
  }
};
