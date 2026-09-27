// 每日待办 · 交互：全部走 JSON 接口，页面不刷新
(function () {
  var form = document.getElementById('todo-form');
  var input = document.getElementById('todo-input');
  var list = document.getElementById('todo-list');
  var empty = document.getElementById('todo-empty');

  function stat(name) {
    return document.querySelector('[data-stat="' + name + '"]');
  }

  function refreshStats() {
    var items = list.querySelectorAll('.todo-item');
    var done = list.querySelectorAll('.todo-item.is-done').length;
    if (stat('total')) stat('total').textContent = items.length + ' 项';
    if (stat('done')) stat('done').textContent = done + ' 项';
    empty.hidden = items.length > 0;
  }

  // ---- 连续打卡卡片：勾选后增量刷新（失败静默降级，保留旧数字） ----
  function streakEl(name) {
    return document.querySelector('[data-streak="' + name + '"]');
  }

  function subText(s) {
    if (s.pending_today) return '连续 ' + s.current + ' 天 · 今天还没打卡';
    if (s.recent[s.recent.length - 1].checked) return '今天已打卡 ✓';
    return '今天还没打卡，续上就是第 1 天';
  }

  function renderStreak(s) {
    var el;
    if ((el = streakEl('current'))) el.textContent = s.current;
    if ((el = streakEl('sub'))) el.textContent = subText(s);
    if ((el = streakEl('meta'))) {
      var meta = '最长 ' + s.longest + ' 天 · 累计 ' + s.total + ' 天';
      if (s.milestone.next) meta += ' · 距离 ' + s.milestone.next + ' 天还有 ' + s.milestone.to_next + ' 天';
      el.textContent = meta;
    }
    if ((el = streakEl('dots'))) {
      el.innerHTML = '';
      s.recent.forEach(function (d) {
        var dot = document.createElement('span');
        dot.className = 'streak-dot' + (d.checked ? ' on' : '') + (d.is_today ? ' today' : '');
        dot.title = d.day + ' · ' + (d.checked ? '已打卡' : '未打卡');
        dot.textContent = d.label;
        el.appendChild(dot);
      });
    }
  }

  function refreshStreak() {
    fetch('/todo/api/streak')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) { if (data && data.ok) renderStreak(data.streak); })
      .catch(function () { /* 静默降级：保留旧数字，不弹错、不清空 UI */ });
  }

  // 跨天兜底：重新聚焦窗口时本地日期变了就整页刷新（轻量方案，不做状态机）
  var loadedDay = new Date().toDateString();
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden && new Date().toDateString() !== loadedDay) location.reload();
  });

  function addItem(data) {
    var li = document.createElement('li');
    li.className = 'todo-item' + (data.done ? ' is-done' : '');
    li.dataset.id = data.id;
    li.innerHTML =
      '<button class="todo-check" type="button" aria-label="切换完成状态"></button>' +
      '<span class="todo-content"></span>' +
      '<button class="todo-del" type="button" aria-label="删除">×</button>';
    li.querySelector('.todo-content').textContent = data.content;
    list.insertBefore(li, list.firstChild);
    refreshStats();
  }

  function api(method, url, body) {
    return fetch(url, {
      method: method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined
    }).then(function (r) {
      // 非 2xx（如 404 条目不存在）统一折成 {ok:false}，调用方只看 res.ok
      return r.json().catch(function () { return {}; }).then(function (data) {
        return r.ok ? data : { ok: false };
      });
    });
  }

  // 添加
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var content = input.value.trim();
    if (!content) return;
    api('POST', '/todo/api/items', { content: content }).then(function (res) {
      if (res.ok) {
        addItem(res.item);
        input.value = '';
        input.focus();
      }
    });
  });

  // 勾选 / 删除（事件委托，动态添加的条目也能响应）
  list.addEventListener('click', function (e) {
    var li = e.target.closest('.todo-item');
    if (!li) return;
    var id = li.dataset.id;

    if (e.target.closest('.todo-del')) {
      api('DELETE', '/todo/api/items/' + id).then(function (res) {
        if (res.ok) {
          li.remove();
          refreshStats();
        }
      });
    } else if (e.target.closest('.todo-check')) {
      api('PATCH', '/todo/api/items/' + id).then(function (res) {
        if (res.ok) {
          li.classList.toggle('is-done', res.item.done);
          refreshStats();
          refreshStreak();   // 勾选/取消后同步打卡卡片，页面不刷新
        }
      });
    }
  });

  refreshStats();
})();
