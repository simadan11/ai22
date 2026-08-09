/* ===========================================================
   Главный пульт
   =========================================================== */

(async function init() {
  if (!localStorage.getItem('edit_token')) { location.href = '/pin.html'; return; }

  // Статус подключения
  const statusEl = $('#connStatus');
  try {
    const h = await API.health();
    if (h.ok) {
      statusEl.classList.remove('offline');
      statusEl.querySelector('.text').textContent = 'online';
      if (h.greeting) $('#greeting').textContent = h.greeting;
      if (h.subtitle) $('#heroSub').textContent = h.subtitle;
    } else throw new Error('not ok');
  } catch (e) {
    statusEl.classList.add('offline');
    statusEl.querySelector('.text').textContent = 'offline';
  }

  // Кнопки быстрых команд
  $all('.tile').forEach(tile => {
    tile.addEventListener('click', () => {
      const cmd = tile.dataset.cmd;
      handleCommand(cmd, tile.querySelector('.tile-title').textContent);
    });
  });

  // Чат
  const form = $('#chatForm');
  const field = $('#chatField');
  const log = $('#chatLog');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = field.value.trim();
    if (!text) return;
    field.value = '';
    await handleCommand(text, null);
  });

  async function handleCommand(text, label) {
    addMsg('user', label || text);
    const t = addMsg('bot', 'Думаю…', true);

    try {
      const r = await API.sendCommand(text);
      t.classList.remove('typing');
      if (r.ok) {
        t.querySelector('.msg-bubble').textContent = r.reply || 'Готово ✓';
      } else {
        t.querySelector('.msg-bubble').textContent = 'Ошибка: ' + (r.error || 'unknown');
      }
    } catch (e) {
      t.classList.remove('typing');
      t.querySelector('.msg-bubble').textContent = 'Нет связи с сервером';
    }
    log.scrollTop = log.scrollHeight;
  }

  function addMsg(who, text, typing = false) {
    const div = document.createElement('div');
    div.className = `msg who-${who === 'bot' ? 'bot' : 'user'}` + (typing ? ' typing' : '');
    div.innerHTML = `
      <div class="msg-who">${who === 'bot' ? 'EDIT' : 'ВЫ'}</div>
      <div class="msg-bubble">${esc(text)}</div>
    `;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
    return div;
  }

  // Logout
  const logout = () => {
    localStorage.removeItem('edit_token');
    location.href = '/pin.html';
  };
  $('#logoutBtn')?.addEventListener('click', (e) => { e.preventDefault(); logout(); });
  $('#logoutBtn2')?.addEventListener('click', (e) => { e.preventDefault(); logout(); });
})();
