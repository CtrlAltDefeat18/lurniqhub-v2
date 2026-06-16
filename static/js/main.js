// LurniqHub — general page utilities

// Animate number counters
document.querySelectorAll('[data-count]').forEach(el => {
  const target = parseInt(el.dataset.count, 10);
  if (isNaN(target) || target < 0) return;
  let start = 0;
  const step = Math.max(1, Math.ceil(target / 60));
  let rafId = null;
  const tick = () => {
    start = Math.min(start + step, target);
    el.textContent = start.toLocaleString();
    if (start < target) {
      rafId = requestAnimationFrame(tick);
      el._rafId = rafId;
    } else {
      el._rafId = null;
    }
  };
  rafId = requestAnimationFrame(tick);
  el._rafId = rafId;
});

// Progress bars: animate width from 0 to data-pct
document.querySelectorAll('[data-pct]').forEach(el => {
  let pct = parseFloat(el.dataset.pct);
  if (isNaN(pct)) return;
  pct = Math.max(0, Math.min(100, pct));
  el.style.width = '0%';
  const tid = setTimeout(() => {
    el.style.transition = 'width 1s cubic-bezier(.4,0,.2,1)';
    el.style.width = pct + '%';
    el._animTimeout = null;
  }, 100);
  el._animTimeout = tid;
});

// GSAP stagger on .animate-in elements
if (typeof gsap !== 'undefined' && gsap.from) {
  try {
    gsap.from('.animate-in', {
      duration: 0.5,
      y: 20,
      opacity: 0,
      stagger: 0.07,
      ease: 'power2.out',
      clearProps: 'transform',
    });
  } catch (e) { console.error('GSAP animate-in error', e); }
}
