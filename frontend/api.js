/* ================= Nivaas — Society Maintenance Tracker =================
   Palette: forest #16382A · leaf #2E7D4F · mint #E4F3E9 · paper #F6FAF6
            ink #1D2A22 · overdue amber #A85B12
========================================================================= */

@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;600;700&family=Karla:wght@400;500;600;700&display=swap');

:root {
  --forest: #16382a;
  --forest-2: #1e4a37;
  --leaf: #2e7d4f;
  --leaf-dark: #256641;
  --mint: #e4f3e9;
  --mint-2: #d2eadb;
  --paper: #f6faf6;
  --card: #ffffff;
  --ink: #1d2a22;
  --muted: #5b6f62;
  --line: #d8e6dc;
  --amber: #a85b12;
  --amber-bg: #fbeedd;
  --red: #b3392f;
  --open: #a85b12;
  --progress: #0e6f74;
  --resolved: #2e7d4f;
  --radius: 14px;
  --shadow: 0 2px 10px rgba(22, 56, 42, 0.08);
  --leaf-shape: 999px 999px 999px 4px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Karla', sans-serif;
  background: var(--paper);
  color: var(--ink);
  line-height: 1.55;
  min-height: 100vh;
}

h1, h2, h3, .brand { font-family: 'Bricolage Grotesque', sans-serif; }

/* ---------- Topbar ---------- */
.topbar {
  background: var(--forest);
  color: #eaf6ee;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 20;
}
.brand { font-size: 1.35rem; font-weight: 700; letter-spacing: 0.2px; display: flex; align-items: center; gap: 10px; }
.brand .leaf-dot {
  width: 14px; height: 14px; background: #7fd6a0;
  border-radius: var(--leaf-shape); display: inline-block;
}
.brand small { font-family: 'Karla'; font-weight: 500; font-size: 0.72rem; opacity: 0.75; display: block; letter-spacing: 0.6px; text-transform: uppercase; }
.topbar .who { font-size: 0.9rem; opacity: 0.9; margin-right: 14px; }

/* ---------- Layout ---------- */
.container { max-width: 1080px; margin: 0 auto; padding: 28px 20px 60px; }
.grid-2 { display: grid; grid-template-columns: 1.4fr 1fr; gap: 24px; align-items: start; }
@media (max-width: 860px) { .grid-2 { grid-template-columns: 1fr; } }

.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 22px;
}
.card h2 { font-size: 1.15rem; margin-bottom: 14px; color: var(--forest); }
.section-note { color: var(--muted); font-size: 0.88rem; margin-top: -8px; margin-bottom: 14px; }

/* ---------- Forms ---------- */
label { display: block; font-weight: 600; font-size: 0.86rem; margin: 12px 0 5px; color: var(--forest-2); }
input, select, textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1.5px solid var(--line);
  border-radius: 10px;
  font: inherit;
  background: #fff;
  color: var(--ink);
  transition: border-color 0.15s;
}
input:focus, select:focus, textarea:focus { outline: none; border-color: var(--leaf); box-shadow: 0 0 0 3px rgba(46,125,79,0.15); }
textarea { resize: vertical; min-height: 90px; }

.btn {
  display: inline-block;
  background: var(--leaf);
  color: #fff;
  border: none;
  padding: 10px 20px;
  border-radius: 10px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
}
.btn:hover { background: var(--leaf-dark); }
.btn:active { transform: scale(0.98); }
.btn:focus-visible { outline: 3px solid rgba(46,125,79,0.4); outline-offset: 2px; }
.btn.secondary { background: var(--mint); color: var(--forest); }
.btn.secondary:hover { background: var(--mint-2); }
.btn.ghost { background: transparent; color: #eaf6ee; border: 1.5px solid rgba(255,255,255,0.4); padding: 7px 16px; }
.btn.ghost:hover { background: rgba(255,255,255,0.12); }
.btn.small { padding: 6px 12px; font-size: 0.83rem; }
.btn.warn { background: var(--amber); }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media (max-width: 560px) { .form-row { grid-template-columns: 1fr; } }

.msg { margin-top: 12px; font-size: 0.9rem; padding: 10px 12px; border-radius: 10px; display: none; }
.msg.error { display: block; background: #fbe9e7; color: var(--red); }
.msg.ok { display: block; background: var(--mint); color: var(--leaf-dark); }

/* ---------- Pills & badges ---------- */
.pill {
  display: inline-block;
  padding: 3px 12px;
  border-radius: var(--leaf-shape);
  font-size: 0.78rem;
  font-weight: 700;
  white-space: nowrap;
}
.pill.Open        { background: #fbeedd; color: var(--open); }
.pill.InProgress  { background: #ddf1f2; color: var(--progress); }
.pill.Resolved    { background: var(--mint); color: var(--resolved); }
.pill.prio-Low    { background: #eef3ee; color: var(--muted); }
.pill.prio-Medium { background: #e8eedd; color: #5c7014; }
.pill.prio-High   { background: #fbe9e7; color: var(--red); }
.pill.overdue     { background: var(--amber); color: #fff; }
.pill.pinned      { background: var(--forest); color: #cdeeda; }

/* ---------- Complaint cards ---------- */
.complaint {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px 18px;
  margin-bottom: 14px;
  background: var(--card);
  transition: box-shadow 0.15s;
}
.complaint:hover { box-shadow: var(--shadow); }
.complaint.is-overdue { border-left: 5px solid var(--amber); }
.complaint-head { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; align-items: baseline; }
.complaint-head h3 { font-size: 1.02rem; color: var(--forest); }
.complaint-meta { color: var(--muted); font-size: 0.82rem; margin-top: 3px; }
.complaint-desc { margin-top: 8px; font-size: 0.93rem; }
.complaint-photo { margin-top: 10px; }
.complaint-photo img { max-width: 220px; max-height: 160px; border-radius: 10px; border: 1px solid var(--line); cursor: zoom-in; }
.pill-row { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }

/* ---------- Signature: leaf-stem history timeline ---------- */
.history { margin-top: 12px; padding-left: 4px; display: none; }
.history.open { display: block; }
.history-item {
  position: relative;
  padding: 0 0 16px 26px;
  border-left: 2px solid var(--mint-2);
  margin-left: 7px;
  font-size: 0.87rem;
}
.history-item:last-child { border-left-color: transparent; padding-bottom: 2px; }
.history-item::before {
  content: '';
  position: absolute;
  left: -8px; top: 2px;
  width: 14px; height: 14px;
  background: var(--leaf);
  border-radius: var(--leaf-shape);
  transform: rotate(45deg);
  border: 2.5px solid var(--paper);
}
.history-item .h-status { font-weight: 700; color: var(--forest-2); }
.history-item .h-when { color: var(--muted); font-size: 0.78rem; }
.history-item .h-note { margin-top: 2px; color: var(--ink); }
.toggle-history { background: none; border: none; color: var(--leaf); font: inherit; font-weight: 700; font-size: 0.84rem; cursor: pointer; padding: 6px 0 0; }
.toggle-history:hover { text-decoration: underline; }

/* ---------- Notices ---------- */
.notice { border: 1px solid var(--line); border-radius: var(--radius); padding: 14px 16px; margin-bottom: 12px; background: var(--card); }
.notice.important { background: var(--mint); border-color: var(--leaf); }
.notice h3 { font-size: 0.98rem; color: var(--forest); display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.notice p { font-size: 0.9rem; margin-top: 6px; white-space: pre-wrap; }
.notice .when { color: var(--muted); font-size: 0.78rem; margin-top: 6px; }

/* ---------- Admin dashboard ---------- */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; margin-bottom: 24px; }
.stat {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow);
}
.stat .num { font-family: 'Bricolage Grotesque'; font-size: 2rem; font-weight: 700; color: var(--forest); }
.stat .lbl { font-size: 0.8rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.stat.alert { background: var(--amber-bg); border-color: var(--amber); }
.stat.alert .num { color: var(--amber); }

.filters { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; align-items: end; }
.filters > div { flex: 1; min-width: 140px; }
.filters label { margin-top: 0; }

.cat-bars { margin-top: 8px; }
.cat-bar { display: grid; grid-template-columns: 90px 1fr 30px; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 0.85rem; }
.cat-bar .bar { background: var(--mint); border-radius: 99px; height: 12px; overflow: hidden; }
.cat-bar .bar > span { display: block; height: 100%; background: var(--leaf); border-radius: 99px; }

.admin-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; align-items: center; }
.admin-actions select { width: auto; padding: 6px 10px; font-size: 0.85rem; }

/* ---------- Auth page ---------- */
.auth-wrap { min-height: 100vh; display: grid; grid-template-columns: 1fr 1fr; }
@media (max-width: 820px) { .auth-wrap { grid-template-columns: 1fr; } .auth-hero { display: none; } }
.auth-hero {
  background: var(--forest);
  color: #eaf6ee;
  padding: 60px 48px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.auth-hero h1 { font-size: 2.6rem; line-height: 1.15; margin: 18px 0 14px; }
.auth-hero p { opacity: 0.85; max-width: 400px; }
.auth-hero .big-leaf {
  position: absolute; right: -80px; bottom: -80px;
  width: 320px; height: 320px;
  background: rgba(127, 214, 160, 0.14);
  border-radius: var(--leaf-shape);
  transform: rotate(45deg);
}
.auth-panel { display: flex; align-items: center; justify-content: center; padding: 40px 24px; }
.auth-card { width: 100%; max-width: 420px; }
.tabs { display: flex; gap: 6px; margin-bottom: 18px; background: var(--mint); padding: 5px; border-radius: 12px; }
.tabs button {
  flex: 1; border: none; background: transparent; padding: 9px;
  font: inherit; font-weight: 700; border-radius: 9px; cursor: pointer; color: var(--forest-2);
}
.tabs button.active { background: #fff; box-shadow: var(--shadow); }

.empty { text-align: center; color: var(--muted); padding: 26px 10px; font-size: 0.92rem; }
.hidden { display: none !important; }

/* ---------- Modal ---------- */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(22,56,42,0.45);
  display: none; align-items: center; justify-content: center; z-index: 50; padding: 20px;
}
.modal-backdrop.open { display: flex; }
.modal { background: #fff; border-radius: var(--radius); padding: 24px; width: 100%; max-width: 440px; }
.modal h3 { color: var(--forest); margin-bottom: 4px; }

@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; }
}
