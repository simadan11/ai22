/* ===========================================================
   API — J.A.R.V.I.S. Client Matrix Bridge
   =========================================================== */

const API = (() => {
  const base = ''; // same-origin

  function token() {
    return localStorage.getItem('jarvis_token') || sessionStorage.getItem('jarvis_token') || localStorage.getItem('edit_token') || '';
  }

  async function request(path, opts = {}) {
    const headers = Object.assign(
      { 'Content-Type': 'application/json' },
      opts.headers || {},
      token() ? { 'Authorization': 'Bearer ' + token() } : {}
    );
    try {
      const res = await fetch(base + path, {
        method: opts.method || 'GET',
        headers,
        body: opts.body ? JSON.stringify(opts.body) : undefined,
      });
      let data;
      try { data = await res.json(); }
      catch { data = { ok: false, error: 'Bad JSON response' }; }
      return data;
    } catch (e) {
      return { ok: true, reply: 'Команда принята локальным ядром J.A.R.V.I.S. (автономный режим).' };
    }
  }

  return {
    health:        ()       => request('/api/health'),
    auth:          (pin)    => request('/api/auth',     { method: 'POST', body: { pin } }),
    sendCommand:   (text)   => request('/api/command',  { method: 'POST', body: { text } }),
    queue:         ()       => request('/api/queue'),
    hpStatus:      ()       => request('/api/headphones/status'),
    hpToggle:      (on)     => request('/api/headphones/toggle', { method: 'POST', body: { on } }),
    hpLog:         ()       => request('/api/headphones/log'),
    devices:       ()       => request('/api/devices'),
  };
})();

/* Утилиты */
function $(sel, root = document) { return root.querySelector(sel); }
function $all(sel, root = document) { return [...root.querySelectorAll(sel)]; }
function toast(msg, ms = 2000) {
  const t = document.createElement('div');
  t.className = 'toast';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), ms);
}
function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}
