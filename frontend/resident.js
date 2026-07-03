/* Shared API helper — token storage + fetch wrapper */

const API = {
  base: '',

  token() { return localStorage.getItem('nivaas_token'); },
  user() {
    try { return JSON.parse(localStorage.getItem('nivaas_user')); }
    catch { return null; }
  },

  saveSession(data) {
    localStorage.setItem('nivaas_token', data.access_token);
    localStorage.setItem('nivaas_user', JSON.stringify(data.user));
  },

  logout() {
    localStorage.removeItem('nivaas_token');
    localStorage.removeItem('nivaas_user');
    window.location.href = '/index.html';
  },

  async request(path, { method = 'GET', body = null, isForm = false } = {}) {
    const headers = {};
    if (this.token()) headers['Authorization'] = `Bearer ${this.token()}`;
    if (body && !isForm) headers['Content-Type'] = 'application/json';

    const res = await fetch(this.base + path, {
      method,
      headers,
      body: body ? (isForm ? body : JSON.stringify(body)) : null,
    });

    if (res.status === 401 && !path.startsWith('/api/auth')) {
      this.logout();
      return;
    }

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = Array.isArray(data.detail)
        ? data.detail.map(d => d.msg).join(', ')
        : (data.detail || 'Something went wrong');
      throw new Error(detail);
    }
    return data;
  },
};

/* Guard a page: redirect if not logged in / wrong role */
function requireRole(role) {
  const user = API.user();
  if (!user || !API.token()) { window.location.href = '/index.html'; return null; }
  if (role && user.role !== role) {
    window.location.href = user.role === 'admin' ? '/admin.html' : '/resident.html';
    return null;
  }
  return user;
}

/* Small helpers */
function fmtDate(iso) {
  return new Date(iso + (iso.endsWith('Z') ? '' : 'Z')).toLocaleString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit',
  });
}
function esc(s) {
  const div = document.createElement('div');
  div.textContent = s ?? '';
  return div.innerHTML;
}
function statusClass(s) { return s.replace(/\s+/g, ''); }
