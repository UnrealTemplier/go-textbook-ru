/* =====================================================================
   Увеличение изображений по клику ([media] lightbox = true). Файл копируется в dist/
   и подключается только на страницах с img.md-zoom; разметку окна (#md-lightbox)
   выводит шаблон страницы. Vanilla JS, работает по file://.
   Клик или Enter — открыть; Esc, клик по фону, × — закрыть; ← → — листать картинки
   страницы; «1:1» — натуральный размер с прокруткой вместо вписывания в окно.
   ===================================================================== */
(function () {
  'use strict';

  const modal = document.getElementById('md-lightbox');
  if (!modal) return;
  const body = document.getElementById('md-lightbox-body');
  const view = document.getElementById('md-lightbox-img');
  const caption = document.getElementById('md-lightbox-caption');
  const counter = document.getElementById('md-lightbox-counter');
  const closeBtn = modal.querySelector('[data-action="lightbox-close"].btn-modal-close');
  const navButtons = modal.querySelectorAll('[data-action="lightbox-prev"], [data-action="lightbox-next"]');

  let items = [];
  let index = -1;
  let natural = false;
  let opener = null;

  // Картинки, которые открываются в окне: внутри ссылки клик ведёт по ссылке
  function zoomable() {
    return Array.from(document.querySelectorAll('.article-markdown img.md-zoom'))
      .filter(function (el) { return !el.closest('a'); });
  }

  function naturalSize() {
    const w = view.naturalWidth || parseFloat(view.getAttribute('width')) || 0;
    const h = view.naturalHeight || parseFloat(view.getAttribute('height')) || 0;
    return [w, h];
  }

  // Вписать целиком (маленькие картинки растягиваются, большие уменьшаются) или 1:1
  function layout() {
    const size = naturalSize();
    if (!size[0] || !size[1]) return;
    let scale = 1;
    if (!natural) {
      const cs = getComputedStyle(body);
      const availW = body.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      const availH = body.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
      scale = Math.min(availW / size[0], availH / size[1]);
    }
    view.style.width = (size[0] * scale) + 'px';
    view.style.height = (size[1] * scale) + 'px';
    body.style.cursor = natural ? 'zoom-out' : 'zoom-in';
  }

  function show(i) {
    index = (i + items.length) % items.length;
    const src = items[index];
    const fig = src.closest('figure.md-figure');
    const cap = fig ? fig.querySelector('figcaption') : null;
    natural = false;
    view.style.width = '';
    view.style.height = '';
    ['width', 'height'].forEach(function (a) {
      if (src.hasAttribute(a)) view.setAttribute(a, src.getAttribute(a)); else view.removeAttribute(a);
    });
    view.alt = src.alt;
    view.onload = layout;
    view.src = src.currentSrc || src.src;
    if (cap) caption.innerHTML = cap.innerHTML; else caption.textContent = src.title || '';
    caption.hidden = !caption.textContent.trim();
    counter.textContent = items.length > 1 ? (index + 1) + ' / ' + items.length : '';
    navButtons.forEach(function (b) { b.hidden = items.length < 2; });
    layout();
  }

  function open(el) {
    items = zoomable();
    if (items.indexOf(el) === -1) return;
    opener = el;
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    show(items.indexOf(el));       // после показа окна: до этого у области нулевой размер
    if (closeBtn) closeBtn.focus();
  }

  function close() {
    if (!modal.classList.contains('active')) return;
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    view.onload = null;
    if (opener) opener.focus();
    opener = null;
  }

  function toggleNatural() {
    natural = !natural;
    layout();
  }

  zoomable().forEach(function (el) {
    el.setAttribute('tabindex', '0');
    el.setAttribute('aria-haspopup', 'dialog');
  });

  document.addEventListener('click', function (e) {
    const action = e.target.closest('#md-lightbox [data-action]');
    if (action) {
      const name = action.getAttribute('data-action');
      if (name === 'lightbox-close') close();
      else if (name === 'lightbox-prev') show(index - 1);
      else if (name === 'lightbox-next') show(index + 1);
      else if (name === 'lightbox-fit') toggleNatural();
      return;
    }
    if (modal.classList.contains('active')) {
      if (e.target === body) close();                 // пустое место вокруг картинки — тоже фон
      else if (e.target === view) toggleNatural();
      return;
    }
    const img = e.target.closest('.article-markdown img.md-zoom');
    if (img && !img.closest('a')) open(img);
  });

  document.addEventListener('keydown', function (e) {
    if (!modal.classList.contains('active')) {
      const img = e.target.closest && e.target.closest('.article-markdown img.md-zoom');
      if (img && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        open(img);
      }
      return;
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      close();
    } else if (e.key === 'ArrowLeft' && items.length > 1) {
      e.preventDefault();
      show(index - 1);
    } else if (e.key === 'ArrowRight' && items.length > 1) {
      e.preventDefault();
      show(index + 1);
    } else if (e.key === 'Tab') {
      // Фокус не уходит из окна
      const focusables = Array.from(modal.querySelectorAll('button, a[href], [tabindex="0"]'))
        .filter(function (el) { return !el.hidden && el.offsetParent !== null; });
      if (!focusables.length) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      } else if (!modal.contains(document.activeElement)) {
        e.preventDefault();
        first.focus();
      }
    }
  });

  window.addEventListener('resize', function () {
    if (modal.classList.contains('active')) layout();
  });

  // Отладка и тесты: window.__mediaLightbox.open(img), .close()
  window.__mediaLightbox = { open: open, close: close, show: function (i) { show(i); } };
})();
