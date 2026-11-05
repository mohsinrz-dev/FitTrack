const nav = document.getElementById('main-nav');
if (nav) {
  const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 48);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

const toggle = document.getElementById('nav-toggle');
const drawer = document.getElementById('nav-drawer');
if (toggle && drawer) {
  toggle.addEventListener('click', () => {
    const open = drawer.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open);
    document.body.style.overflow = open ? 'hidden' : '';
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && drawer.classList.contains('open')) {
      drawer.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }
  });
  drawer.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      drawer.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    });
  });
}

function showToast(msg, type = 'success') {
  const container = document.querySelector('.toast-container') || (() => {
    const el = document.createElement('div');
    el.className = 'toast-container';
    document.body.appendChild(el);
    return el;
  })();
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<i class="toast-icon ph ${type === 'success' ? 'ph-check-circle' : 'ph-warning-circle'}"></i><span class="toast-msg">${msg}</span><button class="modal-close" aria-label="Dismiss"><i class="ph ph-x"></i></button>`;
  toast.querySelector('button').addEventListener('click', () => toast.remove());
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

document.querySelectorAll('form[method="POST"]').forEach(form => {
  form.addEventListener('submit', function () {
    const btn = this.querySelector('button[type="submit"]');
    if (btn && !btn.dataset.noLoad) {
      btn.disabled = true;
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="ph ph-circle-notch" style="animation:spin .8s linear infinite"></i> Saving…';
      setTimeout(() => { btn.disabled = false; btn.innerHTML = orig; }, 6000);
    }
  });
});

const style = document.createElement('style');
style.textContent = '@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}';
document.head.appendChild(style);

function initDataAnimations() {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const bars = document.querySelectorAll('.progress-bar-fill[style*="width"]');
  const counters = document.querySelectorAll('[data-count-to]');
  if (!bars.length && !counters.length) return;

  if (prefersReduced) {
    counters.forEach(el => { el.textContent = el.dataset.countTo; });
    return;
  }

  const animateBar = (el) => {
    const target = el.style.width;
    el.style.width = '0%';
    requestAnimationFrame(() => requestAnimationFrame(() => { el.style.width = target; }));
  };

  const animateCounter = (el) => {
    const to = parseFloat(el.dataset.countTo);
    if (isNaN(to)) return;
    const decimals = (el.dataset.countTo.split('.')[1] || '').length;
    const duration = 900;
    const start = performance.now();
    function tick(now) {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (to * eased).toFixed(decimals);
      if (p < 1) requestAnimationFrame(tick);
      else el.textContent = el.dataset.countTo;
    }
    requestAnimationFrame(tick);
  };

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        if (entry.target.classList.contains('progress-bar-fill')) animateBar(entry.target);
        else animateCounter(entry.target);
        obs.unobserve(entry.target);
      });
    }, { threshold: 0.3 });
    bars.forEach(el => io.observe(el));
    counters.forEach(el => io.observe(el));
  } else {
    bars.forEach(animateBar);
    counters.forEach(animateCounter);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initDataAnimations();

  if (typeof gsap !== 'undefined') {
    gsap.fromTo('body', { opacity: 0 }, { opacity: 1, duration: .25, ease: 'power1.out' });
  }

  document.querySelectorAll('.sidebar-link, .nav-link').forEach(link => {
    link.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('javascript')) return;
      if (typeof gsap === 'undefined') return;
      e.preventDefault();
      gsap.to('body', {
        opacity: 0, duration: .18, ease: 'power1.in',
        onComplete: () => { window.location.href = href; }
      });
    });
  });
});
