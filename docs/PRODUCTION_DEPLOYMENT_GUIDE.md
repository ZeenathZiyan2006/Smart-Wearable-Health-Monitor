# PulseGuardian AI — Production Deployment, Backup & Security Guide

This document establishes the production deployment architecture, security hardening, database recovery, and configuration requirements for **PulseGuardian AI – Smart Wearable Health Monitor**.

---

## 1. Environment Configurations

### Backend Production Configuration (`.env.production`)
Create `backend/.env.production` (never commit real secrets to Git):

```ini
# Core
PROJECT_NAME="PulseGuardian AI Production API"
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=GENERATE_SECURE_RANDOM_SECRET_KEY_MIN_64_CHARACTERS_HEX_OR_BASE64
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Production Database (PostgreSQL with SSL)
DATABASE_URL=postgresql+psycopg2://pulseguardian_admin:SECURE_DB_PASSWORD@prod-db.pulseguardian.internal:5432/pulseguardian_prod?sslmode=require

# Redis & Celery Task Worker
REDIS_URL=rediss://:SECURE_REDIS_PASSWORD@prod-redis.pulseguardian.internal:6379/0
CELERY_BROKER_URL=rediss://:SECURE_REDIS_PASSWORD@prod-redis.pulseguardian.internal:6379/0
CELERY_RESULT_BACKEND=rediss://:SECURE_REDIS_PASSWORD@prod-redis.pulseguardian.internal:6379/1

# Real AI Services (OpenAI & IndicTrans2)
VOICE_STT_PROVIDER=hosted_whisper
OPENAI_API_KEY=sk-proj-PROD_OPENAI_API_KEY
OPENAI_API_BASE=https://api.openai.com/v1

VOICE_TRANSLATION_PROVIDER=hosted_translation
TRANSLATION_API_KEY=sk-proj-PROD_OPENAI_API_KEY
TRANSLATION_MODEL_NAME=gpt-4o-mini

VOICE_TTS_PROVIDER=hosted_tts
TTS_API_KEY=sk-proj-PROD_OPENAI_API_KEY
TTS_MODEL_NAME=tts-1

# Privacy & Security
VOICE_AUDIO_RETENTION_HOURS=0
VOICE_ENABLE_CONSENT_ENFORCEMENT=True

# Allowed CORS Origins
BACKEND_CORS_ORIGINS=["https://app.pulseguardian.ai","https://caregiver.pulseguardian.ai"]
```

---

## 2. Production Database Migrations & Recovery

### Applying Migrations:
```bash
cd backend
alembic upgrade head
```

### Automated Backup Script (`backup_db.sh`):
```bash
#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/var/backups/pulseguardian"
mkdir -p $BACKUP_DIR

pg_dump -U pulseguardian_admin -h prod-db.pulseguardian.internal -Fc pulseguardian_prod > "$BACKUP_DIR/pulseguardian_db_$TIMESTAMP.dump"

# Retain backups for 30 days
find $BACKUP_DIR -type f -name "*.dump" -mtime +30 -exec rm {} \;
```

### Point-in-Time Database Recovery:
```bash
pg_restore -U pulseguardian_admin -h prod-db.pulseguardian.internal -d pulseguardian_prod --clean --if-exists /var/backups/pulseguardian/pulseguardian_db_TIMESTAMP.dump
```

---

## 3. Production Application Deployment

### Backend with Gunicorn + Uvicorn Workers & Systemd:
Create `/etc/systemd/system/pulseguardian-backend.service`:
```ini
[Unit]
Description=PulseGuardian AI FastAPI Production Server
After=network.target

[Service]
User=pulseguardian
Group=pulseguardian
WorkingDirectory=/srv/pulseguardian/backend
EnvironmentFile=/srv/pulseguardian/backend/.env.production
ExecStart=/srv/pulseguardian/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:8000 --access-logfile /var/log/pulseguardian/access.log --error-logfile /var/log/pulseguardian/error.log
Restart=always

[Install]
WantedBy=multi-user.target
```

### Frontend Build & Nginx Reverse Proxy with TLS/SSL:
Build frontend production bundle:
```bash
cd frontend
npm run build
```

Configure Nginx (`/etc/nginx/sites-available/pulseguardian.conf`):
```nginx
server {
    listen 80;
    server_name app.pulseguardian.ai;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.pulseguardian.ai;

    ssl_certificate /etc/letsencrypt/live/app.pulseguardian.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.pulseguardian.ai/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Static Frontend SPA
    location / {
        root /srv/pulseguardian/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Real-Time WebSocket Proxy
    location /api/v1/voice/ws {
        proxy_pass http://127.0.0.1:8000/api/v1/voice/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

---

## 4. Health Checks & Synthetic Monitoring

- **HTTP Status Check**: `GET https://app.pulseguardian.ai/api/v1/health`  
  *Expected Response*: `{"status": "healthy"}`
- **OpenAPI Schema Verification**: `GET https://app.pulseguardian.ai/api/v1/openapi.json`
- **Authenticated WebSocket Check**: `ws://app.pulseguardian.ai/api/v1/voice/ws?token=<ACCESS_TOKEN>`  
  *Send*: `"ping"` ➔ *Receive*: `"pong"`
