/* ==========================================================================
   Портфолио — клиентские микровзаимодействия.
   Все скрипты — внешние файлы (без инлайнового кода, CSP без 'unsafe-inline').
   ========================================================================== */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------------------------
     1. Появление блоков при скролле (fade-in / slide-up)
     ------------------------------------------------------------------ */
  function initReveal() {
    var items = Array.prototype.slice.call(document.querySelectorAll('[data-reveal]'));
    if (!items.length) return;

    if (reduceMotion || !('IntersectionObserver' in window)) {
      items.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var siblings = el.parentElement ? Array.prototype.indexOf.call(el.parentElement.children, el) : 0;
        var delay = Math.min(siblings, 6) * 70;
        el.style.transitionDelay = delay + 'ms';
        el.classList.add('is-visible');
        observer.unobserve(el);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.12 });

    items.forEach(function (el) { observer.observe(el); });
  }

  /* ------------------------------------------------------------------
     2. Мобильное меню
     ------------------------------------------------------------------ */
  function initNav() {
    var burger = document.querySelector('[data-burger]');
    var nav = document.querySelector('[data-nav]');
    if (!burger || !nav) return;

    function setState(open) {
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      nav.classList.toggle('is-open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    }

    burger.addEventListener('click', function () {
      setState(burger.getAttribute('aria-expanded') !== 'true');
    });

    nav.addEventListener('click', function (event) {
      if (event.target.closest('a')) setState(false);
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') setState(false);
    });

    window.addEventListener('resize', function () {
      if (window.innerWidth >= 1024) setState(false);
    });
  }

  /* ------------------------------------------------------------------
     3. Тень у шапки при прокрутке
     ------------------------------------------------------------------ */
  function initHeader() {
    var header = document.querySelector('[data-header]');
    if (!header) return;

    var ticking = false;
    function update() {
      header.classList.toggle('is-stuck', window.scrollY > 8);
      ticking = false;
    }

    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(update);
    }, { passive: true });

    update();
  }

  /* ------------------------------------------------------------------
     4. Галерея: слайдер со свайпом (мобильные) + кнопки навигации
     ------------------------------------------------------------------ */
  function initGallery() {
    var gallery = document.querySelector('[data-gallery]');
    if (!gallery) return;

    var controls = document.querySelector('[data-gallery-controls]');
    var prev = document.querySelector('[data-gallery-prev]');
    var next = document.querySelector('[data-gallery-next]');
    var items = gallery.querySelectorAll('.gallery__item');

    if (controls && items.length > 1) {
      controls.removeAttribute('hidden');
    }

    function step() {
      if (!items.length) return 0;
      var first = items[0];
      var gap = parseFloat(window.getComputedStyle(gallery).columnGap || '16') || 16;
      return first.getBoundingClientRect().width + gap;
    }

    function scrollBy(direction) {
      gallery.scrollBy({ left: direction * step(), behavior: reduceMotion ? 'auto' : 'smooth' });
    }

    if (prev) prev.addEventListener('click', function () { scrollBy(-1); });
    if (next) next.addEventListener('click', function () { scrollBy(1); });
  }

  /* ------------------------------------------------------------------
     5. Клиентская валидация и отправка формы
     ------------------------------------------------------------------ */
  var validators = {
    name: function (value) {
      if (!value) return 'Укажите, как к вам обращаться';
      if (value.length < 2) return 'Имя слишком короткое';
      return '';
    },
    contact: function (value) {
      if (!value) return 'Укажите Telegram или email для ответа';
      if (value.indexOf('@') > -1) {
        if (!/^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$/.test(value)) return 'Проверьте формат email';
        return '';
      }
      if (!/^@?[A-Za-z0-9_]{3,32}$/.test(value)) return 'Проверьте ник в Telegram';
      return '';
    },
    message: function (value) {
      if (!value) return 'Опишите задачу подробнее';
      if (value.trim().length < 10) return 'Минимум 10 символов';
      return '';
    },
    consent: function (value, field) {
      if (!field.checked) return 'Подтвердите согласие на обработку данных';
      return '';
    }
  };

  function setError(form, name, message) {
    var input = form.querySelector('[name="' + name + '"]');
    var box = form.querySelector('[data-error-for="' + name + '"]');
    if (input && input.classList) input.classList.toggle('is-invalid', Boolean(message));
    if (box) {
      box.textContent = message || '';
      box.classList.toggle('is-visible', Boolean(message));
    }
  }

  function validateField(form, name) {
    var input = form.querySelector('[name="' + name + '"]');
    var validator = validators[name];
    if (!input || !validator) return true;
    var value = input.type === 'checkbox' ? '' : (input.value || '').trim();
    var message = validator(value, input);
    setError(form, name, message);
    return !message;
  }

  function initForm() {
    var form = document.querySelector('#contact-form');
    if (!form) return;

    var status = form.querySelector('[data-form-status]');
    var submit = form.querySelector('[data-submit]');

    ['name', 'contact', 'message', 'consent'].forEach(function (name) {
      var input = form.querySelector('[name="' + name + '"]');
      if (!input) return;
      input.addEventListener('blur', function () { validateField(form, name); });
      input.addEventListener('input', function () {
        if (input.classList.contains('is-invalid')) validateField(form, name);
      });
      if (input.type === 'checkbox') {
        input.addEventListener('change', function () { validateField(form, name); });
      }
    });

    form.addEventListener('submit', function (event) {
      var valid = ['name', 'contact', 'message', 'consent'].map(function (name) {
        return validateField(form, name);
      }).every(Boolean);

      if (!valid) {
        event.preventDefault();
        var firstError = form.querySelector('.is-invalid');
        if (firstError && firstError.focus) firstError.focus();
        if (status) {
          status.textContent = 'Проверьте отмеченные поля.';
          status.className = 'form__status is-error';
        }
        return;
      }

      event.preventDefault();
      if (submit) {
        submit.disabled = true;
        submit.textContent = 'Отправляю…';
      }
      if (status) {
        status.textContent = 'Отправляю заявку…';
        status.className = 'form__status';
      }

      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'
      })
        .then(function (response) {
          return response.json().then(function (data) {
            return { ok: response.ok, data: data };
          });
        })
        .then(function (result) {
          if (result.ok && result.data && result.data.ok) {
            form.reset();
            ['name', 'contact', 'message', 'consent'].forEach(function (name) { setError(form, name, ''); });
            if (status) {
              status.textContent = result.data.message || 'Заявка отправлена.';
              status.className = 'form__status is-success';
            }
          } else {
            var message = (result.data && result.data.message) || 'Не удалось отправить заявку. Попробуйте ещё раз.';
            if (status) {
              status.textContent = message;
              status.className = 'form__status is-error';
            }
          }
        })
        .catch(function () {
          if (status) {
            status.textContent = 'Сеть недоступна. Напишите, пожалуйста, в Telegram.';
            status.className = 'form__status is-error';
          }
        })
        .then(function () {
          if (submit) {
            submit.disabled = false;
            submit.textContent = 'Отправить заявку';
          }
        });
    });
  }

  /* ------------------------------------------------------------------
     6. Админ-панель: автосохранение переключателя
     ------------------------------------------------------------------ */
  function initAdmin() {
    var toggles = document.querySelectorAll('[data-auto-submit]');
    Array.prototype.forEach.call(toggles, function (toggle) {
      toggle.addEventListener('change', function () {
        if (toggle.form) toggle.form.submit();
      });
    });
  }

  /* ------------------------------------------------------------------
     Запуск
     ------------------------------------------------------------------ */
  function init() {
    initReveal();
    initNav();
    initHeader();
    initGallery();
    initForm();
    initAdmin();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
