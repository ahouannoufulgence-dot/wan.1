# Déploiement : site (Vercel) + API (serveur GPU)

```
Navigateur ──► Vercel (web/)  ──► Serveur GPU (server/ + generate.py)
               interface + proxy    génère les vidéos avec Wan2.2 TI2V-5B
```

Vercel ne peut pas exécuter le modèle (pas de GPU) : il ne sert que l'interface.

## 1. Serveur GPU (≥ 24 Go de VRAM, ex. RTX 4090 / A5000 / L4)

```bash
git clone https://github.com/ahouannoufulgence-dot/wan.1.git && cd wan.1
pip install -r requirements.txt && pip install -r server/requirements.txt
pip install "huggingface_hub[cli]" && huggingface-cli download Wan-AI/Wan2.2-TI2V-5B --local-dir ./Wan2.2-TI2V-5B
export API_KEY="$(openssl rand -hex 24)"   # notez-la : c'est GPU_API_KEY côté Vercel
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Ou avec Docker : `docker build -f server/Dockerfile -t wan-api .` puis montez les poids dans `/models`.
L'URL publique du serveur doit être en **HTTPS** (le proxy HTTPS de RunPod, Cloudflare Tunnel, etc.).
Vérification : `curl https://VOTRE-URL/health`.

## 2. Site sur Vercel

1. vercel.com → *Add New → Project* → importez `wan.1`.
2. **Root Directory : `web`**, Framework : *Other*.
3. Variables d'environnement :
   - `GPU_API_URL` : URL HTTPS du serveur GPU (sans `/` final)
   - `GPU_API_KEY` : la valeur de `API_KEY` du serveur
   - `ACCESS_CODE` : le code que les visiteurs doivent saisir (protège votre budget GPU)
4. *Deploy*. Chaque `git push` redéploie.

## Limites actuelles
- Une génération à la fois ; file d'attente et historique en mémoire (perdus au redémarrage).
- Le modèle est rechargé à chaque vidéo (plusieurs minutes par génération).
- Les vidéos sont accessibles par leur lien secret, sans mot de passe, et ne sont pas supprimées automatiquement.
- Code de l'API testé avec un faux `generate.py`, pas avec le vrai modèle sur GPU.

## 3. Installer l'application sur téléphone (PWA)
Une fois le site en ligne sur Vercel :
- **Android (Chrome)** : ouvrir le site → menu ⋮ → *Installer l'application* (ou *Ajouter à l'écran d'accueil*).
- **iPhone (Safari)** : ouvrir le site → bouton Partager → *Sur l'écran d'accueil*.

L'icône apparaît comme une application et s'ouvre en plein écran. Elle se met à jour toute seule à chaque `git push`.
