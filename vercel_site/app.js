// EDIT — мобильный клиент (Vercel)
// Пароль → /api/chat → Gemini → ответ + озвучка (TTS телефона → наушники)

(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const feed = $("feed");
  const login = $("login");
  const app = $("app");
  const pill = $("pill");
  const stTxt = $("st");
  const inp = $("inp");
  const pass = $("pass");
  const loginBtn = $("login-btn");
  const loginErr = $("login-err");
  const micBtn = $("mic-btn");
  const sendBtn = $("send-btn");
  const ttsBtn = $("tts-btn");
  const hpBtn = $("hp-btn");

  let password = sessionStorage.getItem("edit_pass") || "";
  let history = [];            // [{role:'user'|'assistant', content}]
  let busy = false;
  let ttsOn = true;
  let hpOn = false;
  let recognition = null;
  let listening = false;
  let wakeLock = null;
  let hpAudio = null;

  // ── статус ───────────────────────────────────────────────────────────────
  function setStatus(mode, text) {
    pill.className = "pill " + (mode === "on" ? "on" : mode === "err" ? "err" : "");
    stTxt.textContent = text;
  }

  // ── сообщения ────────────────────────────────────────────────────────────
  function addMsg(cls, text) {
    const d = document.createElement("div");
    d.className = "msg " + cls;
    d.textContent = text;
    feed.appendChild(d);
    feed.scrollTop = feed.scrollHeight;
    return d;
  }
  function sysMsg(text) { addMsg("msg-sys", text); }

  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // ── вход ─────────────────────────────────────────────────────────────────
  function showApp() {
    login.style.display = "none";
    app.classList.add("active");
    sysMsg("Вход выполнен. EDIT готов — напиши или нажми 🎤, чтобы говорить. Тап по наушнику — тоже «говорить».");
  }

  async function tryLogin() {
    const p = pass.value.trim();
    if (!p) { loginErr.textContent = "Введи пароль"; return; }
    loginBtn.disabled = true;
    loginErr.textContent = "";
    try {
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: p, messages: [{ role: "user", content: "Проверка" }] }),
      });
      const j = await r.json();
      if (r.ok && j.ok) {
        password = p;
        sessionStorage.setItem("edit_pass", p);
        showApp();
      } else if (r.status === 401) {
        loginErr.textContent = "Неверный пароль";
      } else {
        loginErr.textContent = j.error || "Ошибка сервера";
      }
    } catch (e) {
      loginErr.textContent = "Нет соединения с сервером";
    } finally {
      loginBtn.disabled = false;
    }
  }

  loginBtn.addEventListener("click", tryLogin);
  pass.addEventListener("keydown", (e) => { if (e.key === "Enter") tryLogin(); });

  if (password) showApp();

  // ── отправка ─────────────────────────────────────────────────────────────
  async function send(text) {
    text = (text || "").trim();
    if (!text || busy) return;
    busy = true;
    addMsg("msg-u", text);
    history.push({ role: "user", content: text });
    const t = document.createElement("div");
    t.className = "msg msg-e typing"; t.textContent = "EDIT";
    feed.appendChild(t); feed.scrollTop = feed.scrollHeight;

    try {
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password, messages: history }),
      });
      const j = await r.json();
      if (!r.ok) {
        if (r.status === 401) { sessionStorage.removeItem("edit_pass"); location.reload(); return; }
        t.remove();
        addMsg("msg-e", "⚠️ " + (j.error || "Ошибка"));
        return;
      }
      history.push({ role: "assistant", content: j.text });
      if (history.length > 20) history = history.slice(-20);
      t.remove();
      addMsg("msg-e", j.text);
      speak(j.text);
    } catch (e) {
      t.remove();
      addMsg("msg-e", "⚠️ Нет соединения");
    } finally {
      busy = false;
    }
  }

  sendBtn.addEventListener("click", () => { send(inp.value); inp.value = ""; });
  inp.addEventListener("keydown", (e) => { if (e.key === "Enter") { send(inp.value); inp.value = ""; } });

  // ── озвучка (TTS телефона → наушники) ───────────────────────────────────
  let ttsVoice = null;
  if (window.speechSynthesis) {
    const pick = () => {
      try {
        const vs = speechSynthesis.getVoices();
        for (const v of vs) {
          if (/^(ru|uk)-/i.test(v.lang)) { ttsVoice = v; break; }
        }
      } catch (_) {}
    };
    pick();
    try { speechSynthesis.onvoiceschanged = pick; } catch (_) {}
  }

  function speak(text) {
    if (!ttsOn || !window.speechSynthesis) return;
    try {
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text.replace(/[#*_`\[\]]/g, ""));
      if (ttsVoice) u.voice = ttsVoice;
      u.lang = (ttsVoice && ttsVoice.lang) || "ru-RU";
      u.rate = 1.0;
      speechSynthesis.speak(u);
      holdWakeLock();
    } catch (_) {}
  }

  ttsBtn.addEventListener("click", () => {
    ttsOn = !ttsOn;
    ttsBtn.textContent = ttsOn ? "🔊" : "🔇";
    ttsBtn.classList.toggle("off", !ttsOn);
    if (!ttsOn && window.speechSynthesis) speechSynthesis.cancel();
  });

  // ── голосовой ввод (микрофон) ────────────────────────────────────────────
  function startRecognition() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { sysMsg("Распознавание речи не поддерживается этим браузером"); return; }
    if (listening) { stopRecognition(); return; }
    try {
      const rec = new SR();
      rec.lang = "ru-RU";
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      rec.onstart = () => { listening = true; micBtn.textContent = "⏹"; micBtn.classList.add("off"); holdWakeLock(); };
      rec.onresult = (e) => {
        const txt = e.results[0][0].transcript.trim();
        if (txt) { inp.value = ""; send(txt); }
      };
      rec.onerror = (e) => { sysMsg("Микрофон: " + (e.error || "ошибка")); stopRecognition(); };
      rec.onend = () => stopRecognition();
      recognition = rec;
      rec.start();
    } catch (_) { sysMsg("Не удалось запустить микрофон"); }
  }
  function stopRecognition() {
    listening = false;
    micBtn.textContent = "🎤";
    micBtn.classList.remove("off");
    if (recognition) { try { recognition.stop(); } catch (_) {} recognition = null; }
    releaseWakeLockIfIdle();
  }
  micBtn.addEventListener("click", startRecognition);

  // ── кнопка наушников (AVRCP) = «говорить» ────────────────────────────────
  function enableHpMode() {
    hpOn = true;
    hpBtn.classList.add("off");
    hpBtn.title = "Режим наушников ON — тап по наушнику = говорить";
    if ("mediaSession" in navigator) {
      try {
        navigator.mediaSession.metadata = new MediaMetadata({ title: "EDIT — Headphones", artist: "EDIT" });
        const press = () => { stopTts(); startRecognition(); };
        for (const a of ["playpause", "play", "pause", "previoustrack", "nexttrack"]) {
          try { navigator.mediaSession.setActionHandler(a, press); } catch (_) {}
        }
      } catch (_) {}
    }
    // тихий аудио-цикл — держит вкладку активной медиа-сессией
    try {
      if (!hpAudio) {
        hpAudio = new Audio(silentWav());
        hpAudio.loop = true; hpAudio.volume = 0; hpAudio.muted = true;
        hpAudio.play().catch(() => {});
      }
    } catch (_) {}
    sysMsg("🎧 Режим наушников включён. Тап по наушнику — EDIT слушает.");
  }
  hpBtn.addEventListener("click", enableHpMode);

  function silentWav() {
    const sr = 8000, n = sr / 10;
    const buf = new ArrayBuffer(44 + n * 2);
    const dv = new DataView(buf);
    const ascii = (o, s) => { for (let i = 0; i < s.length; i++) dv.setUint8(o + i, s.charCodeAt(i)); };
    ascii(0, "RIFF"); dv.setUint32(4, 36 + n * 2, true); ascii(8, "WAVE");
    ascii(12, "fmt "); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true);
    dv.setUint16(22, 1, true); dv.setUint32(24, sr, true); dv.setUint32(28, sr * 2, true);
    dv.setUint16(32, 2, true); dv.setUint16(34, 16, true);
    ascii(36, "data"); dv.setUint32(40, n * 2, true);
    return URL.createObjectURL(new Blob([buf], { type: "audio/wav" }));
  }

  function stopTts() { if (window.speechSynthesis) { try { speechSynthesis.cancel(); } catch (_) {} } }

  // ── Wake Lock — экран не гаснет, пока говорим/слушаем ────────────────────
  async function holdWakeLock() {
    try {
      if (navigator.wakeLock && navigator.wakeLock.request && !wakeLock) {
        wakeLock = await navigator.wakeLock.request("screen");
        wakeLock.addEventListener("release", () => { wakeLock = null; });
      }
    } catch (_) {}
  }
  function releaseWakeLockIfIdle() {
    if (window.speechSynthesis && speechSynthesis.speaking) return;
    if (listening) return;
    try { if (wakeLock) wakeLock.release(); } catch (_) {}
    wakeLock = null;
  }
  if (window.speechSynthesis) {
    setInterval(() => { if (!speechSynthesis.speaking && !listening && wakeLock) releaseWakeLockIfIdle(); }, 4000);
  }
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && (speechSynthesis.speaking || listening)) holdWakeLock();
  });

  // ── сеть ─────────────────────────────────────────────────────────────────
  function net() {
    if (!navigator.onLine) setStatus("err", "нет сети");
    else setStatus("on", "EDIT онлайн");
  }
  window.addEventListener("online", net);
  window.addEventListener("offline", net);
  net();
  setInterval(net, 15000);

  // PWA install
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => { navigator.serviceWorker.register("/sw.js").catch(() => {}); });
  }
})();
