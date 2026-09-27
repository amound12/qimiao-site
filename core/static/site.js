// 全站通用交互：移动端菜单展开/收起（从 base.html 内联脚本外置，便于 CSP script-src 'self'）
document.querySelector('.menu-toggle').addEventListener('click', function () {
  var panel = document.querySelector('.nav-right');
  var open = panel.classList.toggle('open');
  this.setAttribute('aria-expanded', String(open));
});
