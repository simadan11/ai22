// EDIT — полная веб-копия приложения: HUD, голос, наушники, память, инструменты.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const feed = $("feed"), login = $("login"), app = $("app"), settings = $("settings");
  const pill = $("pill"), stTxt = $("st");
  const orb = $("orb"), orbLetter = $("orb-letter"), hudState = $("hud-state"), hudSub = $("hud-sub");
  const inp = $("inp"), micBtn = $("mic-btn"), sendBtn = $("send-btn");
  const ttsBtn = $("tts-btn"), hpBtn = $("hp-btn"), setBtn = $("set-btn"), outBtn = $("out-btn");
  const pass = $("pass"), apiKey = $("apikey"), eye = $("eye"), loginBtn = $("login-btn"), loginErr = $("login-err");
  const toastEl = $("toast");

  // ── state ──────────────────────────────────────────────────────────────
  let password = sessionStorage.getItem("edit_pass") || "";
  let apiKeySaved = sessionStorage.getItem("edit_apikey") || "";
  let history = [];
  let busy = false;
  let ttsOn = true;
  let hpOn = false;
  let recognition = null;
  let listening = false;
  let alwaysListen = false;
  let wakeLock = null;
  let hpAudio = null;
  let reminders = [];
  let state = "idle";   // idle | listen | speak | think | err

  const profile = {
    name: localStorage.getItem("edit_asst") || "EDIT",
    user: localStorage.getItem("edit_user") || "",
    city: localStorage.getItem("edit_city") || "",
    lang: localStorage.getItem("edit_lang") || "ru-RU",
    rate: parseFloat(localStorage.getItem("edit_rate") || "1"),
  };
  $("asst-name").textContent = profile.name;

  // ── helpers ────────────────────────────────────────────────────────────
  function toast(msg) {
    toastEl.textContent = msg; toastEl.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => toastEl.classList.remove("show"), 2600);
  }
  function setState(s) {
    state = s;
    orb.className = "orb" + (s === "listen" ? " listen" : s === "speak" ? " speak" : s === "think" ? " think" : "");
    const map = {
      idle:   ["", "НАЖМИ НА ОРБ И ГОВОРИ", "или скажи «EDIT, …»"],
      listen: ["listen", "СЛУШАЮ…", "говори"],
      speak:  ["speak", "ГОВОРЮ…", ""],
      think:  ["think", "ДУМАЮ…", ""],
      err:    ["err", "НЕТ СЕТИ", ""],
    };
    const [cls, t, sub] = map[s] || map.idle;
    pill.className = "pill" + (cls ? " " + cls : "");
    stTxt.textContent = t;
    hudState.className = "hud-state" + (cls ? " " + cls : "");
    hudState.textContent = t;
    hudSub.textContent = sub;
  }
  function esc(s) { return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

  // ── messages ───────────────────────────────────────────────────────────
  function addRow(cls, content, tool) {
    const row = document.createElement("div");
    row.className = "row " + cls;
    const av = document.createElement("div");
    av.className = "avatar " + (cls === "edit" ? "edit" : "me");
    av.innerHTML = cls === "edit" ? "<span>" + esc(profile.name[0] || "E") + "</span>" : "🙂";
    const m = document.createElement("div");
    m.className = "msg" + (tool ? " tool" : "");
    m.textContent = content;
    row.appendChild(av); row.appendChild(m);
    feed.appendChild(row); feed.scrollTop = feed.scrollHeight;
    return row;
  }
  function sysMsg(text) {
    const d = document.createElement("div");
    d.className = "msg msg-sys"; d.textContent = text;
    feed.appendChild(d); feed.scrollTop = feed.scrollHeight;
  }
  function addTyping() {
    const row = document.createElement("div");
    row.className = "row edit";
    const av = document.createElement("div");
    av.className = "avatar edit";
    av.innerHTML = "<span>" + esc(profile.name[0] || "E") + "</span>";
    const m = document.createElement("div");
    m.className = "msg typing"; m.innerHTML = "<i></i><i></i><i></i>";
    row.appendChild(av); row.appendChild(m);
    feed.appendChild(row); feed.scrollTop = feed.scrollHeight;
    return row;
  }

  // ── login ──────────────────────────────────────────────────────────────
  function showApp() {
    login.style.display = "none";
    app.classList.add("active");
    $("asst-name").textContent = profile.name;
    sysMsg("EDIT готов. Нажми на орб (или тапни по наушнику) и говори. Скажи «EDIT, …» — и я отвечу.");
    if (alwaysListen) startAlwaysListen();
  }
  async function tryLogin() {
    const p = pass.value.trim(), k = apiKey.value.trim();
    if (!p) { loginErr.textContent = "Введи пароль"; return; }
    loginBtn.disabled = true; loginBtn.textContent = "Проверка…"; loginErr.textContent = "";
    try {
      const r = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: p, api_key: k, messages: [{ role: "user", content: "Проверка" }] }) });
      const j = await r.json();
      if (r.ok && j.ok) {
        password = p; apiKeySaved = k;
        sessionStorage.setItem("edit_pass", p);
        if (k) sessionStorage.setItem("edit_apikey", k);
        showApp();
      } else if (r.status === 401) loginErr.textContent = "Неверный пароль";
      else loginErr.textContent = j.error || "Ошибка сервера";
    } catch (_) { loginErr.textContent = "Нет соединения"; }
    finally { loginBtn.disabled = false; loginBtn.textContent = "ВОЙТИ"; }
  }
  loginBtn.addEventListener("click", tryLogin);
  pass.addEventListener("keydown", (e) => { if (e.key === "Enter") tryLogin(); });
  apiKey.addEventListener("keydown", (e) => { if (e.key === "Enter") tryLogin(); });
  eye.addEventListener("click", () => {
    const show = pass.type === "password";
    pass.type = show ? "text" : "password";
    eye.textContent = show ? "🙈" : "👁";
  });
  outBtn.addEventListener("click", () => {
    sessionStorage.removeItem("edit_pass");
    location.reload();
  });

  // ── settings ───────────────────────────────────────────────────────────
  $("s-name").value = profile.name;
  $("s-user").value = profile.user;
  $("s-city").value = profile.city;
  $("s-lang").value = profile.lang;
  $("s-rate").value = profile.rate;
  $("s-rate-val").textContent = profile.rate.toFixed(2);
  $("s-rate").addEventListener("input", (e) => { $("s-rate-val").textContent = parseFloat(e.target.value).toFixed(2); });
  $("s-always").checked = localStorage.getItem("edit_always") === "1";
  setBtn.addEventListener("click", () => settings.classList.add("open"));
  $("set-close").addEventListener("click", () => settings.classList.remove("open"));
  $("s-save").addEventListener("click", () => {
    profile.name = ($("s-name").value.trim() || "EDIT");
    profile.user = $("s-user").value.trim();
    profile.city = $("s-city").value.trim();
    profile.lang = $("s-lang").value;
    profile.rate = parseFloat($("s-rate").value) || 1;
    localStorage.setItem("edit_asst", profile.name);
    localStorage.setItem("edit_user", profile.user);
    localStorage.setItem("edit_city", profile.city);
    localStorage.setItem("edit_lang", profile.lang);
    localStorage.setItem("edit_rate", profile.rate);
    alwaysListen = $("s-always").checked;
    localStorage.setItem("edit_always", alwaysListen ? "1" : "0");
    $("asst-name").textContent = profile.name;
    settings.classList.remove("open");
    toast("Настройки сохранены");
    if (alwaysListen && !listening) startAlwaysListen();
    if (!alwaysListen && listening && !manualListen) stopRecognition();
  });
  $("s-test").addEventListener("click", () => {
    const t = "Привет, " + (profile.user || "хозяин") + ". Я " + profile.name + ", твой персональный ассистент.";
    settings.classList.remove("open");
    setTimeout(() => speak(t), 300);
  });
  $("s-rem-btn").addEventListener("click", () => {
    const min = parseInt($("s-rem-min").value, 10);
    const txt = $("s-rem-text").value.trim();
    if (!min || min < 1) { toast("Введи минуты"); return; }
    if (!txt) { toast("Введи текст напоминания"); return; }
    scheduleReminder(min, txt);
    toast("Напомню через " + min + " мин: " + txt);
  });
  function scheduleReminder(min, txt) {
    if (Notification.permission === "default") Notification.requestPermission();
    const id = setTimeout(() => {
      if (Notification.permission === "granted") {
        try { new Notification("EDIT — напоминание", { body: txt }); } catch (_) {}
      }
      toast("⏰ " + txt);
      speak("Напоминаю: " + txt);
    }, min * 60000);
    reminders.push(id);
    sysMsg("⏰ Напоминание через " + min + " мин: " + txt);
  }

  // ── chat / tools ───────────────────────────────────────────────────────
  async function send(text, opts = {}) {
    text = (text || "").trim();
    if (!text || busy) return;
    busy = true;
    addRow("user", text);
    history.push({ role: "user", content: text });
    const t = addTyping();
    setState("think");
    try {
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          password, api_key: apiKeySaved,
          messages: history,
          profile: {
            user: profile.user, city: profile.city,
            lang: profile.lang.split("-")[0],
            time: new Date().toLocaleString(profile.lang === "uk-UA" ? "uk-UA" : "ru-RU"),
          },
        }),
      });
      const j = await r.json();
      if (!r.ok) {
        if (r.status === 401) { sessionStorage.removeItem("edit_pass"); location.reload(); return; }
        t.remove();
        addRow("edit", "⚠️ " + (j.error || "Ошибка"));
        setState("idle");
        return;
      }
      history.push({ role: "assistant", content: j.text });
      if (history.length > 20) history = history.slice(-20);
      t.remove();
      if (j.tool) addRow("edit", j.tool, true);
      addRow("edit", j.text);
      setState("speak");
      speak(j.text);
    } catch (_) {
      t.remove();
      addRow("edit", "⚠️ Нет соединения");
      setState("idle");
    } finally {
      busy = false;
    }
  }
  sendBtn.addEventListener("click", () => { send(inp.value); inp.value = ""; });
  inp.addEventListener("keydown", (e) => { if (e.key === "Enter") { send(inp.value); inp.value = ""; } });

  // ── TTS ────────────────────────────────────────────────────────────────
  let ttsVoice = null;
  if (window.speechSynthesis) {
    const pick = () => {
      try {
        const vs = speechSynthesis.getVoices();
        const want = profile.lang.split("-")[0];
        for (const v of vs) { if (v.lang && v.lang.startsWith(want)) { ttsVoice = v; break; } }
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
      u.lang = profile.lang;
      u.rate = profile.rate;
      u.onend = () => { setState("idle"); releaseWakeLockIfIdle(); };
      speechSynthesis.speak(u);
      holdWakeLock();
    } catch (_) {}
  }
  function stopTts() { if (window.speechSynthesis) { try { speechSynthesis.cancel(); } catch (_) {} } }
  ttsBtn.addEventListener("click", () => {
    ttsOn = !ttsOn;
    ttsBtn.textContent = ttsOn ? "🔊" : "🔇";
    ttsBtn.classList.toggle("off", !ttsOn);
    if (!ttsOn) { stopTts(); setState("idle"); }
  });

  // ── speech recognition ────────────────────────────────────────────────
  let manualListen = false;
  function startRecognition(opts = {}) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { toast("Распознавание не поддерживается этим браузером"); return; }
    if (listening) return;
    try {
      const rec = new SR();
      rec.lang = profile.lang;
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      manualListen = !!opts.manual;
      rec.onstart = () => { listening = true; micBtn.classList.add("rec"); micBtn.querySelector(".mic-ico").textContent = "🔴"; setState("listen"); holdWakeLock(); };
      rec.onresult = (e) => {
        const txt = e.results[0][0].transcript.trim();
        if (!txt) return;
        // wake-word: "edit"/"эдит" в начале → команда; иначе игнор (в режиме всегда-слушать)
        const m = txt.match(/^(?:edit|edith|эдит|едит|джарвис)[\s,.:]+(.*)$/i);
        if (m) { send(m[1] || "привет"); return; }
        if (manualListen) { send(txt); return; }
        // случайный текст без wake-word — не отвечаем
      };
      rec.onerror = (e) => { if (e.error !== "aborted" && e.error !== "no-speech") toast("Микрофон: " + e.error); };
      rec.onend = () => {
        listening = false;
        micBtn.classList.remove("rec");
        micBtn.querySelector(".mic-ico").textContent = "🎤";
        if (alwaysListen && !busy && !manualListen) {
          setTimeout(() => { if (alwaysListen && !listening) startRecognition(); }, 250);
        }
        if (!speechSynthesis.speaking) setState("idle");
        releaseWakeLockIfIdle();
      };
      recognition = rec;
      rec.start();
    } catch (_) { toast("Не удалось запустить микрофон"); }
  }
  function stopRecognition() {
    if (recognition) { try { recognition.stop(); } catch (_) {} recognition = null; }
    listening = false;
    micBtn.classList.remove("rec");
    micBtn.querySelector(".mic-ico").textContent = "🎤";
  }
  micBtn.addEventListener("click", () => {
    if (listening) { stopRecognition(); setState("idle"); return; }
    startRecognition({ manual: true });
  });
  orb.addEventListener("click", () => {
    if (listening) { stopRecognition(); setState("idle"); return; }
    startRecognition({ manual: true });
  });
  function startAlwaysListen() {
    if (!window.SpeechRecognition && !window.webkitSpeechRecognition) return;
    if (!listening) startRecognition();
  }

  // ── headphones (AVRCP) ────────────────────────────────────────────────
  function enableHpMode() {
    hpOn = true;
    hpBtn.classList.add("on");
    hpBtn.title = "Режим наушников ON — тап по наушнику = говорить";
    if ("mediaSession" in navigator) {
      try {
        navigator.mediaSession.metadata = new MediaMetadata({ title: profile.name + " — Headphones", artist: profile.name });
        const press = () => { stopTts(); if (listening) { stopRecognition(); setState("idle"); } else startRecognition({ manual: true }); };
        for (const a of ["playpause", "play", "pause", "previoustrack", "nexttrack"]) {
          try { navigator.mediaSession.setActionHandler(a, press); } catch (_) {}
        }
      } catch (_) {}
    }
    try {
      if (!hpAudio) {
        hpAudio = new Audio(silentWav());
        hpAudio.loop = true; hpAudio.volume = 0; hpAudio.muted = true;
        hpAudio.play().catch(() => {});
      }
    } catch (_) {}
    toast("🎧 Наушники: тап по наушнику — говорить");
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

  // ── wake lock ─────────────────────────────────────────────────────────
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
  setInterval(() => { if (!speechSynthesis.speaking && !listening && wakeLock) releaseWakeLockIfIdle(); }, 5000);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      if (speechSynthesis.speaking || listening || alwaysListen) holdWakeLock();
      if (alwaysListen && !listening) startAlwaysListen();
    }
  });

  // ── network ────────────────────────────────────────────────────────────
  function net() {
    if (!navigator.onLine) setState("err");
    else if (state === "err") setState("idle");
  }
  window.addEventListener("online", net);
  window.addEventListener("offline", net);
  net();
  setInterval(net, 15000);

  // ── particles ──────────────────────────────────────────────────────────
  (function makeParticles() {
    const wrap = $("particles");
    if (!wrap) return;
    const n = Math.min(24, Math.floor(window.innerWidth / 16));
    for (let i = 0; i < n; i++) {
      const p = document.createElement("i");
      const s = 2 + Math.random() * 5;
      p.style.width = p.style.height = s + "px";
      p.style.left = Math.random() * 100 + "%";
      p.style.animationDuration = (7 + Math.random() * 9) + "s";
      p.style.animationDelay = (Math.random() * 8) + "s";
      wrap.appendChild(p);
    }
  })();

  // ── PWA ───────────────────────────────────────────────────────────────
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => { navigator.serviceWorker.register("/sw.js").catch(() => {}); });
  }

  if (password && apiKeySaved) showApp();
})();
