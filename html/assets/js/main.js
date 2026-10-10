/* Hiệu Vàng Ngọc Diệp — tương tác (vanilla JS)
 * Nội dung (menu, sản phẩm, liên hệ...) đã in sẵn trong HTML bằng scripts/bake_static.py.
 * JS chỉ lo tương tác + cập nhật giá vàng/bạc. */
(function () {
  'use strict';

  /* ---------------- DATA ---------------- */
  // Bảng giá vàng (VNĐ / chỉ) — số mặc định; khi mở trang sẽ được thay bằng giá quy đổi từ API (loadPrices)
  var PRICES = [
    { id: '9999', name: 'Vàng 9999', buy: 14100000, sell: 14230000 },
    { id: '980', name: 'Vàng 98', buy: 13760000, sell: 13950000 },
    { id: '960', name: 'Vàng 96', buy: 13460000, sell: 13650000 },
    { id: 'NT980', name: 'Nữ Trang 98', buy: 13760000, sell: 14050000 },
    { id: '610', name: 'Vàng 610', buy: 8580000, sell: 9000000 }
  ];
  // Bảng giá bạc trang sức (VNĐ / chỉ 3,75g) — số mặc định; khi mở trang sẽ được thay bằng giá quy đổi từ API
  var SILVER_PRICES = [
    { id: 'AG925', name: 'Bạc trang sức 925 (bạc Ý)', buy: 174000, sell: 177000 },
    { id: 'AG999TS', name: 'Bạc trang sức 999 (bạc ta)', buy: 189000, sell: 192000 }
  ];
  var SILVER_UPDATED_AT = '18:00 06/10/2026';

  // Mốc giờ cập nhật của bảng giá (hiển thị ở "Cập nhật lúc ...")
  var PRICES_UPDATED_AT = '09:15 28/08/2026';

  // Danh mục sản phẩm, thông tin liên hệ: scripts/data/site.json · Sản phẩm: scripts/data/catalog.json
  // -> sửa xong chạy: python3 scripts/bake_static.py

  /* ---------------- HELPERS ---------------- */
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var fmt = function (n) { return n.toLocaleString('vi-VN').replace(/,/g, '.'); };
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  var reflow = function (el) { void el.offsetWidth; };
  var lockCount = 0;
  function lockScroll(on) {
    lockCount += on ? 1 : -1;
    if (lockCount < 0) lockCount = 0;
    var sbw = window.innerWidth - document.documentElement.clientWidth;
    document.documentElement.style.overflow = lockCount ? 'hidden' : '';
    document.body.style.paddingRight = lockCount && sbw ? sbw + 'px' : '';
  }
  function smoothTo(target) {
    var el = typeof target === 'string' ? $(target) : target;
    if (!el) return;
    var y = el === document.body ? 0 : el.getBoundingClientRect().top + window.scrollY - (parseFloat(getComputedStyle(el).scrollMarginTop) || 0);
    window.scrollTo({ top: y, behavior: 'smooth' });
  }
  // Cuộn tới mục trên trang hiện tại; nếu mục nằm ở trang chủ thì chuyển trang
  function goTo(hash) {
    if (hash === '#top' || hash === 'body') {
      if (isHome) return window.scrollTo({ top: 0, behavior: 'smooth' });
      location.href = '/'; return;
    }
    var el = $(hash);
    if (el) smoothTo(el); else location.href = '/' + hash;
  }
  var isHome = document.body.dataset.page === 'home';
  // Link tới trang danh sách sản phẩm (có thể kèm bộ lọc)
  function shopUrl(params) {
    var q = [];
    Object.keys(params || {}).forEach(function (k) { if (params[k]) q.push(k + '=' + encodeURIComponent(params[k])); });
    return '/san-pham/' + (q.length ? '?' + q.join('&') : '');
  }
  var shopApply = null; // được gán khi đang ở trang sản phẩm
  function navigateShop(params) {
    if (shopApply) shopApply(params, true);
    else location.href = shopUrl(params);
  }
  $$('.js-year').forEach(function (n) { n.textContent = new Date().getFullYear(); });

  // Link "#" / nút [data-soon]: trang con chưa có -> báo "đang cập nhật" thay vì bấm không phản hồi
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href="#"], [data-soon]');
    if (!a) return;
    e.preventDefault();
    if (/\bjs-/.test(a.className)) return; // đã có xử lý riêng
    toast('Đang cập nhật', 'Nội dung này sẽ sớm ra mắt. Quý khách vui lòng liên hệ cửa hàng để được tư vấn.');
  });

  /* ---------------- TOAST ---------------- */
  function toast(title, desc) {
    var box = $('#toasts');
    var li = document.createElement('li');
    li.className = 'toast';
    var wrap = document.createElement('div'), t = document.createElement('div');
    t.className = 'toast__title'; t.textContent = title; wrap.appendChild(t);
    if (desc) { var d = document.createElement('div'); d.className = 'toast__desc'; d.textContent = desc; wrap.appendChild(d); }
    li.appendChild(wrap);
    box.appendChild(li);
    reflow(li);
    li.classList.add('is-in');
    setTimeout(function () {
      li.classList.remove('is-in');
      setTimeout(function () { li.remove(); }, 320);
    }, 3500);
  }

  /* ---------------- THEME ---------------- */
  var root = document.documentElement;
  function syncThemeButtons() {
    var dark = !root.classList.contains('light');
    var label = dark ? 'Chuyển sang chế độ sáng' : 'Chuyển sang chế độ tối';
    $$('.js-theme').forEach(function (b) {
      b.setAttribute('aria-label', label);
      b.setAttribute('title', label);
      b.querySelector('use').setAttribute('href', dark ? '#i-sun' : '#i-moon');
    });
  }
  function applyTheme() {
    root.classList.toggle('light');
    store.set('theme-preference', root.classList.contains('light') ? 'light' : 'dark');
    syncThemeButtons();
  }
  // Đổi theme: vùng sáng/tối lan ra theo hình tròn từ điểm click (View Transitions API)
  function toggleTheme(e) {
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!document.startViewTransition || reduce) {
      applyTheme();
      if (chartLoaded) loadChart(true);
      return;
    }
    var r = e.currentTarget.getBoundingClientRect();
    var x = e.clientX || r.left + r.width / 2;
    var y = e.clientY || r.top + r.height / 2;
    var radius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
    var t = document.startViewTransition(applyTheme);
    t.ready.then(function () {
      root.animate(
        { clipPath: ['circle(0px at ' + x + 'px ' + y + 'px)', 'circle(' + radius + 'px at ' + x + 'px ' + y + 'px)'] },
        { duration: 700, easing: 'cubic-bezier(.4, 0, .2, 1)', pseudoElement: '::view-transition-new(root)' }
      );
    });
    t.finished.then(function () { if (chartLoaded) loadChart(true); });
  }
  $$('.js-theme').forEach(function (b) { b.addEventListener('click', toggleTheme); });
  syncThemeButtons();

  /* ---------------- GIÁ: cập nhật số trên bảng / dòng chạy (HTML đã có giá mặc định) ---------------- */
  var rowObserver = 'IntersectionObserver' in window ? new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) { en.target.classList.add('is-in'); rowObserver.unobserve(en.target); }
    });
  }, { threshold: 0.1 }) : null;
  $$('tr.reveal').forEach(function (tr) { if (rowObserver) rowObserver.observe(tr); else tr.classList.add('is-in'); });

  function updatePrices() {
    PRICES.concat(SILVER_PRICES).forEach(function (p) {
      $$('tr[data-id="' + p.id + '"]').forEach(function (tr) {
        $('[data-buy]', tr).textContent = fmt(p.buy);
        $('[data-sell]', tr).textContent = fmt(p.sell);
      });
      $$('.ticker__val[data-id="' + p.id + '"]').forEach(function (v) { v.textContent = fmt(p.sell); });
    });
  }

  function stamp() {
    if ($('#updated-at')) $('#updated-at').textContent = PRICES_UPDATED_AT;
    if ($('#silver-updated-at')) $('#silver-updated-at').textContent = SILVER_UPDATED_AT;
  }
  /* ---------------- GIÁ TỪ API (demo) ----------------
   * Mở trang là lấy giá vàng & bạc thế giới (USD/ounce) + tỷ giá USD/VND rồi quy đổi đổ vào bảng.
   * API miễn phí, không cần key: api.gold-api.com, open.er-api.com
   */
  function loadPrices() {
    var get = function (u) { return fetch(u).then(function (r) { return r.json(); }); };
    return Promise.all([
      get('https://api.gold-api.com/price/XAU'),
      get('https://api.gold-api.com/price/XAG'),
      get('https://open.er-api.com/v6/latest/USD')
    ]).then(function (r) {
      var vnd = r[2].rates.VND, perGram = function (usdOz) { return usdOz * vnd / 31.1035; };
      var round = function (n) { return Math.round(n / 1000) * 1000; };
      var chi = perGram(r[0].price) * 3.75;   // 1 chỉ vàng 999.9
      var chiBac = perGram(r[1].price) * 3.75; // 1 chỉ bạc nguyên chất
      var row = function (p, base, k) { p.sell = round(base * k); p.buy = round(base * k * 0.985); };
      var GOLD_K = { '9999': 1, '980': 0.98, '960': 0.96, 'NT980': 0.98, '610': 0.61 };
      PRICES.forEach(function (p) { row(p, chi, GOLD_K[p.id] || 1); });
      var SILVER_K = { AG925: 0.925, AG999TS: 0.999 }; // theo hàm lượng bạc
      SILVER_PRICES.forEach(function (p) { row(p, chiBac, SILVER_K[p.id] || 1); });
      var d = new Date(), pad = function (n) { return String(n).padStart(2, '0'); };
      PRICES_UPDATED_AT = SILVER_UPDATED_AT = pad(d.getHours()) + ':' + pad(d.getMinutes()) + ' ' + pad(d.getDate()) + '/' + pad(d.getMonth() + 1) + '/' + d.getFullYear();
      updatePrices(); stamp(); renderCalc();
    }).catch(function () { /* lỗi mạng: giữ giá mặc định */ });
  }
  $$('.js-refresh').forEach(function (b) { b.addEventListener('click', loadPrices); });

  /* ---------------- MÁY TÍNH GIÁ VÀNG / BẠC ---------------- */
  var calc = null;
  function initCalc() {
    var box = $('[data-calc]');
    if (!box) return;
    var silver = box.dataset.calc === 'silver';
    calc = { box: box, rows: silver ? SILVER_PRICES : PRICES, mode: 'sell', type: $('#calc-type'), weight: $('#calc-weight'), labor: $('#calc-labor') };
    $$('.calc-mode__btn', box).forEach(function (b) {
      b.addEventListener('click', function () {
        calc.mode = b.dataset.mode;
        $$('.calc-mode__btn', box).forEach(function (x) { var on = x === b; x.classList.toggle('is-on', on); x.setAttribute('aria-pressed', on); });
        renderCalc();
      });
    });
    calc.weight.addEventListener('input', function () {
      calc.weight.value = calc.weight.value.replace(/[^\d.,]/g, '').replace(/([.,].*)[.,]/, '$1');
      renderCalc();
    });
    calc.labor.addEventListener('input', function () {
      var d = calc.labor.value.replace(/\D/g, '');
      calc.labor.value = d ? fmt(+d) : '';
      renderCalc();
    });
    calc.type.addEventListener('change', renderCalc);
    renderCalc();
  }
  function renderCalc() {
    if (!calc) return;
    var row = calc.rows.filter(function (p) { return p.id === calc.type.value; })[0] || calc.rows[0];
    var unit = row[calc.mode];
    var w = parseFloat(calc.weight.value.replace(',', '.')) || 0;
    var sell = calc.mode === 'sell';
    var labor = sell ? (+calc.labor.value.replace(/\D/g, '') || 0) : 0;
    calc.labor.disabled = !sell;
    calc.labor.placeholder = sell ? 'Vd: 200.000' : 'Không áp dụng khi bán lại';
    var sub = Math.round(unit * w);
    $('#calc-unit').textContent = fmt(unit) + ' VNĐ';
    $('#calc-sub').textContent = fmt(sub) + ' VNĐ';
    $('#calc-labor-out').textContent = fmt(labor) + ' VNĐ';
    $('#calc-total').textContent = fmt(sub + labor) + ' VNĐ';
    $('#calc-total-lbl').textContent = sell ? 'Tổng Cộng' : 'Cửa Hàng Trả';
  }

  /* ---------------- TABS + CHART ---------------- */
  var chartLoaded = false;
  function loadChart(force) {
    if (chartLoaded && !force) return;
    chartLoaded = true;
    var dark = !root.classList.contains('light');
    var cfg = { symbol: 'OANDA:XAUUSD', interval: 'D', save_image: '0', studies: '[]', theme: dark ? 'dark' : 'light', style: '1', timezone: 'Asia/Ho_Chi_Minh', withdateranges: '1', studies_overrides: '{}' };
    var src = 'https://s.tradingview.com/widgetembed/?hideideas=1&overrides=%7B%7D&enabled_features=%5B%5D&disabled_features=%5B%5D&locale=vi#' + encodeURIComponent(JSON.stringify(cfg));
    $('#chart-frame').innerHTML = '<iframe title="Biểu đồ giá vàng thế giới XAUUSD" src="' + src + '" allowtransparency="true" scrolling="no" allowfullscreen loading="lazy"></iframe>';
  }
  function showTab(key) {
    $$('.tabs__btn').forEach(function (b) {
      var on = b.dataset.tab === key;
      b.classList.toggle('is-active', on);
      b.setAttribute('aria-selected', on);
    });
    $$('.tabpanel').forEach(function (p) { p.hidden = p.dataset.panel !== key; });
    if (key === 'chart') loadChart();
    // hàng bảng giá trong tab vừa mở đã nằm sẵn trong khung nhìn -> hiện ngay
    $$('.tabpanel:not([hidden]) .reveal').forEach(function (tr) {
      var r = tr.getBoundingClientRect();
      if (r.top < innerHeight && r.bottom > 0) tr.classList.add('is-in');
    });
  }
  $$('.tabs__btn').forEach(function (btn) { btn.addEventListener('click', function () { showTab(btn.dataset.tab); }); });

  /* ---------------- SMOOTH SCROLL LINKS ---------------- */
  $$('.js-scroll').forEach(function (el) {
    el.addEventListener('click', function (e) {
      e.preventDefault();
      var t = el.dataset.target || el.getAttribute('href');
      if (t.indexOf('/#') === 0) t = t.slice(1);
      goTo(t.indexOf('#') > 0 ? t.slice(t.indexOf('#')) : t);
    });
  });
  $$('.js-home').forEach(function (b) { b.addEventListener('click', function () { goTo('#top'); }); });

  /* ---------------- DANH MỤC: CAROUSEL MOBILE ---------------- */
  var car = { i: 0, timer: null, busy: false, n: $$('#pcarousel-slide [data-slide]').length };
  function carMark() {
    $$('.pcarousel__dot').forEach(function (d, k) { d.classList.toggle('is-on', k === car.i); });
    $$('.pcarousel__thumb').forEach(function (t, k) {
      t.classList.toggle('is-on', k === car.i);
      if (k === car.i && t.parentNode.scrollWidth > t.parentNode.clientWidth) {
        t.parentNode.scrollTo({ left: Math.max(0, t.offsetLeft - 8), behavior: 'smooth' });
      }
    });
  }
  function carGo(n, dir) {
    if (car.busy || n === car.i) return;
    car.busy = true;
    var slide = $('#pcarousel-slide');
    var rev = dir < 0;
    slide.className = 'pcarousel__slide ' + (rev ? 'is-exit-rev' : 'is-exit');
    setTimeout(function () {
      car.i = n;
      $$('[data-slide]', slide).forEach(function (a) { a.hidden = +a.dataset.slide !== n; });
      slide.className = 'pcarousel__slide ' + (rev ? 'is-pre-rev' : 'is-pre');
      reflow(slide);
      slide.className = 'pcarousel__slide is-enter';
      carMark();
      setTimeout(function () { car.busy = false; }, 300);
    }, 300);
  }
  function carAuto() {
    clearInterval(car.timer);
    car.timer = setInterval(function () {
      if (document.hidden || !$('#pcarousel').offsetParent) return; // desktop hoặc tab ẩn
      carGo((car.i + 1) % car.n, 1);
    }, 3500);
  }
  function initCarousel() {
    if (!car.n) return;
    $('#pcarousel').addEventListener('click', function (e) {
      var b = e.target.closest('[data-i]');
      if (!b) return;
      var n = +b.dataset.i;
      carGo(n, n > car.i ? 1 : -1);
      carAuto();
    });
    var vp = $('.pcarousel__viewport'), sx = 0, sy = 0;
    vp.addEventListener('touchstart', function (e) { sx = e.touches[0].clientX; sy = e.touches[0].clientY; }, { passive: true });
    vp.addEventListener('touchend', function (e) {
      var dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
      if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) {
        var L = car.n;
        if (dx < 0) carGo((car.i + 1) % L, 1); else carGo((car.i - 1 + L) % L, -1);
        carAuto();
      }
    });
    carAuto();
  }

  /* ---------------- DRAWER MENU ---------------- */
  var drawer = $('#drawer'), panel = $('#drawer-panel');
  var menuOpen = false;
  function openMenu() {
    if (menuOpen) return;
    menuOpen = true;
    drawer.hidden = false;
    drawer.classList.remove('is-closing');
    reflow(drawer);
    drawer.classList.add('is-open');
    lockScroll(true);
    $('#fabs').classList.add('is-hidden');
  }
  function closeMenu(after) {
    if (!menuOpen) { if (after) after(); return; }
    menuOpen = false;
    drawer.classList.add('is-closing');
    drawer.classList.remove('is-open');
    panel.style.transform = '';
    $('#drawer-overlay').style.opacity = '';
    setTimeout(function () {
      drawer.hidden = true;
      drawer.classList.remove('is-closing');
      lockScroll(false);
      if (!chatOpen) $('#fabs').classList.remove('is-hidden');
      if (after) after();
    }, 300);
  }
  $$('.js-open-menu').forEach(function (b) { b.addEventListener('click', openMenu); });
  $$('.js-close-menu').forEach(function (b) { b.addEventListener('click', function () { closeMenu(); }); });
  $('#drawer-overlay').addEventListener('click', function () { closeMenu(); });

  // Kéo panel sang trái để đóng
  (function () {
    var startX = 0, startY = 0, dx = 0, tracking = false, dragging = false, justDragged = false, w = 0, t0 = 0;
    panel.addEventListener('click', function (ev) { if (justDragged) { ev.stopPropagation(); ev.preventDefault(); } }, true);
    panel.addEventListener('pointerdown', function (e) {
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      tracking = true; dragging = false; dx = 0;
      startX = e.clientX; startY = e.clientY; w = panel.offsetWidth; t0 = Date.now();
    });
    window.addEventListener('pointermove', function (e) {
      if (!tracking) return;
      var mx = e.clientX - startX, my = e.clientY - startY;
      if (!dragging) {
        if (Math.abs(mx) > 8 && Math.abs(mx) > Math.abs(my)) {
          dragging = true;
          drawer.classList.add('is-dragging');
          try { panel.setPointerCapture(e.pointerId); } catch (err) {}
        } else if (Math.abs(my) > 8) { tracking = false; return; } else return;
      }
      dx = Math.min(0, mx);
      panel.style.transform = 'translateX(' + dx + 'px)';
      $('#drawer-overlay').style.opacity = String(1 + dx / w);
    });
    function end() {
      if (!tracking) return;
      tracking = false;
      if (!dragging) return;
      drawer.classList.remove('is-dragging');
      var v = dx / Math.max(1, Date.now() - t0);
      if (dx < -w * 0.3 || v < -0.5) closeMenu();
      else { panel.style.transform = ''; $('#drawer-overlay').style.opacity = ''; }
      // chặn đúng cú click phát sinh ngay sau thao tác kéo
      justDragged = true;
      setTimeout(function () { justDragged = false; }, 60);
      dragging = false;
    }
    window.addEventListener('pointerup', end);
    window.addEventListener('pointercancel', end);
  })();

  // Submenu accordion (height 0 <-> auto)
  function toggleSub(btn, sub) {
    var open = btn.getAttribute('aria-expanded') === 'true';
    btn.setAttribute('aria-expanded', String(!open));
    if (!open) {
      sub.hidden = false;
      var h = sub.scrollHeight;
      sub.style.height = '0px'; sub.style.opacity = '0';
      reflow(sub);
      sub.style.height = h + 'px'; sub.style.opacity = '1';
      sub.addEventListener('transitionend', function te(e) {
        if (e.propertyName !== 'height') return;
        sub.removeEventListener('transitionend', te);
        if (btn.getAttribute('aria-expanded') === 'true') sub.style.height = '';
      });
    } else {
      sub.style.height = sub.scrollHeight + 'px';
      reflow(sub);
      sub.style.height = '0px';
      sub.addEventListener('transitionend', function te(e) {
        if (e.propertyName !== 'height') return;
        sub.removeEventListener('transitionend', te);
        if (btn.getAttribute('aria-expanded') === 'false') { sub.hidden = true; sub.style.height = ''; sub.style.opacity = ''; }
      });
    }
  }
  $('#drawer-nav').addEventListener('click', function (e) {
    var t = e.target.closest('.js-sub, .js-sub3');
    if (t) {
      var sub = t.classList.contains('js-sub') ? t.nextElementSibling : t.parentNode.nextElementSibling;
      toggleSub(t, sub);
      return;
    }
  });
  $$('#drawer .js-nav-link').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      var href = a.getAttribute('href');
      if (isHome && href.indexOf('/#') === 0) href = href.slice(1);
      if (href === '/' && isHome) href = '#top';
      if (href.charAt(0) !== '#') { closeMenu(function () { location.href = href; }); return; }
      closeMenu(function () { goTo(href); });
    });
  });
  // Tìm kiếm trong menu
  var sBtn = $('#nav-search-btn'), sForm = $('#nav-search'), sInput = $('#nav-search-input');
  sBtn.addEventListener('click', function () { sBtn.hidden = true; sForm.hidden = false; sInput.focus(); });
  $('#nav-search-x').addEventListener('click', function () { sInput.value = ''; sForm.hidden = true; sBtn.hidden = false; });
  sForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var q = sInput.value.trim();
    if (!q) return;
    closeMenu(function () { navigateShop({ q: q }); });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (menuOpen) closeMenu();
    else if (chatOpen) setChat(false);
  });

  /* ---------------- LIVE CHAT ---------------- */
  var chat = $('#chat'), chatOpen = false;
  function setChat(on) {
    chatOpen = on;
    chat.classList.toggle('is-open', on);
    chat.setAttribute('aria-hidden', String(!on));
    chat.inert = !on; // panel đóng thì không nhận focus bàn phím
    $('#fabs').classList.toggle('is-hidden', on);
    $('#mbar').classList.toggle('is-hidden', on);
    if (on) setTimeout(function () { var f = chat.querySelector('input'); if (f) f.focus({ preventScroll: true }); }, 300);
  }
  $$('.js-open-chat').forEach(function (b) { b.addEventListener('click', function () { setChat(!chatOpen); }); });
  $$('.js-close-chat').forEach(function (b) { b.addEventListener('click', function () { setChat(false); }); });
  var cName = $('#chat-name'), cSubmit = $('.chat__submit');
  cName.addEventListener('input', function () { cSubmit.disabled = !cName.value.trim(); });
  $('#chat-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var name = cName.value.trim();
    if (!name) return;
    $$('#chat-body > :not(#chat-msgs)').forEach(function (n) { n.hidden = true; });
    $('#chat-hello').textContent = 'Xin chào ' + name + '! Nhân viên Hiệu Vàng Ngọc Diệp sẽ phản hồi trong giây lát.';
    if (chatProduct) {
      $('#chat-ask').textContent = 'Tôi muốn được tư vấn sản phẩm: ' + chatProduct.name + ' (' + chatProduct.id + ')';
      $('#chat-ask').hidden = false;
    }
    $('#chat-msgs').hidden = false;
    var compose = $('#chat-compose'), inp = $('input', compose);
    compose.hidden = false;
    inp.focus();
    compose.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var v = inp.value.trim();
      if (!v) return;
      var m = document.createElement('div');
      m.className = 'chat__msg chat__msg--me';
      m.textContent = v;
      $('#chat-msgs').appendChild(m);
      inp.value = '';
      $('#chat-body').scrollTop = $('#chat-body').scrollHeight;
    });
  });

  /* ---------------- MOBILE TOOLBAR ---------------- */
  var mWrap = $('#mbar-wrap'), mShow = $('#mbar-show');
  $('#mbar-hide').addEventListener('click', function () {
    mWrap.classList.add('is-out');
    setTimeout(function () {
      mWrap.hidden = true;
      mShow.hidden = false;
      mShow.classList.add('is-pre');
      reflow(mShow);
      mShow.classList.remove('is-pre');
    }, 200);
  });
  mShow.addEventListener('click', function () {
    mShow.classList.add('is-pre');
    setTimeout(function () {
      mShow.hidden = true;
      mWrap.hidden = false;
      reflow(mWrap);
      mWrap.classList.remove('is-out');
    }, 200);
  });

  /* ---------------- MENU NGANG DESKTOP ---------------- */
  function initTopnav() {
    var dds = $$('#topnav .dd');
    var hoverable = window.matchMedia('(hover: hover) and (pointer: fine)');
    function setOpen(dd, on) {
      dd.classList.toggle('is-open', on);
      dd.querySelector('.dd__trigger').setAttribute('aria-expanded', String(on));
    }
    function closeAll(except) { dds.forEach(function (d) { if (d !== except) setOpen(d, false); }); }

    dds.forEach(function (dd) {
      var trigger = dd.querySelector('.dd__trigger'), timer, closedByClick = false;
      function hoverOpen() {
        if (!hoverable.matches || closedByClick || dd.classList.contains('is-open')) return;
        clearTimeout(timer);
        timer = setTimeout(function () { closeAll(dd); setOpen(dd, true); }, 80);
      }
      trigger.addEventListener('click', function () {
        clearTimeout(timer);
        var on = !dd.classList.contains('is-open');
        closeAll(dd);
        setOpen(dd, on);
        closedByClick = !on; // người dùng chủ động đóng -> không tự mở lại khi còn rê chuột
      });
      dd.addEventListener('mouseenter', hoverOpen);
      // Sau khi chọn một mục, chuột có thể vẫn "ở trong" menu nên không có mouseenter mới -> mở lại khi rê trên nút
      trigger.addEventListener('pointermove', hoverOpen);
      dd.addEventListener('mouseleave', function () {
        closedByClick = false;
        if (!hoverable.matches) return;
        clearTimeout(timer);
        timer = setTimeout(function () { setOpen(dd, false); }, 260);
      });
      // Bấm một mục trong dropdown thì đóng lại
      dd.querySelector('.dd__panel').addEventListener('click', function (e) {
        if (e.target.closest('a, button')) setOpen(dd, false);
      });
      // Bàn phím: mũi tên xuống mở và focus mục đầu
      trigger.addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowDown') return;
        e.preventDefault();
        closeAll(dd); setOpen(dd, true);
        var first = dd.querySelector('.dd__panel a, .dd__panel button');
        if (first) first.focus();
      });
    });

    document.addEventListener('click', function (e) { if (!e.target.closest('#topnav .dd')) closeAll(); });
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      var open = dds.filter(function (d) { return d.classList.contains('is-open'); })[0];
      if (open) { setOpen(open, false); open.querySelector('.dd__trigger').focus(); }
    });

    // Ô tìm kiếm mở rộng
    var hs = $('#hsearch'), hin = $('#hsearch-input'), hbtn = $('#hsearch-btn');
    function openSearch() { hs.classList.add('is-open'); hin.tabIndex = 0; hin.focus({ preventScroll: true }); }
    function closeSearch() { hs.classList.remove('is-open'); hin.tabIndex = -1; hin.value = ''; }
    hbtn.addEventListener('click', function () {
      if (!hs.classList.contains('is-open')) return openSearch();
      if (hin.value.trim()) hs.requestSubmit(); else closeSearch();
    });
    hs.addEventListener('submit', function (e) {
      e.preventDefault();
      var q = hin.value.trim();
      if (!q) return;
      closeSearch();
      navigateShop({ q: q });
    });
    hin.addEventListener('keydown', function (e) { if (e.key === 'Escape') { e.stopPropagation(); closeSearch(); hbtn.focus(); } });
    hin.addEventListener('blur', function () { setTimeout(function () { if (!hin.value.trim() && document.activeElement !== hbtn) closeSearch(); }, 150); });

    // Đánh dấu mục đang xem khi cuộn
    var spyLinks = $$('#topnav [data-spy]');
    var sections = spyLinks.map(function (a) { return document.getElementById(a.dataset.spy); });
    var ticking = false;
    function spy() {
      ticking = false;
      var y = window.scrollY + 120, current = 'top';
      sections.forEach(function (s) { if (s && s.offsetTop <= y) current = s.id; });
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) current = 'lien-he';
      spyLinks.forEach(function (a) { a.classList.toggle('is-active', a.dataset.spy === current); });
    }
    window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(spy); } }, { passive: true });
    spy();
  }

  // Header nổi trên hero (trang Giới thiệu): trong suốt ở đầu trang, có nền khi cuộn
  function initOverlayHeader() {
    var h = $('#hdr-overlay');
    if (!h) return;
    var update = function () { h.classList.toggle('is-scrolled', window.scrollY > 10); };
    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  /* ---------------- SẢN PHẨM: xem nhanh ---------------- */
  function fold(str) { return String(str).normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase(); }
  // Thông tin sản phẩm đọc từ thẻ đã in sẵn trong HTML
  function productOf(card) {
    var d = card.dataset;
    return { id: d.id, name: d.name, cat: d.cat, catTitle: d.catTitle, catDesc: d.catDesc, sub: d.sub, gold: d.gold, weight: d.weight, price: +d.price || 0, desc: d.desc, img: $('img', card).getAttribute('src') };
  }

  var qv = $('#qv'), qvList = [], qvIndex = 0, qvReturn = null, chatProduct = null;
  function initQuickView() {
    if (!qv) return;
    qv.addEventListener('click', function (e) {
      if (e.target.closest('.js-qv-close')) return closeQuickView();
      var nav = e.target.closest('.qv__nav');
      if (nav) return stepQuickView(+nav.dataset.step);
      // "Tư vấn ngay" -> mở/thu bảng chọn kênh: Zalo / Gọi điện / Messenger fanpage
      if (e.target.closest('.js-qv-consult')) setChannels(!$('#qv-channels').hidden ? false : true);
    });
    document.addEventListener('click', function (e) {
      var b = e.target.closest('.js-qv');
      if (!b) return;
      var card = b.closest('.prod'), grid = b.closest('[data-grid]');
      var cards = grid ? $$('.prod', grid).filter(function (c) { return !c.hidden; }) : [card];
      openQuickView(cards.map(productOf), cards.indexOf(card));
    });
    document.addEventListener('keydown', function (e) {
      if (qv.hidden) return;
      if (e.key === 'Escape') { e.stopImmediatePropagation(); closeQuickView(); }
      else if (e.key === 'ArrowRight') stepQuickView(1);
      else if (e.key === 'ArrowLeft') stepQuickView(-1);
    }, true);
  }
  // Giá: có số → chỉ số tiền "1.800.000đ", không có → "Giá: Liên hệ" (ĐÚNG markup của price_html trong bake_static.py)
  function priceHtml(price) {
    if (price) return '<span class="price"><b class="price__num">' + price.toLocaleString('vi-VN') + '</b><span class="price__cur">đ</span></span>';
    return '<span class="price__lbl">Giá:</span><span class="price price--contact">Liên hệ</span>';
  }
  function fillQuickView(p) {
    $('#qv-img').src = p.img; $('#qv-img').alt = p.name;
    $('#qv-cat').textContent = p.catTitle; $('#qv-cat').href = shopUrl({ cat: p.cat });
    $('#qv-sub').textContent = p.sub; $('#qv-sub').href = shopUrl({ cat: p.cat, sub: p.sub });
    $('#qv-title').textContent = p.name;
    $('#qv-sku').textContent = p.catDesc;
    $('#qv-price').innerHTML = priceHtml(p.price) +
      (p.price ? '' : '<span class="qv__price-note">Giá thay đổi theo thời giá — gọi hoặc nhắn để được báo giá</span>');
    $('#qv-gold').textContent = p.gold || 'Liên hệ tư vấn';
    $('#qv-weight').textContent = p.weight || 'Liên hệ tư vấn';
    $('#qv-subname').textContent = p.sub;
    $('#qv-id').textContent = p.id;
    $('#qv-desc').textContent = p.desc;
    $('#qv-ch-id').textContent = p.id;
    setChannels(false);
    var many = qvList.length > 1;
    $$('.qv__nav', qv).forEach(function (n) { n.hidden = !many; });
  }
  // Messenger: máy tính mở hộp thư web với fanpage (href); điện thoại/máy tính bảng mở app qua m.me
  // (data-app-href) — m.me trên máy tính hay lỗi nên không dùng cho máy tính.
  document.addEventListener('click', function (e) {
    var a = e.target.closest('.js-messenger');
    if (!a || !a.dataset.appHref) return;
    if (/Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) || (navigator.maxTouchPoints > 1 && /Macintosh/.test(navigator.userAgent))) {
      a.href = a.dataset.appHref;
    }
  }, true);
  function setChannels(open) {
    var box = $('#qv-channels'), btn = $('.js-qv-consult', qv);
    if (!box) return;
    box.hidden = !open;
    if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) box.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }
  function openQuickView(list, index) {
    qvList = list;
    qvIndex = Math.max(0, index);
    fillQuickView(qvList[qvIndex]);
    qvReturn = document.activeElement;
    qv.hidden = false;
    reflow(qv);
    qv.classList.add('is-open');
    lockScroll(true);
    setTimeout(function () { $('.qv__panel', qv).focus({ preventScroll: true }); }, 30);
  }
  function stepQuickView(d) {
    if (qvList.length < 2) return;
    qvIndex = (qvIndex + d + qvList.length) % qvList.length;
    var media = $('.qv__media img', qv);
    media.classList.add('is-swap');
    setTimeout(function () { fillQuickView(qvList[qvIndex]); media.classList.remove('is-swap'); }, 160);
  }
  function closeQuickView() {
    if (!qv || qv.hidden) return;
    qv.classList.remove('is-open');
    setTimeout(function () {
      qv.hidden = true;
      lockScroll(false);
      if (qvReturn && qvReturn.focus && document.contains(qvReturn)) qvReturn.focus({ preventScroll: true });
    }, 220);
  }
  // Lọc lưới sản phẩm: ẩn/hiện thẻ có sẵn (kèm hiệu ứng chuyển)
  function showCards(grid, cards) {
    clearTimeout(grid._swap); // lần lọc mới huỷ lần chuyển cũ chưa xong -> luôn hiện kết quả mới nhất
    grid.classList.add('is-leaving');
    grid._swap = setTimeout(function () {
      $$('.prod', grid).forEach(function (c) { c.hidden = true; });
      cards.forEach(function (c, i) {
        c.style.animationDelay = Math.min(i, 12) * 45 + 'ms';
        grid.appendChild(c); // đúng thứ tự sắp xếp
        c.hidden = false;
      });
      grid.classList.remove('is-leaving');
    }, 160);
  }

  /* ---------------- TRANG CHỦ: SẢN PHẨM NỔI BẬT ---------------- */
  function initFeatured() {
    var chips = $('#feat-chips'), grid = $('#feat-grid');
    if (!chips || !grid) return;
    function show(cat) {
      var cards = $$('.prod', grid).filter(function (c) {
        return cat ? c.dataset.cat === cat && c.hasAttribute('data-top') : c.hasAttribute('data-pick');
      });
      showCards(grid, cards);
      $('#feat-more').href = shopUrl({ cat: cat });
    }
    chips.addEventListener('click', function (e) {
      var c = e.target.closest('.chip');
      if (!c || c.classList.contains('is-on')) return;
      $$('.chip', chips).forEach(function (x) { var on = x === c; x.classList.toggle('is-on', on); x.setAttribute('aria-pressed', on); });
      show(c.dataset.cat);
    });
  }

  /* ---------------- TRANG DANH SÁCH SẢN PHẨM ---------------- */
  function initShop() {
    var grid = $('#shop-grid');
    if (!grid) return;
    var cards = $$('.prod', grid);
    var catChips = $$('#shop-cats .chip'), subChips = $$('#shop-subs .chip');
    var catTitle = {};
    catChips.forEach(function (c) { catTitle[c.dataset.cat] = c.firstChild.textContent; });
    var hasSub = function (cat, sub) { return subChips.some(function (c) { return c.dataset.parent === cat && c.dataset.sub === sub; }); };
    var st = {};
    var qIn = $('#shop-q'), sortSel = $('#shop-sort');
    var defaults = { cat: '', sub: '', q: '', sort: 'featured' };
    function setState(p) {
      st = { cat: p.cat || '', sub: p.sub || '', q: p.q || '', sort: p.sort === 'new' ? 'new' : 'featured' };
      if (st.cat && !catTitle[st.cat]) st.cat = '';
      if (st.sub && (!st.cat || !hasSub(st.cat, st.sub))) st.sub = '';
      qIn.value = st.q; sortSel.value = st.sort;
    }
    function paramsOf(search) {
      var u = new URLSearchParams(search), o = {};
      ['cat', 'sub', 'q', 'gold', 'sort'].forEach(function (k) { o[k] = u.get(k) || ''; });
      return o;
    }
    setState(paramsOf(location.search));

    function matches(c, ignoreCat) {
      var d = c.dataset;
      if (!ignoreCat && st.cat && d.cat !== st.cat) return false;
      if (!ignoreCat && st.sub && d.sub !== st.sub) return false;
      if (st.q && fold(st.q).split(/\s+/).some(function (w) { return w && d.q.indexOf(w) < 0; })) return false;
      return true;
    }
    function sortCards(list) {
      var key = st.sort === 'new' ? 'data-new' : 'data-featured';
      return list.slice().sort(function (a, b) {
        return (b.hasAttribute(key) - a.hasAttribute(key)) || (a.dataset.idx - b.dataset.idx);
      });
    }
    function syncUrl(push) {
      var u = shopUrl({ cat: st.cat, sub: st.sub, q: st.q, sort: st.sort === 'featured' ? '' : st.sort });
      if (u === '/san-pham/' + location.search) return;
      if (push) history.pushState(null, '', u); else history.replaceState(null, '', u);
    }
    // Đánh dấu mục đang xem trong menu (mega + drawer)
    function markNav() {
      $$('#mega-products a, #nav-products a').forEach(function (a) {
        var p = paramsOf(a.getAttribute('href').split('?')[1] || '');
        var on = !st.q && p.cat === st.cat && p.sub === st.sub && !!st.cat;
        a.classList.toggle('is-current', on);
        if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
      });
    }
    function render(push) {
      // chip danh mục (số lượng theo từ khoá tìm)
      var base = cards.filter(function (c) { return matches(c, true); });
      catChips.forEach(function (c) {
        var on = st.cat === c.dataset.cat;
        c.classList.toggle('is-on', on); c.setAttribute('aria-pressed', on);
        $('.chip__n', c).textContent = base.filter(function (p) { return !c.dataset.cat || p.dataset.cat === c.dataset.cat; }).length;
      });
      // chip danh mục con
      $('#shop-subs').hidden = !st.cat;
      subChips.forEach(function (c) {
        var all = !c.dataset.parent;
        c.hidden = !all && (c.dataset.parent !== st.cat || !base.some(function (p) { return p.dataset.cat === st.cat && p.dataset.sub === c.dataset.sub; }));
        c.classList.toggle('is-on', st.sub === c.dataset.sub);
      });
      // tiêu đề
      var title = st.sub || (st.cat ? catTitle[st.cat] : 'Tất cả sản phẩm');
      var t = $('#shop-title');
      if (st.q) {
        t.textContent = 'Kết quả cho “';
        var q = document.createElement('span'); q.className = 'gold-text'; q.textContent = st.q;
        t.appendChild(q); t.appendChild(document.createTextNode('”'));
      } else t.textContent = title;
      $('#shop-crumb-cur').textContent = st.cat ? catTitle[st.cat] : 'Sản phẩm';
      document.title = (st.q ? 'Tìm “' + st.q + '”' : title) + ' | Hiệu Vàng Ngọc Diệp';
      // lưới
      var items = sortCards(cards.filter(function (c) { return matches(c); }));
      $('#shop-count').textContent = items.length + ' sản phẩm';
      $('#shop-empty').hidden = items.length > 0;
      showCards(grid, items);
      syncUrl(push);
      markNav();
    }
    $('#shop-cats').addEventListener('click', function (e) {
      var c = e.target.closest('.chip'); if (!c) return;
      st.cat = c.dataset.cat; st.sub = ''; render(true);
    });
    $('#shop-subs').addEventListener('click', function (e) {
      var c = e.target.closest('.chip'); if (!c) return;
      st.sub = c.dataset.sub; render(true);
    });
    var t;
    qIn.addEventListener('input', function () { clearTimeout(t); t = setTimeout(function () { st.q = qIn.value.trim(); render(); }, 220); });
    $('#shop-search').addEventListener('submit', function (e) { e.preventDefault(); clearTimeout(t); st.q = qIn.value.trim(); render(); });
    sortSel.addEventListener('change', function () { st.sort = sortSel.value; render(); });
    $$('.js-shop-reset').forEach(function (b) { b.addEventListener('click', function () {
      st = { cat: '', sub: '', q: '', sort: 'featured' };
      qIn.value = ''; sortSel.value = 'featured'; render(true);
    }); });

    // Điều hướng tới trang sản phẩm khi đang ở chính trang này: lọc tại chỗ, không tải lại trang
    shopApply = function (p, push) {
      setState(p);
      render(push);
      var top = $('.shop-hero').getBoundingClientRect().top + window.scrollY;
      if (window.scrollY > top + 40) window.scrollTo({ top: top, behavior: 'smooth' });
    };
    document.addEventListener('click', function (e) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var a = e.target.closest('a[href]');
      if (!a || a.target === '_blank') return;
      var url = new URL(a.getAttribute('href'), location.href);
      if (url.origin !== location.origin || !/^\/san-pham\/?$/.test(url.pathname)) return;
      e.preventDefault();
      var p = paramsOf(url.search);
      if (menuOpen) closeMenu(function () { shopApply(p, true); });
      else shopApply(p, true);
    });
    window.addEventListener('popstate', function () { setState(paramsOf(location.search)); render(false); });
    // HTML đã in sẵn danh sách mặc định; chỉ lọc lại khi URL có bộ lọc (?cat=, ?q=...)
    if (Object.keys(defaults).some(function (k) { return st[k] !== defaults[k]; })) render(false);
    else markNav();
  }

  /* ---------------- TIN TỨC ---------------- */
  function initNews() {
    var chips = $('#news-chips');
    if (chips) chips.addEventListener('click', function (e) {
      var c = e.target.closest('.chip');
      if (!c) return;
      $$('.chip', chips).forEach(function (x) { var on = x === c; x.classList.toggle('is-on', on); x.setAttribute('aria-pressed', on); });
      var n = 0;
      $$('#news-list > article').forEach(function (a) {
        var show = !c.dataset.cat || a.dataset.cat === c.dataset.cat;
        a.hidden = !show; if (show) n++;
      });
      $('#news-list').classList.toggle('is-filtered', !!c.dataset.cat);
      $('#news-empty').hidden = n > 0;
    });
    $$('.js-share-fb').forEach(function (a) { a.href = 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(location.href.split('#')[0]); });
    $$('.js-copy-link').forEach(function (b) {
      b.addEventListener('click', function () {
        var url = location.href.split('#')[0];
        var done = function () { toast('Đã sao chép liên kết', url); };
        if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, done); else done();
      });
    });
  }

  /* ---------------- FORM LIÊN HỆ → trang quản trị (GAS.md mục V) ---------------- */
  // URL /exec của trang quản trị — điền sau khi deploy CMS lần đầu (gas/README.md). Deploy lại bằng
  // "New version" thì URL không đổi. Để trống thì form báo lỗi, KHÔNG giả vờ gửi thành công.
  var GAS_EXEC_URL = 'https://script.google.com/macros/s/AKfycbyRqZKiIw-jAzQ7EE4WIm5nR4oA-rYUajNv4M_7-CyCuZFQx8W1RO4F8l8MnPjho90x9Q/exec';
  function initContactForm() {
    var form = $('#contact-form');
    if (!form) return;
    var err = $('#cf-err');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = $('#cf-name').value.trim(), phone = $('#cf-phone').value.replace(/[\s.]/g, '');
      var msg = !name ? 'Vui lòng nhập họ và tên.' : !/^(\+?84|0)\d{9,10}$/.test(phone) ? 'Số điện thoại chưa đúng, vui lòng kiểm tra lại.' : '';
      err.textContent = msg; err.hidden = !msg;
      if (msg) { (name ? $('#cf-phone') : $('#cf-name')).focus(); return; }
      var btn = $('.cform__submit', form);
      var fail = function (m) {
        var hl = $('[data-contact="hotline"]');
        err.textContent = m || 'Chưa gửi được yêu cầu. Quý khách vui lòng gọi hotline' + (hl ? ' ' + hl.textContent : '') + ' giúp em nhé.';
        err.hidden = false;
      };
      if (!GAS_EXEC_URL) { fail(); return; }
      btn.disabled = true; btn.classList.add('is-loading');
      // text/plain để trình duyệt không gửi preflight OPTIONS (máy chủ form không xử lý được)
      fetch(GAS_EXEC_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify({
          formType: 'contact', _hp: $('#cf-hp').value,
          name: name, phone: $('#cf-phone').value.trim(), need: $('#cf-need').value, message: $('#cf-msg').value.trim()
        })
      }).then(function (r) { return r.json(); }).then(function (res) {
        if (!res.ok) { fail(res.error); return; }
        $('#cf-done-name').textContent = name;
        $('#cf-done-phone').textContent = $('#cf-phone').value.trim();
        form.hidden = true; $('#contact-done').hidden = false;
        form.reset();
      }).catch(function () { fail(); }).then(function () {
        btn.disabled = false; btn.classList.remove('is-loading');
      });
    });
    $('#cf-again').addEventListener('click', function () { $('#contact-done').hidden = true; form.hidden = false; $('#cf-name').focus(); });
  }

  /* ---------------- INIT ---------------- */
  initQuickView();
  if ($('#ptable-d') || $('#stable-d')) {
    initCalc();
    loadPrices();
  }
  initCarousel();
  // Mở trang kèm #mục (vd /bang-gia/#gia-bac) -> cuộn tới mục đó
  if (location.hash.length > 1 && $(location.hash)) setTimeout(function () { smoothTo(location.hash); }, 80);
  initTopnav();
  initOverlayHeader();
  initFeatured();
  initShop();
  initNews();
  initContactForm();
})();
