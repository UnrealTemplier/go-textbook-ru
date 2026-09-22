/**
 * Go Backend Encyclopedia — Interactive Client Scripts
 * Brian Kernighan Style: Simple, robust, zero-dependency, works on file:///
 */

(function () {
  'use strict';

  // -------------------------------------------------------------------------
  // 1. Инициализация Mermaid.js
  // -------------------------------------------------------------------------
  function saveMermaidSources() {
    document.querySelectorAll('pre.mermaid').forEach(function (el) {
      if (!el.hasAttribute('data-mermaid-source') && !el.hasAttribute('data-processed') && !el.querySelector('svg')) {
        el.setAttribute('data-mermaid-source', el.textContent);
      }
    });
  }

  function initMermaid() {
    if (typeof mermaid !== 'undefined') {
      try {
        var cs = getComputedStyle(document.documentElement);
        var currentTheme = document.documentElement.dataset.theme || 'paper';
        var isDark = currentTheme === 'dark';
        var isPaper = currentTheme === 'paper';
        var defaultBg = isDark ? '#0e0d0b' : (isPaper ? '#eae1cb' : '#f2f4f7');
        var defaultCard = isDark ? '#201d19' : (isPaper ? '#fbf7ec' : '#ffffff');
        var defaultAccent = isDark ? '#d89b32' : (isPaper ? '#b45309' : '#1e5a96');
        var defaultText = isDark ? '#ded8cc' : (isPaper ? '#26211a' : '#101828');
        var defaultTextSec = isDark ? '#b8b0a2' : (isPaper ? '#3b342a' : '#242c38');
        var defaultBorder = isDark ? '#4d4338' : (isPaper ? '#b2a184' : '#98a2b3');
        var defaultLink = isDark ? '#e06b2d' : (isPaper ? '#8c3b12' : '#18528c');
        var defaultSurface = isDark ? '#181613' : (isPaper ? '#eae0c8' : '#eef0f3');

        var mermaidBg = cs.getPropertyValue('--mermaid-bg').trim() || defaultBg;
        var bgCard = cs.getPropertyValue('--bg-card').trim() || defaultCard;
        var accent = cs.getPropertyValue('--accent').trim() || defaultAccent;
        var textColor = cs.getPropertyValue('--text').trim() || defaultText;
        var textSecondary = cs.getPropertyValue('--text-secondary').trim() || defaultTextSec;
        var borderStrong = cs.getPropertyValue('--border-strong').trim() || defaultBorder;
        var link = cs.getPropertyValue('--link').trim() || defaultLink;
        var bgSurface = cs.getPropertyValue('--bg-surface').trim() || defaultSurface;

        mermaid.initialize({
          startOnLoad: true,
          theme: isDark ? 'dark' : 'base',
          securityLevel: 'loose',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          themeVariables: {
            darkMode: isDark,
            background: mermaidBg,
            primaryColor: accent,
            primaryTextColor: textColor,
            primaryBorderColor: borderStrong,
            lineColor: borderStrong,
            secondaryColor: bgSurface,
            tertiaryColor: bgSurface,
            noteBkgColor: bgCard,
            noteTextColor: textSecondary,
            noteBorderColor: borderStrong
          }
        });
      } catch (err) {
        console.warn('Mermaid initialization warning:', err);
      }
    }
  }

  // -------------------------------------------------------------------------
  // Вспомогательные функции центрирования и плавной прокрутки сайдбара
  // -------------------------------------------------------------------------
  function smoothScroll(container, targetScrollTop, duration = 480) {
    if (!container) return;

    const startScrollTop = container.scrollTop;
    const maxScroll = Math.max(0, container.scrollHeight - container.clientHeight);
    const clampedTarget = Math.max(0, Math.min(maxScroll, Math.round(targetScrollTop)));
    const distance = clampedTarget - startScrollTop;

    if (Math.abs(distance) < 2 || duration <= 0) {
      container.scrollTop = clampedTarget;
      return;
    }

    if (container._scrollAnimId) {
      cancelAnimationFrame(container._scrollAnimId);
      container._scrollAnimId = null;
    }

    const startTime = performance.now();

    // easeOutQuart: мягкое, размеренное и плавное замедление
    function easeOutQuart(t) {
      return 1 - Math.pow(1 - t, 4);
    }

    function step(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(1, elapsed / duration);
      const ease = easeOutQuart(progress);

      container.scrollTop = Math.round(startScrollTop + distance * ease);

      if (progress < 1) {
        container._scrollAnimId = requestAnimationFrame(step);
      } else {
        container.scrollTop = clampedTarget;
        container._scrollAnimId = null;
      }
    }

    container._scrollAnimId = requestAnimationFrame(step);
  }

  function centerElementInContainer(container, element, smooth = false) {
    if (!container || !element) return;

    const containerRect = container.getBoundingClientRect();
    const elementRect = element.getBoundingClientRect();

    if (containerRect.height === 0 || elementRect.height === 0) return;

    const currentScrollTop = container.scrollTop;
    const elementTopInContent = (elementRect.top - containerRect.top) + currentScrollTop;
    const targetScrollTop = elementTopInContent + (elementRect.height / 2) - (container.clientHeight / 2);

    if (smooth) {
      smoothScroll(container, targetScrollTop, 480);
    } else {
      const maxScroll = Math.max(0, container.scrollHeight - container.clientHeight);
      container.scrollTop = Math.max(0, Math.min(maxScroll, Math.round(targetScrollTop)));
    }
  }

  function centerActiveLecture(smooth = false) {
    const container = document.getElementById('sidebar-content');
    if (!container) return;

    const activeItem = container.querySelector('.nav-item.active');
    if (activeItem) {
      let parentDetails = activeItem.closest('details');
      while (parentDetails) {
        if (!parentDetails.hasAttribute('open')) {
          parentDetails.setAttribute('open', '');
        }
        parentDetails = parentDetails.parentElement ? parentDetails.parentElement.closest('details') : null;
      }
      centerElementInContainer(container, activeItem, smooth);
    }
  }

  // -------------------------------------------------------------------------
  // 2. Управление шириной сайдбара (drag-to-resize)
  // -------------------------------------------------------------------------
  function initSidebarResize() {
    const sidebar = document.getElementById('app-sidebar');
    const resizer = document.getElementById('drag-resizer');
    if (!sidebar || !resizer) return;

    const STORAGE_KEY = 'go_encyclopedia_sidebar_width';
    const savedWidth = localStorage.getItem(STORAGE_KEY);
    if (savedWidth) {
      const widthNum = parseInt(savedWidth, 10);
      if (widthNum >= 220 && widthNum <= 550) {
        sidebar.style.width = widthNum + 'px';
      }
    }

    let isResizing = false;

    resizer.addEventListener('mousedown', function (e) {
      isResizing = true;
      resizer.classList.add('resizing');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', function (e) {
      if (!isResizing) return;
      const newWidth = e.clientX;
      if (newWidth >= 220 && newWidth <= 550) {
        sidebar.style.width = newWidth + 'px';
      }
    });

    document.addEventListener('mouseup', function () {
      if (isResizing) {
        isResizing = false;
        resizer.classList.remove('resizing');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        localStorage.setItem(STORAGE_KEY, parseInt(sidebar.style.width, 10));
        centerActiveLecture(false);
      }
    });
  }

  // -------------------------------------------------------------------------
  // 3. Мгновенная фильтрация лекций в сайдбаре
  // -------------------------------------------------------------------------
  function initSidebarFilter() {
    const filterInput = document.getElementById('sidebar-filter');
    const clearBtn = document.getElementById('clear-filter');
    const sidebarContent = document.getElementById('sidebar-content');
    if (!filterInput || !sidebarContent) return;

    const navItems = sidebarContent.querySelectorAll('.nav-item');
    const modules = sidebarContent.querySelectorAll('.nav-module');
    const submodules = sidebarContent.querySelectorAll('.nav-submodule');

    filterInput.addEventListener('input', function () {
      const query = filterInput.value.trim().toLowerCase();

      if (clearBtn) {
        clearBtn.style.display = query ? 'block' : 'none';
      }

      if (!query) {
        navItems.forEach(item => item.style.display = '');
        modules.forEach(mod => {
          mod.style.display = '';
          // Восстанавливаем только активный
          if (!mod.classList.contains('active-module')) {
            mod.removeAttribute('open');
          }
        });
        submodules.forEach(sub => {
          sub.style.display = '';
          if (!sub.classList.contains('active-submodule')) {
            sub.removeAttribute('open');
          } else {
            sub.setAttribute('open', '');
          }
        });
        setTimeout(function () {
          centerActiveLecture(true);
        }, 30);
        return;
      }

      // Если есть поисковый запрос:
      modules.forEach(mod => {
        let modHasMatches = false;
        const modItems = mod.querySelectorAll('.nav-item');

        modItems.forEach(item => {
          const text = item.textContent.toLowerCase();
          if (text.includes(query)) {
            item.style.display = '';
            modHasMatches = true;
          } else {
            item.style.display = 'none';
          }
        });

        // Проверяем подмодули
        const modSubs = mod.querySelectorAll('.nav-submodule');
        modSubs.forEach(sub => {
          let subHasMatches = false;
          const subItems = sub.querySelectorAll('.nav-item');
          subItems.forEach(si => {
            if (si.textContent.toLowerCase().includes(query)) {
              subHasMatches = true;
            }
          });
          if (subHasMatches) {
            sub.style.display = '';
            sub.setAttribute('open', '');
          } else {
            sub.style.display = 'none';
          }
        });

        if (modHasMatches) {
          mod.style.display = '';
          mod.setAttribute('open', '');
        } else {
          mod.style.display = 'none';
        }
      });
    });

    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        filterInput.value = '';
        filterInput.dispatchEvent(new Event('input'));
        filterInput.focus();
      });
    }
  }

  // -------------------------------------------------------------------------
  // 4. Копирование кода в 1 клик
  // -------------------------------------------------------------------------
  window.copyCodeBlock = function (btn) {
    const codeWrapper = btn.closest('.code-block');
    if (!codeWrapper) return;
    const codeEl = codeWrapper.querySelector('code');
    if (!codeEl) return;

    const textToCopy = codeEl.innerText || codeEl.textContent;

    navigator.clipboard.writeText(textToCopy).then(() => {
      const successColor = getComputedStyle(document.documentElement).getPropertyValue('--success').trim() || '#10b981';
      const originalHTML = btn.innerHTML;
      btn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${successColor}" stroke-width="2" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg>
        <span style="color:${successColor}; font-weight:600;">Скопировано!</span>
      `;
      btn.style.borderColor = successColor;

      setTimeout(() => {
        btn.innerHTML = originalHTML;
        btn.style.borderColor = '';
      }, 2000);
    }).catch(err => {
      console.error('Copy failed:', err);
    });
  };

  // -------------------------------------------------------------------------
  // 4.1. Делегирование событий пользовательского интерфейса (data-action)
  // -------------------------------------------------------------------------
  function initActionDelegation() {
    document.addEventListener('click', function (e) {
      const actionEl = e.target.closest('[data-action]');
      if (!actionEl) return;

      const action = actionEl.getAttribute('data-action');
      if (action === 'copy-code') {
        window.copyCodeBlock(actionEl);
      } else if (action === 'mermaid-fullscreen') {
        window.toggleMermaidModal(actionEl);
      } else if (action === 'close-mermaid-modal') {
        window.closeMermaidModal();
      } else if (action === 'zoom-mermaid-in') {
        window.zoomMermaid(0.2);
      } else if (action === 'zoom-mermaid-out') {
        window.zoomMermaid(-0.2);
      } else if (action === 'zoom-mermaid-reset') {
        window.resetMermaidZoom();
      }
    });
  }

  // -------------------------------------------------------------------------
  // 5. Полноэкранный модальный просмотр диаграмм Mermaid и зумирование
  // -------------------------------------------------------------------------
  let currentMermaidZoom = 1.0;

  window.toggleMermaidModal = function (btn) {
    const wrapper = btn.closest('.mermaid-wrapper');
    if (!wrapper) return;
    const svgEl = wrapper.querySelector('.mermaid svg');
    if (!svgEl) return;

    const modal = document.getElementById('mermaid-modal');
    const container = document.getElementById('mermaid-modal-content');
    if (!modal || !container) return;

    container.innerHTML = '';
    const clonedSvg = svgEl.cloneNode(true);
    container.appendChild(clonedSvg);

    currentMermaidZoom = 1.0;
    clonedSvg.style.transform = `scale(${currentMermaidZoom})`;

    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  };

  window.closeMermaidModal = function () {
    const modal = document.getElementById('mermaid-modal');
    if (!modal) return;
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  };

  window.zoomMermaid = function (delta) {
    const container = document.getElementById('mermaid-modal-content');
    if (!container) return;
    const svg = container.querySelector('svg');
    if (!svg) return;

    currentMermaidZoom = Math.max(0.3, Math.min(3.5, currentMermaidZoom + delta));
    svg.style.transform = `scale(${currentMermaidZoom})`;
  };

  window.resetMermaidZoom = function () {
    const container = document.getElementById('mermaid-modal-content');
    if (!container) return;
    const svg = container.querySelector('svg');
    if (!svg) return;

    currentMermaidZoom = 1.0;
    svg.style.transform = `scale(1.0)`;
  };

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      window.closeMermaidModal();
    }
  });

  // Зум колесиком мыши в модалке
  const modalBody = document.getElementById('mermaid-modal-content');
  if (modalBody) {
    modalBody.addEventListener('wheel', function (e) {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.15 : -0.15;
      window.zoomMermaid(delta);
    }, { passive: false });
  }

  // -------------------------------------------------------------------------
  // 6. Индикатор чтения и кнопка "Наверх"
  // -------------------------------------------------------------------------
  function initScrollProgress() {
    const progressEl = document.getElementById('reading-progress');
    const btnScrollTop = document.getElementById('btn-scroll-top');

    window.addEventListener('scroll', function () {
      const scrollTop = window.scrollY || document.documentElement.scrollTop;
      const docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;

      if (progressEl && docHeight > 0) {
        const percent = Math.min(100, Math.max(0, (scrollTop / docHeight) * 100));
        progressEl.style.width = percent + '%';
        progressEl.setAttribute('aria-valuenow', Math.round(percent));
      }

      if (btnScrollTop) {
        if (scrollTop > 350) {
          btnScrollTop.classList.add('visible');
        } else {
          btnScrollTop.classList.remove('visible');
        }
      }
    });

    if (btnScrollTop) {
      btnScrollTop.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }
  }

  // -------------------------------------------------------------------------
  // 7. Мобильное меню сайдбара
  // -------------------------------------------------------------------------
  function initMobileMenu() {
    const toggleBtn = document.getElementById('toggle-sidebar');
    const sidebar = document.getElementById('app-sidebar');
    if (!toggleBtn || !sidebar) return;

    toggleBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      const isOpen = sidebar.classList.toggle('open');
      toggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      if (isOpen) {
        setTimeout(function () {
          centerActiveLecture(false);
        }, 150);
      }
    });

    document.addEventListener('click', function (e) {
      if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
        if (!sidebar.contains(e.target) && e.target !== toggleBtn) {
          sidebar.classList.remove('open');
          toggleBtn.setAttribute('aria-expanded', 'false');
        }
      }
    });
  }

  // -------------------------------------------------------------------------
  // 8. Живой полнотекстовый поиск на главной странице (index.html)
  // -------------------------------------------------------------------------
  function initGlobalSearch() {
    const searchInput = document.getElementById('global-search-input');
    const dropdown = document.getElementById('global-search-results');
    if (!searchInput || !dropdown) return;

    // Данные подгружаются из window.SEARCH_DATA (search-data.js)
    searchInput.addEventListener('input', function () {
      const q = searchInput.value.trim().toLowerCase();
      if (!q || !window.SEARCH_DATA) {
        dropdown.classList.remove('active');
        dropdown.innerHTML = '';
        return;
      }

      const words = q.split(/\s+/);
      const matches = [];

      for (let i = 0; i < window.SEARCH_DATA.length; i++) {
        const item = window.SEARCH_DATA[i];
        const titleLower = item.title.toLowerCase();
        const modLower = item.module.toLowerCase();
        
        let score = 0;
        let matchedAll = true;

        for (let w = 0; w < words.length; w++) {
          const word = words[w];
          if (titleLower.includes(word)) {
            score += 10;
          } else if (modLower.includes(word)) {
            score += 3;
          } else {
            matchedAll = false;
            break;
          }
        }

        if (matchedAll) {
          matches.push({ item, score });
        }
      }

      matches.sort((a, b) => b.score - a.score);

      if (matches.length === 0) {
        dropdown.innerHTML = '<div style="padding:16px; color:inherit; opacity:0.6; font-size:0.9rem;">Ничего не найдено. Попробуйте другой запрос (например: GC, Raft, epoll, каналы).</div>';
        dropdown.classList.add('active');
        return;
      }

      const topResults = matches.slice(0, 15);
      let resHTML = '';

      topResults.forEach(({ item }) => {
        resHTML += `
          <a href="${item.url}" class="search-result-item" role="option">
            <div class="search-res-title">${escapeHtml(item.title)}</div>
            <div class="search-res-module">${escapeHtml(item.module)} ${item.sub ? '• ' + escapeHtml(item.sub) : ''}</div>
          </a>
        `;
      });

      dropdown.innerHTML = resHTML;
      dropdown.classList.add('active');
    });

    document.addEventListener('click', function (e) {
      if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('active');
      }
    });
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // -------------------------------------------------------------------------
  // 9. Автоцентрирование сайдбара и плавная размеренная анимация аккордеона
  // -------------------------------------------------------------------------
  function initSidebarCentering() {
    const container = document.getElementById('sidebar-content');
    if (!container) return;

    // Отмена анимации программного скролла при ручной прокрутке колесиком или тачем
    container.addEventListener('wheel', function () {
      if (container._scrollAnimId) {
        cancelAnimationFrame(container._scrollAnimId);
        container._scrollAnimId = null;
      }
    }, { passive: true });
    container.addEventListener('touchmove', function () {
      if (container._scrollAnimId) {
        cancelAnimationFrame(container._scrollAnimId);
        container._scrollAnimId = null;
      }
    }, { passive: true });

    let userHasScrolled = false;
    container.addEventListener('wheel', function () {
      userHasScrolled = true;
    }, { passive: true, once: true });
    container.addEventListener('touchmove', function () {
      userHasScrolled = true;
    }, { passive: true, once: true });

    // 1. Всегда центрируем сайдбар на текущей выбранной лекции при открытии страницы
    centerActiveLecture(false);

    requestAnimationFrame(function () {
      if (!userHasScrolled) {
        centerActiveLecture(false);
      }
    });

    setTimeout(function () {
      if (!userHasScrolled) {
        centerActiveLecture(false);
      }
    }, 120);

    window.addEventListener('pageshow', function () {
      centerActiveLecture(false);
    });

    // 2. Плавная и более медленная анимация аккордеона (сворачивание/разворачивание)
    const ANIMATION_DURATION = 480; // комфортная, плавная длительность (0.48с)
    const EASING = 'cubic-bezier(0.22, 1, 0.36, 1)';

    container.addEventListener('click', function (e) {
      const summary = e.target.closest('.nav-module-title, .nav-submodule-title');
      if (!summary) return;

      const details = summary.closest('details');
      if (!details) return;

      const content = details.querySelector('.nav-module-content') || details.querySelector('.sub-list') || details.children[1];
      if (!content) return;

      e.preventDefault();
      e.stopPropagation();

      const isOpen = details.hasAttribute('open') && !details.classList.contains('closing');

      // Прерываем предыдущую анимацию этого блока, если пользователь кликает повторно
      if (content._anim) {
        content._anim.cancel();
        content._anim = null;
      }

      if (isOpen) {
        // --- СВОРАЧИВАНИЕ МОДУЛЯ ---
        const startHeight = content.offsetHeight;
        if (startHeight <= 0) {
          details.removeAttribute('open');
          details.classList.remove('closing');
          return;
        }

        // Помечаем блок как закрывающийся, чтобы шеврон и стили сразу начали синхронную анимацию закрытия
        details.classList.add('closing');

        // Вычисляем целевой скролл для центрирования заголовка модуля
        const containerRect = container.getBoundingClientRect();
        const summaryRect = summary.getBoundingClientRect();
        const summaryTopInContent = (summaryRect.top - containerRect.top) + container.scrollTop;

        // В свёрнутом состоянии максимальный скролл уменьшится на startHeight
        const finalMaxScroll = Math.max(0, (container.scrollHeight - startHeight) - container.clientHeight);
        const desiredScrollTop = summaryTopInContent + (summaryRect.height / 2) - (container.clientHeight / 2);
        const targetScrollTop = Math.max(0, Math.min(finalMaxScroll, Math.round(desiredScrollTop)));

        // Плавно и медленно скроллим сайдбар к центру заголовка
        smoothScroll(container, targetScrollTop, ANIMATION_DURATION);

        // Плавно анимируем схлопывание высоты и прозрачности контента
        content.style.overflow = 'hidden';
        const anim = content.animate([
          { height: startHeight + 'px', opacity: 1 },
          { height: '0px', opacity: 0 }
        ], {
          duration: ANIMATION_DURATION,
          easing: EASING
        });

        content._anim = anim;

        anim.onfinish = function () {
          content._anim = null;
          details.removeAttribute('open');
          details.classList.remove('closing');
          content.style.overflow = '';
          content.style.height = '';
          content.style.opacity = '';
        };

        anim.oncancel = function () {
          content._anim = null;
          details.classList.remove('closing');
          content.style.overflow = '';
          content.style.height = '';
          content.style.opacity = '';
        };

      } else {
        // --- РАЗВОРАЧИВАНИЕ МОДУЛЯ ---
        details.classList.remove('closing');
        details.setAttribute('open', '');
        content.style.height = 'auto';
        content.style.overflow = 'hidden';
        const fullHeight = content.offsetHeight;

        if (fullHeight <= 0) {
          content.style.overflow = '';
          return;
        }

        // Вычисляем целевой элемент для центрирования
        const containerRect = container.getBoundingClientRect();
        let targetElement = null;

        const activeItem = details.querySelector('.nav-item.active');
        if (activeItem) {
          // Проверяем, видна ли активная лекция (открыты ли все родительские details до details)
          let isItemVisible = true;
          let p = activeItem.parentElement ? activeItem.parentElement.closest('details') : null;
          let closedSub = null;
          while (p && p !== details) {
            if (!p.hasAttribute('open')) {
              isItemVisible = false;
              closedSub = p;
              break;
            }
            p = p.parentElement ? p.parentElement.closest('details') : null;
          }

          if (isItemVisible) {
            // Если лекция открыта и видна — центрируемся на ней
            targetElement = activeItem;
          } else if (closedSub) {
            // Если подраздел с лекцией свёрнут — центрируемся на заголовке этого подраздела!
            targetElement = closedSub.querySelector('.nav-submodule-title') || closedSub;
          }
        }

        if (!targetElement) {
          // Проверяем, может в развернутом блоке есть активный подраздел
          const activeSub = details.querySelector('.nav-submodule.active-submodule');
          if (activeSub) {
            targetElement = activeSub.querySelector('.nav-submodule-title') || activeSub;
          } else {
            targetElement = summary;
          }
        }

        const targetRect = targetElement.getBoundingClientRect();
        const targetTopInContent = (targetRect.top - containerRect.top) + container.scrollTop;
        const desired = targetTopInContent + (targetRect.height / 2) - (container.clientHeight / 2);
        const maxScroll = Math.max(0, container.scrollHeight - container.clientHeight);
        const targetScrollTop = Math.max(0, Math.min(maxScroll, Math.round(desired)));

        // Плавно скроллим контейнер синхронно с разворачиванием
        smoothScroll(container, targetScrollTop, ANIMATION_DURATION);

        // Плавно анимируем раскрытие высоты и появление контента
        const anim = content.animate([
          { height: '0px', opacity: 0 },
          { height: fullHeight + 'px', opacity: 1 }
        ], {
          duration: ANIMATION_DURATION,
          easing: EASING
        });

        content._anim = anim;

        anim.onfinish = function () {
          content._anim = null;
          content.style.overflow = '';
          content.style.height = '';
          content.style.opacity = '';
        };

        anim.oncancel = function () {
          content._anim = null;
          content.style.overflow = '';
          content.style.height = '';
          content.style.opacity = '';
        };
      }
    });
  }

  // -------------------------------------------------------------------------
  
  // -------------------------------------------------------------------------
  // Mermaid re-render on theme change
  // -------------------------------------------------------------------------
  function rerenderMermaid() {
    if (typeof mermaid === 'undefined') return;
    
    // Close modal if open
    var modal = document.getElementById('mermaid-modal');
    if (modal && modal.classList.contains('active') && typeof window.closeMermaidModal === 'function') {
      window.closeMermaidModal();
    }
    
    // Restore original mermaid source for all diagrams
    document.querySelectorAll('pre.mermaid').forEach(function (el) {
      var src = el.getAttribute('data-mermaid-source');
      if (src) {
        el.textContent = src;
        el.removeAttribute('data-processed');
      }
    });
    
    // Re-initialize with new theme colors
    initMermaid();
    
    // Re-run rendering
    try {
      mermaid.run({ querySelector: 'pre.mermaid' });
    } catch (e) {
      try {
        mermaid.init(undefined, document.querySelectorAll('pre.mermaid'));
      } catch (e2) {
        console.warn('Mermaid re-render failed:', e2);
      }
    }
  }

// 1.1. Инициализация KaTeX (математические формулы LaTeX)
  // -------------------------------------------------------------------------
  function initKaTeX() {
    if (typeof renderMathInElement === 'function') {
      const content = document.querySelector('.article-markdown') || document.body;
      try {
        renderMathInElement(content, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false },
            { left: '\\(', right: '\\)', display: false },
            { left: '\\[', right: '\\]', display: true }
          ],
          ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'option'],
          ignoredClasses: ['code-block', 'mermaid', 'mermaid-wrapper'],
          throwOnError: false
        });
      } catch (err) {
        console.warn('KaTeX rendering warning:', err);
      }
    }
  }

  // -------------------------------------------------------------------------
  // 10. Переключение тем (paper / light / dark)
  // -------------------------------------------------------------------------
  function initThemeSwitcher() {
    const THEME_KEY = 'go_encyclopedia_theme';
    const THEMES = ['paper', 'light', 'dark'];
    const THEME_LABELS = { paper: '📄 Paper', light: '☀️ Light', dark: '🌑 Dark' };

    // Restore saved theme on load (also done by inline script for anti-flicker)
    const saved = localStorage.getItem(THEME_KEY);
    if (saved && THEMES.includes(saved)) {
      document.documentElement.dataset.theme = saved;
    }

    const btn = document.getElementById('theme-switcher-btn');
    if (!btn) return;

    function updateBtn() {
      const current = document.documentElement.dataset.theme || 'paper';
      btn.textContent = THEME_LABELS[current] || current;
      btn.dataset.currentTheme = current;
    }

    updateBtn();

    btn.addEventListener('click', function() {
      const current = document.documentElement.dataset.theme || 'paper';
      const idx = THEMES.indexOf(current);
      const next = THEMES[(idx + 1) % THEMES.length];
      document.documentElement.dataset.theme = next;
      localStorage.setItem(THEME_KEY, next);
      updateBtn();
      setTimeout(rerenderMermaid, 80);
    });
  }

  // -------------------------------------------------------------------------
  // Запуск при загрузке DOM
  // -------------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function () {
    saveMermaidSources();
    initMermaid();
    initKaTeX();
    initActionDelegation();
    initSidebarResize();
    initSidebarFilter();
    initSidebarCentering();
    initScrollProgress();
    initMobileMenu();
    initGlobalSearch();
    initThemeSwitcher();
  });

})();
