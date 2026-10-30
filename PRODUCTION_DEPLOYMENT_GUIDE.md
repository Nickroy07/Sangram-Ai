# Sangram AI — Complete Production Launch & Deployment Manual

**Domain:** `https://sangramai.tech`  
**API Subdomain:** `https://api.sangramai.tech`  
**Frontend Platform:** Hostinger Shared Web Hosting (Static HTML/CSS/JS Assets)  
**Backend Platform:** VPS / Container Service running Python 3.11+ / FastAPI  
**Database:** Managed PostgreSQL (Version 15+)  

---

## 1. Architecture Overview

```
                          [ User Browser ]
                                 │
                 ┌───────────────┴───────────────┐
                 │ HTTPS                         │ HTTPS / WSS / SSE
                 ▼                               ▼
       [ https://sangramai.tech ]      [ https://api.sangramai.tech ]
       Hostinger Shared Hosting                 FastAPI Backend
       Document Root: public_html/              (Uvicorn ASGI Server)
       ├── index.html                           ├── Python 3.11/3.12/3.13
       ├── assets/ (*.js, *.css)                ├── Alembic Migrations
       ├── .htaccess (SPA fallback)             └── Provider Gateway
       └── robots.txt & sitemap.xml                      │
                                                         ▼
                                                [ PostgreSQL DB ]
                                                Managed Cloud DB
                                                (asyncpg driver)
```

---

## 2. Part A: Deploying Frontend to Hostinger Shared Hosting

Hostinger shared hosting executes Apache / LiteSpeed web servers and **cannot run persistent long-lived Python background services or WebSockets/SSE asynchronously**. Therefore, the frontend is compiled into optimized static production assets.

### Step 1: Configure Frontend Production Environment
In `frontend/.env.production` (or `frontend/.env` prior to build):

```ini
VITE_API_BASE_URL=https://api.sangramai.tech
VITE_GOOGLE_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com
```

### Step 2: Build Static Production Assets
In your terminal:

```powershell
cd d:\Sangram-Ai-main\frontend
npm ci
npm run build
```

This compiles your application into `frontend/dist/`.

### Step 3: Upload to Hostinger `public_html`
1. Log in to **Hostinger hPanel** → **File Manager** (or connect via SFTP / FileZilla).
2. Navigate to `domains/sangramai.tech/public_html/`.
3. Clear any default Hostinger placeholder files (`default.php`, etc.).
4. Upload all files and folders directly from `frontend/dist/` into `public_html/`:
   - `index.html`
   - `assets/` (contains hashed JS and CSS)
   - `.htaccess` (Ensures client-side React routes like `/pricing`, `/app/arena` don't 404 on refresh)
   - `robots.txt`
   - `sitemap.xml`
   - `favicon.ico`, `favicon.png`, `sangram-logo.png`

---

## 3. Part B: Deploying FastAPI Backend (VPS / Container)

The backend handles AI orchestration, password hashing, JWT sessions, SSE streaming, and Google ID token verification.

### Option 1: Docker Deployment (Recommended)

1. Provision an Ubuntu 22.04 / 24.04 VPS (Hostinger VPS, DigitalOcean, or Hetzner).
2. Install Docker and Docker Compose:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose-v2
   ```
3. Copy `backend/` folder to `/var/www/sangram-backend`.
4. Create production `.env` at `/var/www/sangram-backend/.env`:
   ```ini
   ENVIRONMENT=production
   DEBUG=false
   PROJECT_NAME="Sangram AI Backend"
   VERSION="1.0.0"
   API_V1_PREFIX="/api"
   HOST=0.0.0.0
   PORT=8000
   SECRET_KEY="GENERATE_A_64_CHAR_HEX_KEY_NOT_CONTAINING_DEV_OR_INSECURE"
   ALLOWED_ORIGINS=["https://sangramai.tech","https://www.sangramai.tech"]
   DATABASE_URL="postgresql+asyncpg://DB_USER:DB_PASSWORD@DB_HOST:5432/sangram_ai"
   COOKIE_SECURE=true
   COOKIE_SAMESITE=lax
   FRONTEND_URL=https://sangramai.tech
   GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
   EMAIL_BACKEND=smtp
   EMAIL_FROM="Sangram AI <support@sangramai.tech>"
   SMTP_HOST="smtp.hostinger.com"
   SMTP_PORT=587
   SMTP_USERNAME="support@sangramai.tech"
   SMTP_PASSWORD="YOUR_SMTP_PASSWORD"
   SMTP_STARTTLS=true

   # Model Providers (Server-side credentials only)
   OPENAI_API_KEY="sk-..."
   ANTHROPIC_API_KEY="sk-ant-..."
   GOOGLE_API_KEY="AIzaSy..."
   GROQ_API_KEY="gsk_..."
   MISTRAL_API_KEY="..."
   XAI_API_KEY="..."
   ```
5. Apply database migrations:
   ```bash
   alembic upgrade head
   ```
6. Start container:
   ```bash
   docker compose up -d --build
   ```

### Option 2: Systemd Native Service (Ubuntu VPS)

```ini
# /etc/systemd/system/sangram-backend.service
[Unit]
Description=Sangram AI FastAPI Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/sangram-backend
EnvironmentFile=/var/www/sangram-backend/.env
ExecStart=/var/www/sangram-backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Nginx Reverse Proxy configuration:
```nginx
server {
    server_name api.sangramai.tech;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Server-Sent Events (SSE) buffering disabled for real-time battle streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
```

---

## 4. Part C: Google Cloud Console Configuration

To enable real **Google Sign-In**:
1. Open [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Select or create your project: **Sangram AI**.
3. Configure the **OAuth Consent Screen**:
   - User Type: **External**
   - App Name: `Sangram AI`
   - User Support Email: your email / `support@sangramai.tech`
   - Authorized Domains: `sangramai.tech`
4. Under **Credentials** → **Create Credentials** → **OAuth client ID**:
   - Application Type: **Web application**
   - Name: `Sangram AI Production Client`
   - **Authorized JavaScript origins**:
     - `https://sangramai.tech`
     - `https://www.sangramai.tech`
     - `http://localhost:3000` (for local development)
   - **Authorized redirect URIs**:
     - `https://sangramai.tech`
     - `https://sangramai.tech/auth/login`
5. Copy the generated **Client ID** (ends with `.apps.googleusercontent.com`):
   - Set in `frontend/.env` as `VITE_GOOGLE_CLIENT_ID`
   - Set in `backend/.env` as `GOOGLE_CLIENT_ID`

---

## 5. Part D: DNS & SSL Records

In your domain DNS registrar / Hostinger DNS Zone Editor:
| Type | Name | Content / Target | TTL |
| :--- | :--- | :--- | :--- |
| **A** | `@` (sangramai.tech) | Hostinger Shared Hosting IP | 3600 |
| **CNAME** | `www` | `sangramai.tech` | 3600 |
| **A** | `api` (api.sangramai.tech) | VPS Server IP address | 3600 |

Install free Let's Encrypt SSL certificates for both `sangramai.tech` (via Hostinger hPanel 1-click SSL) and `api.sangramai.tech` (via `certbot --nginx` on your VPS).

---

## 6. Verification Checklist

- [x] Liveness probe: `curl -I https://api.sangramai.tech/health/live` (returns 200 OK)
- [x] Readiness probe: `curl -I https://api.sangramai.tech/health/ready` (returns 200 OK, database connected)
- [x] Frontend SPA direct reload on `/pricing` and `/app/arena` (returns index.html without 404 via `.htaccess`)
- [x] Google Sign-In button renders and logs in real accounts
- [x] Email/Password registration issues session cookies and sends verification email
- [x] Usage telemetry loads real battle counts from PostgreSQL
- [x] Provider keys stay strictly on backend server
