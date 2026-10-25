"""API HTTP minimale autour de generate.py (Wan2.2 TI2V-5B).

Une seule génération à la fois (file d'attente en mémoire).
Variables d'environnement :
  API_KEY          (obligatoire) clé exigée dans l'en-tête X-API-Key
  WAN_CKPT_DIR     dossier des poids (défaut ./Wan2.2-TI2V-5B)
  GENERATE_SCRIPT  chemin de generate.py (défaut ../generate.py)
  OUTPUT_DIR       dossier des vidéos (défaut ./outputs)
"""
import os
import queue
import re
import secrets
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

API_KEY = os.environ.get("API_KEY", "")
if len(API_KEY) < 16:
    sys.exit("API_KEY manquant ou trop court (16 caractères minimum).")

HERE = Path(__file__).resolve().parent
CKPT_DIR = os.environ.get("WAN_CKPT_DIR", str(HERE.parent / "Wan2.2-TI2V-5B"))
GENERATE = os.environ.get("GENERATE_SCRIPT", str(HERE.parent / "generate.py"))
OUT_DIR = Path(os.environ.get("OUTPUT_DIR", HERE / "outputs"))
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEOUT_S = 30 * 60
MAX_PENDING = 20
SIZES = {"1280*704", "704*1280"}  # tailles supportées par ti2v-5B
ID_RE = re.compile(r"^[0-9a-f]{32}$")

app = FastAPI(title="Wan2.2 API")
jobs: dict[str, dict] = {}
pending: "queue.Queue[str]" = queue.Queue()


class JobRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=1000)
    size: str = "1280*704"
    seed: int | None = Field(default=None, ge=0, le=2**31 - 1)


def check_key(x_api_key: str = Header(default="")):
    if not secrets.compare_digest(x_api_key.encode(), API_KEY.encode()):
        raise HTTPException(401, "Clé API invalide")


def run_job(job_id: str):
    job = jobs[job_id]
    job["status"] = "running"
    job["started_at"] = time.time()
    out = OUT_DIR / f"{job_id}.mp4"
    cmd = [
        sys.executable, GENERATE,
        "--task", "ti2v-5B",
        "--size", job["size"],
        "--ckpt_dir", CKPT_DIR,
        "--offload_model", "True",
        "--convert_model_dtype",
        "--t5_cpu",
        f"--prompt={job['prompt']}",  # forme "=" : un prompt commençant par "-" reste une valeur
        "--save_file", str(out),
    ]
    if job["seed"] is not None:
        cmd += ["--base_seed", str(job["seed"])]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)
        if r.returncode == 0 and out.exists():
            job["status"] = "done"
            job["video_path"] = f"/videos/{job_id}.mp4"
        else:
            job["status"] = "error"
            job["error"] = (r.stderr or r.stdout or "échec inconnu")[-800:]
    except subprocess.TimeoutExpired:
        job["status"] = "error"
        job["error"] = "Délai dépassé (30 min)"
    except Exception as e:  # noqa: BLE001
        job["status"] = "error"
        job["error"] = str(e)[:800]
    job["finished_at"] = time.time()


def worker():
    while True:
        run_job(pending.get())


threading.Thread(target=worker, daemon=True).start()


@app.get("/health")
def health():
    return {"ok": True, "pending": pending.qsize()}


@app.post("/jobs", status_code=202, dependencies=[Depends(check_key)])
def create_job(req: JobRequest):
    if req.size not in SIZES:
        raise HTTPException(422, f"size doit être l'un de {sorted(SIZES)}")
    if pending.qsize() >= MAX_PENDING:
        raise HTTPException(429, "File d'attente pleine, réessayez plus tard")
    job_id = uuid.uuid4().hex
    jobs[job_id] = {"id": job_id, "status": "queued", "prompt": req.prompt,
                    "size": req.size, "seed": req.seed, "created_at": time.time()}
    pending.put(job_id)
    return {"id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}", dependencies=[Depends(check_key)])
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job introuvable")
    keys = ("id", "status", "video_path", "error", "created_at")
    return {k: job[k] for k in keys if k in job}


@app.get("/videos/{job_id}.mp4")
def get_video(job_id: str):
    # Pas de clé API : le lecteur <video> du navigateur n'en envoie pas.
    # L'identifiant (UUID aléatoire de 128 bits) sert de secret.
    if not ID_RE.match(job_id):
        raise HTTPException(404)
    path = OUT_DIR / f"{job_id}.mp4"
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="video/mp4")
