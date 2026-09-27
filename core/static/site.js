// 全站通用交互：移动端菜单展开/收起（从 base.html 内联脚本外置，便于 CSP script-src 'self'）
document.querySelector('.menu-toggle').addEventListener('click', function () {
  var panel = document.querySelector('.nav-right');
  var open = panel.classList.toggle('open');
  this.setAttribute('aria-expanded', String(open));
});

/* ============================================================
 * 「打个招呼」三态轻交互（v0.2）
 * - 模式 A：随机问候气泡；模式 B：小动画 + 一句话（A/B 随机）
 * - 模式 C：第 10 次点击的彩蛋（背景渐变 + 小猫走过），播完归零循环
 * - 计数持久化 localStorage（qimiao:greet:count），刷新不丢
 * - 动效全部 CSS keyframes + 内联 SVG（CSP: script-src 'self'，无外链）
 * - prefers-reduced-motion: reduce 时跳过位移动画，只显示文案
 * ============================================================ */
(function () {
  var btn = document.getElementById('greet-btn');
  if (!btn) return;

  var KEY = 'qimiao:greet:count';
  var CYCLE = 10;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var eggLock = false;        // 彩蛋播放中加锁：忽略新点击，防两场重叠
  var toastNode = null;
  var toastTimer = null;

  var TOASTS = [
    '嗨，今天过得怎么样？',
    '有没有好好吃饭？',
    '今天也辛苦啦。',
    '摸鱼也是正经事。',
    '喝口水吧。',
    '慢慢来，不着急。',
    '抬头看看天，让眼睛歇会儿。',
    '你点的每一次，我都有收到。',
    '保持热爱，继续折腾。',
    '睡前记得放下手机。'
  ];

  var B_LINES = ['收到你的招呼啦 👋', '嗨，我在呢。', '叮——问候已送达。'];

  var EGG_LINES = [
    '喵呜——被你发现啦，这是第 10 次打招呼的奖励。',
    '第 10 次了，你和我一样爱折腾。'
  ];

  function readCount() {
    var n = parseInt(localStorage.getItem(KEY) || '0', 10);
    return isNaN(n) || n < 0 ? 0 : n;
  }

  function writeCount(n) {
    try { localStorage.setItem(KEY, String(n)); } catch (e) { /* 隐私模式等：静默降级 */ }
    var m = n % CYCLE;
    // 低调的进度提示：只在有计数时出现，不剧透彩蛋
    btn.title = m > 0 ? '神秘进度 ' + m + '/' + CYCLE : '打个招呼试试';
  }

  function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

  /* ---- 模式 A：问候气泡（单例节点，重复点击重置计时而非叠加） ---- */
  function showToast(text, hold) {
    if (toastNode) { toastNode.remove(); toastNode = null; }
    clearTimeout(toastTimer);
    toastNode = document.createElement('div');
    toastNode.className = 'greet-toast';
    toastNode.setAttribute('role', 'status');
    toastNode.setAttribute('aria-live', 'polite');
    toastNode.textContent = text;
    document.body.appendChild(toastNode);
    requestAnimationFrame(function () {
      if (toastNode) toastNode.classList.add('show');
    });
    toastTimer = setTimeout(function () {
      var node = toastNode;
      if (!node) return;
      node.classList.remove('show');
      setTimeout(function () {
        node.remove();
        if (toastNode === node) toastNode = null;
      }, 320);
    }, hold || 2500);
  }

  /* ---- 模式 B：三选一小动画，播完（约 1.2s）补一句话 ---- */
  function artNode(className, inner) {
    var wrap = document.createElement('div');
    wrap.className = 'greet-art-wrap';
    wrap.setAttribute('aria-hidden', 'true');
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'greet-art ' + className);
    svg.setAttribute('viewBox', '0 0 64 64');
    svg.innerHTML = inner;
    wrap.appendChild(svg);
    document.body.appendChild(wrap);
    return wrap;
  }

  function playWave() {
    var wrap = artNode('greet-wave',
      '<g class="wave-arm">' +
      '<path d="M26 46 C24 38 24 26 30 14" />' +
      '<path d="M34 46 C33 36 34 24 40 12" />' +
      '<path d="M42 46 C43 38 45 28 50 20" />' +
      '<path d="M22 48 C26 54 40 55 46 49 C50 45 50 40 47 36" />' +
      '</g>');
    setTimeout(function () { wrap.remove(); }, 1200);
  }

  function playFace() {
    var wrap = artNode('greet-face',
      '<circle cx="32" cy="32" r="22" class="ink-line" fill="none"/>' +
      '<circle cx="25" cy="27" r="2.4" class="ink-dot"/>' +
      '<circle cx="39" cy="27" r="2.4" class="ink-dot"/>' +
      '<path d="M22 38 C26 44 38 44 42 38" class="ink-line" fill="none"/>');
    setTimeout(function () { wrap.remove(); }, 1200);
  }

  function playConfetti() {
    var rect = btn.getBoundingClientRect();
    var colors = ['var(--accent)', 'var(--accent-dark)', 'var(--star-yellow)', 'var(--accent-back)', 'var(--accent-soft)'];
    var box = document.createElement('div');
    box.className = 'greet-confetti-box';
    box.setAttribute('aria-hidden', 'true');
    for (var i = 0; i < 24; i++) {
      var s = document.createElement('span');
      s.className = 'greet-confetti';
      var size = 6 + Math.round(Math.random() * 6);
      s.style.cssText =
        'left:' + Math.round(rect.left + rect.width / 2 + (Math.random() * 160 - 80)) + 'px;' +
        'width:' + size + 'px;height:' + Math.round(size * 0.6) + 'px;' +
        'background:' + colors[i % colors.length] + ';' +
        'animation-delay:' + (Math.random() * 0.3).toFixed(2) + 's;' +
        '--spin:' + (Math.random() > 0.5 ? '' : '-') + (360 + Math.round(Math.random() * 360)) + 'deg';
      box.appendChild(s);
    }
    document.body.appendChild(box);
    setTimeout(function () { box.remove(); }, 1600);
  }

  function playModeB() {
    if (reduced.matches) { showToast(pick(B_LINES)); return; }
    var roll = Math.floor(Math.random() * 3);
    if (roll === 0) playWave();
    else if (roll === 1) playFace();
    else playConfetti();
    setTimeout(function () { showToast(pick(B_LINES)); }, 1200);
  }

  /* ---- 模式 C：十连彩蛋（背景渐变 + 小猫走过 + 文案），4 秒后彻底清理 ---- */
  function buildCat() {
    var cat = document.createElement('div');
    cat.className = 'greet-cat';
    cat.setAttribute('aria-hidden', 'true');
    // 手绘侧身小猫：身体/头/耳/尾一笔线稿，腿部两组交替摆动出踏步感
    cat.innerHTML =
      '<svg viewBox="0 0 140 80" class="cat-svg">' +
      '<g class="cat-bob">' +
      '<path class="cat-line" d="M22 52 C20 40 30 30 48 30 C66 30 84 32 96 34"/>' +  // 背线
      '<path class="cat-line" d="M96 34 C104 32 110 26 112 18 L118 24 L124 17 C126 26 124 32 118 36 C114 40 108 42 102 42"/>' + // 头+耳
      '<path class="cat-line" d="M22 52 C18 54 14 54 10 50 C6 46 8 38 14 34 C10 32 8 28 10 24" />' + // 尾巴
      '<path class="cat-line" d="M46 52 C48 56 52 58 58 58"/>' +  // 腹线
      '<g class="leg leg-a"><path class="cat-line" d="M40 52 L38 70"/><path class="cat-line" d="M52 54 L52 70"/></g>' +
      '<g class="leg leg-b"><path class="cat-line" d="M70 54 L72 70"/><path class="cat-line" d="M84 52 L88 70"/></g>' +
      '<g class="whiskers">' +
      '<path class="cat-line thin" d="M108 32 L122 30"/><path class="cat-line thin" d="M108 36 L122 38"/>' +
      '</g>' +
      '<circle cx="114" cy="27" r="1.6" class="ink-dot"/>' +
      '</g></svg>';
    return cat;
  }

  function playEgg(done) {
    if (reduced.matches) {
      // 减少动态效果：只给文案，不做任何位移/闪烁
      showToast(pick(EGG_LINES), 3600);
      done();
      return;
    }
    var veil = document.createElement('div');
    veil.className = 'greet-egg-veil';
    veil.setAttribute('aria-hidden', 'true');
    var cat = buildCat();
    document.body.appendChild(veil);
    document.body.appendChild(cat);
    setTimeout(function () { showToast(pick(EGG_LINES), 2600); }, 900);
    setTimeout(function () {
      veil.remove();
      cat.remove();
      done();
    }, 4200);
  }

  btn.addEventListener('click', function () {
    if (eggLock) return;                       // 彩蛋播放中：忽略点击（加锁防重叠）
    var next = readCount() + 1;
    if (next % CYCLE === 0) {
      writeCount(0);                           // 第 10 次必彩蛋，播完归零重新循环
      eggLock = true;
      playEgg(function () { eggLock = false; });
    } else {
      writeCount(next);
      if (Math.random() < 0.5) showToast(pick(TOASTS));
      else playModeB();
    }
  });

  writeCount(readCount());
})();
