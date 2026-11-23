# HRES Optimizer v2.0 — Production Docker Image (Hugging Face Spaces / Render / Cloud)
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    HOST=0.0.0.0 \
    PORT=7860

# Non-root user required by Hugging Face Spaces (UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user:user requirements-web.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-web.txt

COPY --chown=user:user data_handlers ./data_handlers
COPY --chown=user:user models ./models
COPY --chown=user:user optimization ./optimization
COPY --chown=user:user reporting ./reporting
COPY --chown=user:user simulation ./simulation
COPY --chown=user:user web ./web
COPY --chown=user:user web_app.py ./web_app.py

RUN mkdir -p data_handlers/cache

EXPOSE 7860

CMD ["sh", "-c", "uvicorn web_app:app --host 0.0.0.0 --port ${PORT:-7860}"]
