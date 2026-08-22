/* McCormack's Pharmacy theme JS — shared behaviors, wired via data attributes. */
(() => {
  const on = (root, evt, sel, fn) =>
    root.addEventListener(evt, e => {
      const t = e.target.closest(sel);
      if (t && root.contains(t)) fn(e, t);
    });

  // ---- Mega menu: data-mega-trigger="key" links, data-mega-panel="key" panels,
  // data-mega-root wrapper. Opens on hover/keyboard focus; tap-to-open on touch
  // (second tap follows the link); 250ms close grace on mouseleave; Esc closes;
  // aria-expanded kept in sync; open trigger stays highlighted via [data-open].
  document.querySelectorAll('[data-mega-root]').forEach(root => {
    const panels = root.querySelectorAll('[data-mega-panel]');
    const triggers = root.querySelectorAll('[data-mega-trigger]');
    let closeTimer = null;
    const closeAll = () => {
      clearTimeout(closeTimer);
      panels.forEach(p => p.removeAttribute('data-open'));
      triggers.forEach(t => { t.removeAttribute('data-open'); t.setAttribute('aria-expanded', 'false'); });
    };
    const open = key => {
      clearTimeout(closeTimer);
      closeAll();
      const panel = root.querySelector(`[data-mega-panel="${key}"]`);
      if (!panel) return;
      panel.setAttribute('data-open', 'true');
      const t = root.querySelector(`[data-mega-trigger="${key}"]`);
      if (t) { t.setAttribute('data-open', 'true'); t.setAttribute('aria-expanded', 'true'); }
      // narrow panels align under their trigger (wide ones span from the container edge)
      const inner = panel.firstElementChild;
      if (t && inner && inner.offsetWidth > 0 && inner.offsetWidth < 500) {
        const max = root.clientWidth - inner.offsetWidth - 30;
        inner.style.left = Math.max(30, Math.min(t.offsetLeft, max)) + 'px';
      }
    };
    const scheduleClose = () => { clearTimeout(closeTimer); closeTimer = setTimeout(closeAll, 250); };

    const canHover = () => matchMedia('(hover: hover)').matches;
    triggers.forEach(t => {
      t.setAttribute('aria-haspopup', 'true');
      t.setAttribute('aria-expanded', 'false');
      // a tap fires synthetic mouseenter/focus before click, so hover-open is
      // gated to hover-capable devices and focus-open to real keyboard focus
      t.addEventListener('mouseenter', () => { if (canHover()) open(t.dataset.megaTrigger); });
      t.addEventListener('focus', () => { if (t.matches(':focus-visible')) open(t.dataset.megaTrigger); });
      t.addEventListener('click', e => {
        // touch devices: first tap opens the panel, second tap follows the link
        if (!canHover()) {
          const panel = root.querySelector(`[data-mega-panel="${t.dataset.megaTrigger}"]`);
          if (panel && panel.getAttribute('data-open') !== 'true') {
            e.preventDefault();
            open(t.dataset.megaTrigger);
          }
        }
      });
    });
    root.querySelectorAll('[data-mega-close]').forEach(a => {
      a.addEventListener('mouseenter', closeAll);
      a.addEventListener('focus', closeAll);
    });
    panels.forEach(p => p.addEventListener('mouseenter', () => {
      clearTimeout(closeTimer);
      p.setAttribute('data-open', 'true');
    }));
    root.addEventListener('mouseenter', () => clearTimeout(closeTimer));
    root.addEventListener('mouseleave', scheduleClose);
    root.addEventListener('focusout', e => { if (!root.contains(e.relatedTarget)) closeAll(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAll(); });
    // tapping outside the nav closes an open panel on touch
    document.addEventListener('click', e => { if (!root.contains(e.target)) closeAll(); });
  });

  // ---- Mobile drawer
  on(document, 'click', '[data-mnav-open-btn]', () => document.body.setAttribute('data-mnav-open', ''));
  on(document, 'click', '[data-mnav-close]', () => document.body.removeAttribute('data-mnav-open'));

  // ---- Scroll rails: button[data-rail-btn][data-rail-target=id][data-rail-by=px]
  // Each arrow hides when it has nothing to do: back at scroll 0, forward at the
  // end — and both when the track doesn't overflow at all (wide viewports, few items).
  on(document, 'click', '[data-rail-btn]', (e, btn) => {
    const track = document.getElementById(btn.dataset.railTarget);
    if (track) track.scrollBy({ left: parseInt(btn.dataset.railBy, 10), behavior: 'smooth' });
  });
  document.querySelectorAll('[data-rail-btn]').forEach(btn => {
    const track = document.getElementById(btn.dataset.railTarget);
    if (!track) return;
    const back = btn.hasAttribute('data-rail-back');
    const sync = () => {
      const room = track.scrollWidth - track.clientWidth;
      const useful = room > 4 && (back ? track.scrollLeft > 4 : track.scrollLeft < room - 4);
      btn.style.display = useful ? 'flex' : 'none';
    };
    track.addEventListener('scroll', sync, { passive: true });
    addEventListener('resize', sync);
    if (window.ResizeObserver) new ResizeObserver(sync).observe(track);
    sync();
  });

  // ---- Hero slider: [data-slider] holds [data-slide] panes + [data-slide-dot] dots.
  // Optional autoplay via data-slider-auto="<ms>": paused on hover, stopped for
  // good on manual dot use, skipped under prefers-reduced-motion.
  document.querySelectorAll('[data-slider]').forEach(slider => {
    const slides = slider.querySelectorAll('[data-slide]');
    const dots = slider.querySelectorAll('[data-slide-dot]');
    let idx = 0;
    const go = i => {
      idx = i;
      slides.forEach((s, j) => { s.style.display = j === i ? '' : 'none'; });
      dots.forEach((d, j) => {
        d.style.background = j === i ? '#ffffff' : 'rgba(255,255,255,.5)';
        d.style.width = j === i ? '22px' : '8px';
      });
    };
    go(0);

    const auto = parseInt(slider.dataset.sliderAuto || '0', 10);
    let timer = null;
    const play = () => { if (auto && !timer) timer = setInterval(() => go((idx + 1) % slides.length), auto); };
    const pause = () => { clearInterval(timer); timer = null; };
    let stopped = false;
    dots.forEach((d, i) => d.addEventListener('click', () => { stopped = true; pause(); go(i); }));
    if (auto > 0 && slides.length > 1 && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      slider.addEventListener('mouseenter', pause);
      slider.addEventListener('mouseleave', () => { if (!stopped) play(); });
      play();
    }
  });

  // ---- Missing images degrade to the theme's striped panel instead of the
  // browser's broken-image icon. Capture phase, because 'error' does not bubble.
  // Covers hardcoded theme assets (where Liquid cannot test for a missing file,
  // asset_url returns a URL either way) and catalogue images alike.
  document.addEventListener('error', (e) => {
    const img = e.target;
    if (!img || img.tagName !== 'IMG' || img.dataset.fallbackApplied) return;
    img.dataset.fallbackApplied = '1';
    img.classList.add('img-fallback');
    img.removeAttribute('srcset');
    // 1x1 transparent gif: keeps layout box and alt text, drops the broken icon
    img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
  }, true);

  // ---- Accordions: [data-acc-toggle=key] toggles [data-acc-content=key] (+ rotates [data-acc-chevron])
  on(document, 'click', '[data-acc-toggle]', (e, btn) => {
    const key = btn.dataset.accToggle;
    const content = document.querySelector(`[data-acc-content="${key}"]`);
    if (!content) return;
    const open = content.getAttribute('data-open') === 'true';
    content.setAttribute('data-open', String(!open));
    const chev = btn.querySelector('[data-acc-chevron], .ftr-acc-chevron');
    if (chev) chev.style.transform = open ? 'rotate(0deg)' : 'rotate(180deg)';
    if (btn.hasAttribute('aria-expanded')) btn.setAttribute('aria-expanded', String(!open));
  });

  // ---- AJAX add to cart: form[data-ajax-add] or button[data-add-id=variantId]
  // Routes come from Liquid (layout/theme.liquid) so this keeps working under a
  // locale or market path prefix, e.g. /en-ie/cart/add.js.
  const routes = window.mccRoutes || {};
  const cartAddUrl = (routes.cart_add_url || '/cart/add') + '.js';
  const cartUrl = (routes.cart_url || '/cart') + '.js';
  async function addToCart(id, qty) {
    const res = await fetch(cartAddUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, quantity: qty || 1 }),
    });
    if (!res.ok) throw new Error('add failed');
    const cart = await fetch(cartUrl).then(r => r.json());
    document.querySelectorAll('[data-cart-count]').forEach(el => {
      el.textContent = cart.item_count;
      el.style.display = cart.item_count > 0 ? 'flex' : 'none';
    });
    return cart;
  }
  on(document, 'click', '[data-add-id]', async (e, btn) => {
    e.preventDefault();
    const label = btn.textContent;
    btn.disabled = true;
    try {
      await addToCart(parseInt(btn.dataset.addId, 10), parseInt(btn.dataset.addQty || '1', 10));
      btn.textContent = 'Added ✓';
    } catch {
      btn.textContent = 'Sold out';
    }
    setTimeout(() => { btn.textContent = label; btn.disabled = false; }, 1600);
  });
  on(document, 'submit', 'form[data-ajax-add]', async (e, form) => {
    e.preventDefault();
    const id = parseInt(new FormData(form).get('id'), 10);
    const qty = parseInt(new FormData(form).get('quantity') || '1', 10);
    const btn = form.querySelector('[type=submit]');
    if (btn) btn.disabled = true;
    try { await addToCart(id, qty); if (btn) btn.textContent = 'Added to bag ✓'; }
    catch { if (btn) btn.textContent = 'Unavailable'; }
    if (btn) setTimeout(() => { btn.disabled = false; btn.textContent = 'Add To Bag'; }, 1600);
  });

  // ---- Generic tab views: [data-view-btn=key] shows [data-view=key], hides siblings
  on(document, 'click', '[data-view-btn]', (e, btn) => {
    e.preventDefault();
    const key = btn.dataset.viewBtn;
    document.querySelectorAll('[data-view]').forEach(v => {
      v.style.display = v.dataset.view === key ? '' : 'none';
    });
    document.querySelectorAll('[data-view-btn]').forEach(b =>
      b.setAttribute('data-active', String(b.dataset.viewBtn === key)));
  });
})();
