# Nivaas — Society Maintenance Tracker

A platform where apartment residents raise and track maintenance complaints with photos, the admin manages them through a clear workflow with priorities and overdue detection, and everyone stays informed through a notice board and email updates.

**Stack:** FastAPI · SQLAlchemy · SQLite (dev) / PostgreSQL (prod) · Vanilla HTML/CSS/JS · JWT auth · SMTP email

---

## Features

**Residents**
- Register, log in, raise complaints with category, title, description, and an optional photo (JPG/PNG/WEBP, ≤5 MB)
- View all their complaints with the full status history of each change (timestamp, actor, note)
- See the society notice board with important notices pinned to the top
- Receive an email whenever their complaint status changes or an important notice is posted

**Admin**
- View all complaints; filter by category, status, and date range
- Set complaint priority (Low / Medium / High)
- Update status through the lifecycle **Open → In Progress → Resolved** with an optional note; every change is recorded in history
- Resolved complaints are closed — no further status changes allowed
- Complaints open beyond a configurable threshold are automatically marked overdue and surface at the top; the admin can also flag/clear overdue manually
- Change the overdue threshold from the UI (persisted in the database)
- Post notices, optionally marked important (pinned + emailed to every resident)
- Dashboard: totals by status, by category, and overdue count

---

## Local setup

```bash
# 1. Clone and enter the project
cd nivaas

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env         # Windows (or: cp .env.example .env)
# Edit .env if needed. Leaving SMTP_HOST empty prints emails to the console.

# 5. Run
uvicorn backend.main:app --reload
```

Open **http://localhost:8000** — the frontend is served by the same server.
Interactive API docs (Swagger) are at **http://localhost:8000/docs**.

**Default admin login** (seeded on first start): `admin@nivaas-society.com` / `admin123` — change these via `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env` before deploying.

Register any new account from the UI to get a resident login.

### Email setup (free tier)
Set the `SMTP_*` variables in `.env` using any free provider — e.g. **Brevo** (300 emails/day free): host `smtp-relay.brevo.com`, port `587`, plus your Brevo login and SMTP key. A Gmail app password also works. With `SMTP_HOST` empty, emails are printed to the server console so the flow is testable without an account.

---

## Deployment (Render)

The repo includes `render.yaml` (Render Blueprint):

1. Push the project to GitHub
2. On Render: **New → Blueprint**, pick the repo
3. Set `ADMIN_PASSWORD` when prompted; add `SMTP_*` vars in the dashboard for real emails
4. Deploy — Render provisions the web service and a free PostgreSQL database automatically

> Note: uploads on Render's free tier are stored on ephemeral disk, so photos reset on redeploy. For a permanent store, attach a Render Disk or point `UPLOAD_DIR` at a mounted volume (covered in the system design write-up).

---

## API documentation

All endpoints are prefixed with `/api`. Authenticated endpoints require the header `Authorization: Bearer <token>`.

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | — | Register a resident. Body: `{name, flat_no, email, password}` → token + user |
| POST | `/api/auth/login` | — | Log in. Body: `{email, password}` → token + user |
| GET | `/api/auth/me` | Any | Current user profile |

### Complaints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/complaints/categories` | — | Available categories, statuses, priorities |
| POST | `/api/complaints` | Resident/Admin | Raise a complaint. `multipart/form-data`: `category`, `title`, `description`, optional `photo` |
| GET | `/api/complaints/mine` | Any | The caller's complaints with full history |
| GET | `/api/complaints` | Admin | All complaints. Query filters: `category`, `status`, `date_from`, `date_to` (YYYY-MM-DD). Sorted overdue-first, then priority, then newest |
| POST | `/api/complaints/{id}/status` | Admin | Update status. Body: `{status, note?}`. Rejects changes to Resolved (closed) complaints. Emails the resident |
| PATCH | `/api/complaints/{id}/priority` | Admin | Body: `{priority}` — Low / Medium / High |
| PATCH | `/api/complaints/{id}/overdue` | Admin | Body: `{flagged: bool}` — manually flag or clear the overdue flag |

### Notices

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/notices` | Any | All notices, pinned important ones first |
| POST | `/api/notices` | Admin | Body: `{title, body, is_important}`. Important notices email every resident |

### Dashboard & settings

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/dashboard` | Admin | `{total, by_status, by_category, overdue_count, overdue_threshold_days}` |
| PUT | `/api/settings/overdue-days` | Admin | Body: `{days}` (1–90) — persists the overdue threshold |
| GET | `/api/health` | — | Health check |

Complaint responses include: `id, category, title, description, photo_url, priority, status, is_overdue, days_open, created_at, resolved_at, resident_name, resident_flat, history[]` where each history item is `{status, note, actor_name, created_at}`.

---

## Database schema

```
users
  id            INTEGER PK
  name          VARCHAR(120)  NOT NULL
  flat_no       VARCHAR(30)   NOT NULL
  email         VARCHAR(255)  UNIQUE NOT NULL
  password_hash VARCHAR(255)  NOT NULL
  role          VARCHAR(20)   NOT NULL DEFAULT 'resident'   -- resident | admin
  created_at    DATETIME      NOT NULL

complaints
  id             INTEGER PK
  user_id        INTEGER FK -> users.id
  category       VARCHAR(50)  NOT NULL  (indexed)
  title          VARCHAR(150) NOT NULL
  description    TEXT         NOT NULL
  photo_path     VARCHAR(255) NULL
  priority       VARCHAR(10)  NOT NULL DEFAULT 'Medium'     -- Low | Medium | High
  status         VARCHAR(20)  NOT NULL DEFAULT 'Open'       -- Open | In Progress | Resolved
  flagged_overdue BOOLEAN     NOT NULL DEFAULT false        -- manual admin flag
  created_at     DATETIME     NOT NULL (indexed)
  resolved_at    DATETIME     NULL

status_history
  id           INTEGER PK
  complaint_id INTEGER FK -> complaints.id
  status       VARCHAR(20) NOT NULL
  note         TEXT        NULL
  actor_id     INTEGER FK -> users.id
  created_at   DATETIME    NOT NULL

notices
  id           INTEGER PK
  title        VARCHAR(150) NOT NULL
  body         TEXT         NOT NULL
  is_important BOOLEAN      NOT NULL DEFAULT false
  author_id    INTEGER FK -> users.id
  created_at   DATETIME     NOT NULL

settings
  key   VARCHAR(50)  PK      -- e.g. 'overdue_days'
  value VARCHAR(255) NOT NULL
```

**Relationships:** a user has many complaints; a complaint has many status_history rows (its full lifecycle); every history row records the actor who made the change; notices belong to their admin author.

---

## Project structure

```
nivaas/
├── backend/
│   ├── main.py               # App entry: routers, static mounts, admin seeding
│   ├── database.py           # Engine + session (SQLite dev / Postgres prod)
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── auth.py               # JWT + password hashing + role dependencies
│   ├── emailer.py            # SMTP with console fallback
│   └── routers/
│       ├── auth_router.py
│       ├── complaints_router.py
│       ├── notices_router.py
│       └── dashboard_router.py
├── frontend/
│   ├── index.html            # Login / register
│   ├── resident.html         # Raise + track complaints, notice board
│   ├── admin.html            # Dashboard, complaint management, notices
│   ├── css/styles.css
│   └── js/ (api.js, resident.js, admin.js)
├── uploads/                  # Complaint photos (gitignored content)
├── requirements.txt
├── .env.example
├── render.yaml               # One-click Render Blueprint deploy
└── SYSTEM_DESIGN.md          # 800-word design write-up
```
