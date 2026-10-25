# Image pour serveur GPU (RunPod, Modal, VM avec NVIDIA). Non testée sur GPU.
FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-devel
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
# flash_attn en dernier : sa compilation échoue souvent et prend du temps
RUN grep -v flash_attn requirements.txt > /tmp/req.txt && pip install -r /tmp/req.txt \
 && pip install -r server/requirements.txt \
 && pip install flash_attn --no-build-isolation
ENV WAN_CKPT_DIR=/models/Wan2.2-TI2V-5B OUTPUT_DIR=/data/outputs
EXPOSE 8000
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
