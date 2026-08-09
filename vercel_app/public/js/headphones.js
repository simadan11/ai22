/* ===========================================================
   Режим наушников — UI + push-to-talk + визуализатор
   =========================================================== */

(async function init() {
  if (!localStorage.getItem('edit_token')) { location.href = '/pin.html'; return; }

  const orb         = $('#hpOrb');
  const hero        = $('.hp-hero');
  const push        = $('#hpPush');
  const pushLabel   = $('#hpPushLabel');
  const toggle      = $('#hpToggleMode');
  const sync        = $('#hpSync');
  const devEl       = $('#hpDevice');
  const micEl       = $('#hpMic');
  const actEl       = $('#hpActivity');
  const logEl       = $('#hpLog');
  const barsWrap    = $('#hpBars');
  const statusEl    = $('#hpStatus');

  // Генерация баров визуализатора
  const BARS = 28;
  const bars = [];
  for (let i = 0; i < BARS; i++) {
    const s = document.createElement('span');
    barsWrap.appendChild(s);
    bars.push(s);
  }
  let levelRaf = null;
  let listening = false;
  let micStream = null;
  let audioCtx  = null;
  let analyser  = null;
  let micData   = null;

  // Первичная загрузка статуса
  await refresh();

  // Кнопка toggle режима
  toggle.addEventListener('click', async () => {
    const wasOn = toggle.classList.contains('on');
    try {
      const r = await API.hpToggle(!wasOn);
      if (r.ok) {
        toggle.classList.toggle('on', r.enabled);
        toggle.textContent = r.enabled ? 'Выключить режим' : 'Включить режим';
        addLog(r.enabled ? 'Режим наушников активирован' : 'Режим наушников выключен',
               r.enabled ? 'ok' : 'muted');
      }
    } catch {
      toast('Не удалось переключить режим');
    }
  });

  // Sync
  sync.addEventListener('click', refresh);

  async function refresh() {
    try {
      const r = await API.hpStatus();
      statusEl.classList.toggle('offline', !r.ok);
      statusEl.querySelector('.text').textContent = r.connected ? 'connected' : 'idle';
      devEl.textContent = r.device || '— не подключено —';
      micEl.textContent = r.mic    || '—';
      actEl.textContent = r.activity || 'idle';
      toggle.classList.toggle('on', !!r.enabled);
      toggle.textContent = r.enabled ? 'Выключить режим' : 'Включить режим';
    } catch {
      statusEl.classList.add('offline');
      statusEl.querySelector('.text').textContent = 'offline';
    }
  }

  // ===== Push-to-talk (hold) =====
  push.addEventListener('pointerdown', startListen);
  push.addEventListener('pointerup',   stopListen);
  push.addEventListener('pointerleave',stopListen);
  push.addEventListener('pointercancel',stopListen);

  // Клик для тех, у кого нет hold
  let holdMode = true;
  push.addEventListener('click', (e) => {
    if (holdMode) return; // pointerdown уже обработал
  });

  async function startListen(e) {
    if (e) e.preventDefault();
    if (listening) return;
    listening = true;
    push.classList.add('listening');
    hero.classList.add('listening');
    pushLabel.textContent = 'СЛУШАЮ…';
    actEl.textContent = 'listening';
    addLog('Начало записи с микрофона', 'ok');

    try {
      if (!micStream) {
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const src = audioCtx.createMediaStreamSource(micStream);
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64;
        src.connect(analyser);
        micData = new Uint8Array(analyser.frequencyBinCount);
      }
      tick();
    } catch (err) {
      addLog('Микрофон недоступен: ' + err.message, 'err');
      toast('Нет доступа к микрофону');
    }
  }

  function stopListen() {
    if (!listening) return;
    listening = false;
    push.classList.remove('listening');
    hero.classList.remove('listening');
    pushLabel.textContent = 'УДЕРЖИВАЙ И ГОВОРИ';
    actEl.textContent = 'idle';
    addLog('Конец записи', 'muted');
    if (levelRaf) { cancelAnimationFrame(levelRaf); levelRaf = null; }
    bars.forEach(b => b.style.height = '6px');
  }

  function tick() {
    if (!listening || !analyser) return;
    analyser.getByteFrequencyData(micData);
    for (let i = 0; i < BARS; i++) {
      const v = micData[i] || 0;
      const h = 6 + (v / 255) * 60;
      bars[i].style.height = h + 'px';
      bars[i].style.opacity = 0.4 + (v / 255) * 0.6;
    }
    levelRaf = requestAnimationFrame(tick);
  }

  // Лог
  function addLog(text, kind = 'muted') {
    if (logEl.querySelector('.muted') && logEl.children.length === 1) logEl.innerHTML = '';
    const li = document.createElement('li');
    li.className = kind;
    li.innerHTML = `<time>${timeNow()}</time>${esc(text)}`;
    logEl.prepend(li);
    // Не больше 30 событий
    while (logEl.children.length > 30) logEl.lastElementChild.remove();
  }

  // Периодический опрос статуса
  setInterval(refresh, 6000);

  // Logout
  $('#logoutBtn')?.addEventListener('click', (e) => { e.preventDefault(); doLogout(); });
  $('#logoutBtn2')?.addEventListener('click', (e) => { e.preventDefault(); doLogout(); });
  function doLogout() {
    localStorage.removeItem('edit_token');
    if (micStream) micStream.getTracks().forEach(t => t.stop());
    location.href = '/pin.html';
  }

  // Пред-запрос лога с сервера
  try {
    const r = await API.hpLog();
    if (r.ok && r.events) {
      logEl.innerHTML = '';
      r.events.slice().reverse().forEach(ev => addLog(ev.text, ev.kind || 'muted'));
    }
  } catch {}
})();
