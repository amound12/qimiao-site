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
        }
      });
    }
  });

  refreshStats();
})();
