# Nivaas — System Design Write-up

## Complaint history model

The core design decision is separating a complaint's **current state** from its **lifecycle record**. The `complaints` table stores the live snapshot (status, priority, timestamps), while an append-only `status_history` table stores every transition as its own row: `(complaint_id, status, note, actor_id, created_at)`.

This gives three properties the assignment demands. First, **auditability** — history rows are never updated or deleted, so the record of who changed what, when, and why cannot drift from reality. Second, **attribution** — `actor_id` is a foreign key to `users`, so each entry shows whether the resident raised it or which admin moved it forward, along with the optional note ("plumber visiting tomorrow"). Third, **cheap reads** — the current status lives denormalised on the complaint row, so list views and dashboard counts never need to scan history; history is only joined (eagerly, via `joinedload`, avoiding N+1 queries) when rendering a complaint's timeline.

The lifecycle is enforced in the API, not just the UI: a complaint is created as `Open` with an automatic first history entry, can move to `In Progress` or `Resolved`, and once `Resolved` it is closed — the status endpoint rejects any further transition with a 409, and `resolved_at` is stamped for reporting. No-op transitions (setting the same status twice) are also rejected so history stays meaningful.

## Overdue detection

Overdue status is **computed, not stored**. At read time, a complaint is overdue if it is unresolved and `now − created_at ≥ threshold`, or if the admin has manually set the `flagged_overdue` boolean. Computing rather than persisting the automatic part avoids the classic pitfalls of a background cron job: there is no scheduler to deploy, no stale flags when the threshold changes, and no race between the job and reads. The moment the admin lowers the threshold from 7 to 3 days, every affected complaint is immediately overdue on the next request.

The threshold itself is configurable at two levels: an `OVERDUE_DAYS` environment variable provides the default, and a `settings` key-value table lets the admin change it from the UI without a redeploy — the database value wins. The manual flag covers the real-world case where something is urgent before the clock runs out (a lift failure on day one). Resolving a complaint clears the flag. The admin complaint list sorts overdue items first, then by priority weight (High → Low), then recency, so the queue reads top-down as "what needs attention now."

## Photo handling

Photos are uploaded as `multipart/form-data` alongside the complaint fields. The server validates the extension against an allowlist (JPG/PNG/WEBP) and enforces a 5 MB cap by reading the payload before writing. Files are stored on disk under `uploads/` with a **UUID filename** — the original name is discarded, which prevents path traversal, name collisions, and leaking resident information through filenames. The database stores only the relative path; FastAPI serves the directory read-only at `/uploads`, and the API returns a ready-to-use `photo_url`.

Storing files outside the database keeps rows small and backups fast. The trade-off is that platform-managed ephemeral disks (Render free tier) lose files on redeploy; the design isolates this behind the `UPLOAD_DIR` setting, so pointing it at a persistent mounted disk — or swapping the save function for S3/Cloudinary — requires no schema or API change.

## Notification flow

Emails are sent for two events: a status change (to the complaint's owner) and an important notice (fanned out to all residents). Both are dispatched through FastAPI's **BackgroundTasks**, so the HTTP response returns immediately and a slow or failing SMTP server never blocks or fails the user's action — email is best-effort by design, and errors are logged rather than raised. The database commit happens *before* the task is queued, so a notification is only ever sent for a change that actually persisted.

The mailer is provider-agnostic: standard SMTP with STARTTLS, configured entirely by environment variables, so any free tier (Brevo, Gmail app password, Mailtrap) drops in. When `SMTP_HOST` is unset, emails print to the console — the full flow stays demonstrable in development and grading without credentials.

## Supporting decisions

Role-based auth uses stateless JWTs (24 h expiry) with two FastAPI dependencies — `get_current_user` and `require_admin` — so authorisation is declared per-route rather than scattered through handlers. Passwords are hashed with PBKDF2-SHA256. The dashboard aggregates counts by status and category server-side and reuses the same overdue predicate as the list view, so numbers always agree with what the admin sees. SQLite keeps local setup to one command while `DATABASE_URL` switches the same SQLAlchemy models to PostgreSQL in production, deployed via the included Render Blueprint with the frontend served statically from the same service — one URL, no CORS complexity.

*(≈780 words)*
