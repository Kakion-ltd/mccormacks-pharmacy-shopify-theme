/* McCormack's Pharmacy theme JS — shared behaviors, wired via data attributes. */
(() => {
  const on = (root, evt, sel, fn) =>
    root.addEventListener(evt, e => {
      const t = e.target.closest(sel);
      if (t && root.contains(t)) fn(e, t);
    });

  // Both drawers become visible by flipping an attribute on <body>, and both are
  // visibility:hidden until it lands. Calling focus() in the same task focuses
  // nothing — the element is still hidden as far as the un-flushed style is
  // concerned, and focus() on a hidden element is silently a no-op. One frame
  // later the style has been recomputed and it takes.
  const focusSoon = (el) => { if (el) requestAnimationFrame(() => el.focus()); };

  // Mirror the shop's money format loosely; exact rendering stays server-side
  // wherever Liquid can do it. Intl keeps decimals and grouping correct per locale.
  const formatMoney = (cents) => {
    try {
      return new Intl.NumberFormat(document.documentElement.lang || 'en-IE',
        { style: 'currency', currency: 'EUR' }).format(cents / 100);
    } catch { return '\u20ac' + (cents / 100).toFixed(2); }
  };

  const escapeHtml = (t) => String(t == null ? '' : t).replace(/[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

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

  // ---- Mobile drawer, with drill-down panels.
  // The drawer used to be ten flat links whose right-chevron only ever went to
  // the department page, so 197 groups and leaves were unreachable on a phone.
  // Panels come from snippets/mobile-nav.liquid, generated from the taxonomy.
  const mnav = document.querySelector('.mnav-drawer');
  const mnavStack = document.querySelector('[data-mnav-stack]');
  let mnavLastFocus = null;

  const mnavPanel = (key) => mnavStack && mnavStack.querySelector('[data-mnav-panel="' + key + '"]');

  // Show one panel, hide the rest. Kept as a full reset rather than a stack of
  // opens, so a mis-click can never leave two panels visible at once.
  const mnavGoTo = (key, back) => {
    if (!mnavStack) return;
    const next = mnavPanel(key);
    if (!next) return;
    mnavStack.querySelectorAll('[data-mnav-panel]').forEach((p) => {
      p.hidden = p !== next;
      p.classList.remove('is-current', 'is-entering', 'is-entering-back');
    });
    next.classList.add('is-current', back ? 'is-entering-back' : 'is-entering');
    if (mnav) mnav.scrollTop = 0;
    focusSoon(next.querySelector('[data-mnav-back], .mnav-link'));
  };

  const mnavOpen = () => {
    mnavLastFocus = document.activeElement;
    document.body.setAttribute('data-mnav-open', '');
    focusSoon(mnav && mnav.querySelector('[data-mnav-close]'));
  };
  const mnavClose = () => {
    document.body.removeAttribute('data-mnav-open');
    // Reset to the root so reopening does not drop the shopper back into
    // whatever branch they last looked at.
    if (mnavStack) mnavGoTo('root', false);
    if (mnavLastFocus && mnavLastFocus.focus) mnavLastFocus.focus();
  };

  on(document, 'click', '[data-mnav-open-btn]', mnavOpen);
  on(document, 'click', '[data-mnav-close]', mnavClose);
  on(document, 'click', '[data-mnav-into]', (e, btn) => {
    e.preventDefault();
    mnavGoTo(btn.dataset.mnavInto, false);
  });
  on(document, 'click', '[data-mnav-back]', (e, btn) => {
    e.preventDefault();
    const panel = btn.closest('[data-mnav-panel]');
    mnavGoTo((panel && panel.dataset.mnavParent) || 'root', true);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape' || !document.body.hasAttribute('data-mnav-open')) return;
    // Escape steps back a level first, and only closes from the root — the same
    // way the browser back button would behave if these were pages.
    const current = mnavStack && mnavStack.querySelector('[data-mnav-panel].is-current');
    const parent = current && current.dataset.mnavParent;
    if (parent && current.dataset.mnavPanel !== 'root') mnavGoTo(parent, true);
    else mnavClose();
  });

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

  // ---- Cart cross-sell rail. Shopify renders sections/cart-recommendations.liquid
  // for us, which is where restricted products and items already in the bag are
  // filtered out — deliberately in Liquid, so no path through this file can
  // reintroduce a line that must not be one-click added.
  // Declared as a function so the drawer below can call it regardless of order.
  function loadRecs(mount, productId, key) {
    if (!mount) return;
    if (!productId) { mount.hidden = true; mount.innerHTML = ''; delete mount.dataset.crecKey; return; }
    // Refetch when the bag changes, not just when the anchor product does — a
    // product just added must drop out of its own recommendation rail.
    if (mount.dataset.crecKey === key) return;
    mount.dataset.crecKey = key;
    const base = (window.mccRoutes || {}).product_recommendations_url || '/recommendations/products';
    const url = base + '?section_id=cart-recommendations&limit=8&intent=related'
      + '&product_id=' + encodeURIComponent(productId);
    fetch(url)
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error('recommendations failed'))))
      .then((html) => {
        const holder = document.createElement('div');
        holder.innerHTML = html;
        const rail = holder.querySelector('[data-crec]');
        mount.innerHTML = rail ? rail.outerHTML : '';
        mount.hidden = !rail;
      })
      .catch(() => { mount.hidden = true; mount.innerHTML = ''; });
  }

  // Cart page mount: anchor product is baked into the markup by Liquid.
  document.querySelectorAll('[data-crec-mount][data-crec-product]').forEach((mount) => {
    loadRecs(mount, mount.dataset.crecProduct, 'page:' + mount.dataset.crecProduct);
  });

  // ---- Cart drawer. Rendered client-side from the Cart AJAX API so it is correct
  // after every add without a page load. Opens on a successful add, which is the
  // whole point: before this, add-to-cart had no route to checkout.
  const cd = {
    drawer: document.querySelector('[data-cd-drawer]'),
    overlay: document.querySelector('[data-cd-overlay]'),
  };
  if (cd.drawer) {
    const $ = (sel) => cd.drawer.querySelector(sel);
    const threshold = parseInt(cd.drawer.dataset.cdThreshold || '0', 10);
    const fmt = formatMoney;
    const esc = escapeHtml;

    const recMount = $('[data-crec-mount]');
    let lastFocus = null;
    const open = () => {
      lastFocus = document.activeElement;
      document.body.setAttribute('data-cd-open', '');
      focusSoon($('[data-cd-close]'));
    };
    const close = () => {
      document.body.removeAttribute('data-cd-open');
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    };
    cd.overlay && cd.overlay.addEventListener('click', close);
    on(document, 'click', '[data-cd-close]', (e) => { e.preventDefault(); close(); });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && document.body.hasAttribute('data-cd-open')) close();
    });

    const render = (cart) => {
      $('[data-cd-count]').textContent = '(' + cart.item_count + ')';
      const empty = cart.item_count === 0;
      $('[data-cd-empty]').hidden = !empty;
      $('[data-cd-foot]').hidden = empty;
      $('[data-cd-ship]').hidden = empty || !threshold;

      if (!empty && threshold) {
        const left = threshold - cart.total_price;
        $('[data-cd-ship-msg]').textContent = left <= 0
          ? 'You have free delivery'
          : fmt(left) + ' away from free delivery';
        $('[data-cd-bar]').style.width =
          Math.min(100, Math.round((cart.total_price / threshold) * 100)) + '%';
      }
      $('[data-cd-subtotal]').textContent = fmt(cart.total_price);

      $('[data-cd-items]').innerHTML = cart.items.map((it, i) => {
        const img = it.image
          ? '<img src="' + esc(it.image) + '" alt="" loading="lazy">'
          : '<span style="display:block;width:100%;height:100%;background:repeating-linear-gradient(135deg,#dfe6d5,#dfe6d5 12px,#d7dfcb 12px,#d7dfcb 24px);"></span>';
        const was = (it.original_line_price > it.final_line_price)
          ? '<span class="cd-line-was">' + fmt(it.original_line_price) + '</span>' : '';
        return '<div class="cd-line" data-cd-line="' + (i + 1) + '">' +
          '<span class="cd-line-img">' + img + '</span>' +
          '<div class="cd-line-body">' +
            (it.product_type || it.vendor ? '<span class="cd-line-vendor">' + esc(it.vendor) + '</span>' : '') +
            '<span class="cd-line-title"><a href="' + esc(it.url) + '">' + esc(it.product_title) + '</a></span>' +
            '<div class="cd-line-foot">' +
              '<span class="cd-qty">' +
                '<button type="button" data-cd-qty="' + (i + 1) + '" data-cd-to="' + (it.quantity - 1) + '" aria-label="Decrease quantity">&minus;</button>' +
                '<span>' + it.quantity + '</span>' +
                '<button type="button" data-cd-qty="' + (i + 1) + '" data-cd-to="' + (it.quantity + 1) + '" aria-label="Increase quantity">+</button>' +
              '</span>' +
              '<span class="cd-line-price">' + was + fmt(it.final_line_price) + '</span>' +
            '</div>' +
          '</div>' +
        '</div>';
      }).join('');

      // Cross-sell follows the first line item, and refreshes whenever the bag changes.
      loadRecs(recMount,
        empty ? null : cart.items[0].product_id,
        empty ? '' : cart.items[0].product_id + ':' + cart.item_count);
    };

    // Line quantity changes inside the drawer, including remove (quantity 0).
    on(document, 'click', '[data-cd-qty]', async (e, btn) => {
      const line = parseInt(btn.dataset.cdQty, 10);
      const to = Math.max(0, parseInt(btn.dataset.cdTo, 10));
      cd.drawer.querySelectorAll('[data-cd-qty]').forEach((b) => { b.disabled = true; });
      try {
        const changeUrl = ((window.mccRoutes || {}).cart_change_url || '/cart/change') + '.js';
        const res = await fetch(changeUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ line, quantity: to }),
        });
        const cart = await res.json();
        render(cart);
        document.querySelectorAll('[data-cart-count]').forEach((el) => {
          el.textContent = cart.item_count;
          el.style.display = cart.item_count > 0 ? 'flex' : 'none';
        });
      } catch { /* leave the drawer as-is; the cart page is the source of truth */ }
    });

    window.mccCartDrawer = { open, close, render };
  }

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
      const cart = await addToCart(parseInt(btn.dataset.addId, 10), parseInt(btn.dataset.addQty || '1', 10));
      btn.textContent = 'Added ✓';
      if (window.mccCartDrawer) { window.mccCartDrawer.render(cart); window.mccCartDrawer.open(); }
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
    try {
      const cart = await addToCart(id, qty);
      if (btn) btn.textContent = 'Added to bag ✓';
      if (window.mccCartDrawer) { window.mccCartDrawer.render(cart); window.mccCartDrawer.open(); }
    }
    catch { if (btn) btn.textContent = 'Unavailable'; }
    if (btn) setTimeout(() => { btn.disabled = false; btn.textContent = 'Add To Bag'; }, 1600);
  });

  // ---- Wishlist. Stored in the visitor's own browser, no account and no app.
  // Only handles are stored; the wishlist page reads price, stock and image live
  // from /products/<handle>.js, so a saved item cannot show a stale price and a
  // deleted product drops out by itself.
  const WISH_KEY = 'mcc_wishlist';
  let wishRender = null;

  const wishRead = () => {
    try {
      const raw = JSON.parse(localStorage.getItem(WISH_KEY) || '{}');
      return Array.isArray(raw.items) ? raw.items.filter((h) => typeof h === 'string') : [];
    } catch {
      // Private mode, blocked storage, or something else wrote to the key.
      return [];
    }
  };
  const wishWrite = (items) => {
    try { localStorage.setItem(WISH_KEY, JSON.stringify({ v: 1, items })); } catch { /* nothing we can do */ }
  };

  const wishCount = () => {
    const n = wishRead().length;
    document.querySelectorAll('[data-wish-count]').forEach((el) => {
      el.textContent = n;
      el.style.display = n > 0 ? 'flex' : 'none';
    });
  };

  // Every button for a handle reflects the same state — a product can appear in
  // a grid and a rail on the same page.
  const wishSync = () => {
    const items = wishRead();
    document.querySelectorAll('[data-wish-toggle]').forEach((btn) => {
      const saved = items.indexOf(btn.dataset.wishToggle) > -1;
      btn.setAttribute('aria-pressed', String(saved));
      btn.classList.toggle('is-saved', saved);
      const label = btn.querySelector('[data-wish-label]');
      if (label) label.textContent = saved ? 'Saved' : 'Save for later';
    });
    wishCount();
  };

  on(document, 'click', '[data-wish-toggle]', (e, btn) => {
    e.preventDefault();
    const handle = btn.dataset.wishToggle;
    const items = wishRead();
    const at = items.indexOf(handle);
    if (at > -1) items.splice(at, 1); else items.unshift(handle);
    wishWrite(items);
    wishSync();
    if (typeof wishRender === 'function') wishRender();
  });
  wishSync();

  // ---- Wishlist page. Cards are built from live product JSON.
  const wishGrid = document.querySelector('[data-wish-grid]');
  if (wishGrid) {
    const wishEmpty = document.querySelector('[data-wish-empty]');
    // The pharmacy gate lives in Liquid everywhere else. This page renders
    // client-side, so the tag has to come across in the markup — otherwise a
    // restricted product would get a one-click add here and nowhere else.
    const gateTag = (wishGrid.dataset.wishRestrictedTag || '').toLowerCase();

    const card = (p) => {
      const restricted = gateTag && (p.tags || []).some((t) => String(t).toLowerCase() === gateTag);
      const quickAdd = !restricted && p.available && p.variants && p.variants.length === 1;
      const img = p.featured_image
        ? '<img src="' + escapeHtml(p.featured_image) + '" alt="" loading="lazy" class="wish-card-img">'
        : '<span class="wish-card-ph"></span>';
      let action;
      if (quickAdd) {
        action = '<button type="button" class="wish-add hov-bg-green" data-add-id="' + p.variants[0].id + '">Add To Bag</button>';
      } else {
        action = '<a class="wish-add wish-add-link hov-bg-green" href="/products/' + encodeURIComponent(p.handle) + '">'
          + (restricted ? 'View product' : (p.available ? 'Choose options' : 'Out of stock')) + '</a>';
      }
      return '<div class="wish-card">'
        + '<a class="wish-card-thumb" href="/products/' + encodeURIComponent(p.handle) + '">' + img + '</a>'
        + '<a class="wish-card-title" href="/products/' + encodeURIComponent(p.handle) + '">' + escapeHtml(p.title) + '</a>'
        + '<div class="wish-card-price">' + formatMoney(p.price) + '</div>'
        + action
        + '<button type="button" class="wish-remove" data-wish-toggle="' + escapeHtml(p.handle) + '">Remove</button>'
        + '</div>';
    };

    wishRender = async () => {
      const handles = wishRead();
      if (!handles.length) {
        wishGrid.innerHTML = '';
        wishGrid.hidden = true;
        if (wishEmpty) wishEmpty.hidden = false;
        return;
      }
      if (wishEmpty) wishEmpty.hidden = true;
      wishGrid.hidden = false;
      const results = await Promise.all(handles.map((h) =>
        fetch('/products/' + encodeURIComponent(h) + '.js')
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null)));

      // A product that no longer resolves has been deleted or unpublished.
      // Drop it rather than leaving a dead card the shopper cannot clear.
      const alive = [];
      const gone = [];
      results.forEach((p, i) => (p ? alive.push(p) : gone.push(handles[i])));
      if (gone.length) {
        wishWrite(handles.filter((h) => gone.indexOf(h) === -1));
        wishCount();
      }
      wishGrid.innerHTML = alive.map(card).join('');
      if (!alive.length) {
        wishGrid.hidden = true;
        if (wishEmpty) wishEmpty.hidden = false;
      }
    };
    wishRender();
  }

  // ---- Cookie consent. Drives Shopify's Customer Privacy API; stores nothing
  // itself. See snippets/consent-banner.liquid for how the gating works and why
  // it must not be reimplemented with a cookie.
  const ccBanner = document.querySelector('[data-cc-banner]');
  if (ccBanner) {
    const ccOptions = ccBanner.querySelector('[data-cc-options]');
    const ccManage = ccBanner.querySelector('[data-cc-manage]');
    const ccToggles = () => Array.from(ccBanner.querySelectorAll('[data-cc-toggle]'));

    const ccShow = () => {
      ccBanner.hidden = false;
      // Announce it without yanking focus off whatever the visitor is reading;
      // the first control is one Tab away because the banner is last in the DOM.
      ccBanner.setAttribute('tabindex', '-1');
    };
    const ccHide = () => {
      ccBanner.hidden = true;
      if (ccOptions) ccOptions.hidden = true;
      if (ccManage) ccManage.setAttribute('aria-expanded', 'false');
    };

    // Reflect stored consent into the checkboxes when reopening from the footer.
    const ccSync = (privacy) => {
      let current = {};
      try { current = privacy.currentVisitorConsent() || {}; } catch { current = {}; }
      ccToggles().forEach((input) => {
        input.checked = current[input.dataset.ccToggle] === 'yes';
      });
    };

    const ccApply = (privacy, consent) => {
      // sale_of_data is a US concept and is never granted from this banner; the
      // store does not sell personal data. Sending it explicitly keeps Shopify
      // from inferring it from the marketing grant.
      const payload = {
        preferences: !!consent.preferences,
        analytics: !!consent.analytics,
        marketing: !!consent.marketing,
        sale_of_data: false,
      };
      try {
        privacy.setTrackingConsent(payload, () => ccHide());
      } catch {
        // If the call throws, leave the banner up rather than hiding it and
        // implying a choice was recorded.
      }
    };

    const ccInit = (privacy) => {
      // shouldShowBanner() honours the shop's own region rules, so a visitor
      // outside a consent region is not nagged.
      let show = true;
      try { show = privacy.shouldShowBanner(); } catch { show = true; }
      if (show) ccShow();
      ccSync(privacy);

      on(document, 'click', '[data-cc-accept]', (e) => {
        e.preventDefault();
        ccApply(privacy, { preferences: true, analytics: true, marketing: true });
      });
      on(document, 'click', '[data-cc-reject]', (e) => {
        e.preventDefault();
        ccApply(privacy, { preferences: false, analytics: false, marketing: false });
      });
      on(document, 'click', '[data-cc-save]', (e) => {
        e.preventDefault();
        const chosen = {};
        ccToggles().forEach((input) => { chosen[input.dataset.ccToggle] = input.checked; });
        ccApply(privacy, chosen);
      });
      on(document, 'click', '[data-cc-manage]', (e) => {
        e.preventDefault();
        if (!ccOptions) return;
        const opening = ccOptions.hidden;
        ccOptions.hidden = !opening;
        e.target.setAttribute('aria-expanded', String(opening));
      });
      // Permanent re-entry point, e.g. the footer link. Required: a choice has
      // to be as easy to change as it was to make.
      on(document, 'click', '[data-cc-reopen]', (e) => {
        e.preventDefault();
        ccSync(privacy);
        ccShow();
        if (ccOptions) ccOptions.hidden = false;
        if (ccManage) ccManage.setAttribute('aria-expanded', 'true');
        const first = ccBanner.querySelector('button, input');
        if (first) first.focus();
      });
    };

    // Shopify.loadFeatures is injected by content_for_header. If it is missing
    // or errors, the banner stays hidden and no consent is recorded — which
    // leaves the permission-gated pixels withheld, the safe failure direction.
    const bootConsent = () => {
      const S = window.Shopify;
      if (!S || typeof S.loadFeatures !== 'function') return;
      S.loadFeatures([{ name: 'consent-tracking-api', version: '0.1' }], (error) => {
        if (error || !window.Shopify.customerPrivacy) return;
        ccInit(window.Shopify.customerPrivacy);
      });
    };
    bootConsent();
  }

  // ---- Predictive search. The header input queries Shopify's /search/suggest
  // endpoint and drops the returned markup into the panel. We ask for a rendered
  // SECTION rather than JSON so prices go through the money filter and the
  // restricted-product rule stays in Liquid — see sections/predictive-search.liquid.
  // Suggestions are links only; nothing here adds to the bag.
  const psInput = document.querySelector('[data-ps-input]');
  const psPanel = document.querySelector('[data-ps-panel]');
  if (psInput && psPanel && (window.mccRoutes || {}).predictive_search_url) {
    const psStatus = document.querySelector('[data-ps-status]');
    const psUrl = window.mccRoutes.predictive_search_url;
    const psCache = new Map();
    let psTimer = null;
    let psAbort = null;
    // Escape and click-away are explicit dismissals. Without this flag, closing
    // with Escape from inside the panel calls psInput.focus(), the focus handler
    // refetches, and the panel a shopper just dismissed springs straight back.
    let psDismissed = false;

    const psItems = () => Array.from(psPanel.querySelectorAll('.ps-item, .ps-all'));

    function psClose() {
      psPanel.hidden = true;
      psPanel.innerHTML = '';
      psInput.setAttribute('aria-expanded', 'false');
      if (psAbort) { psAbort.abort(); psAbort = null; }
      clearTimeout(psTimer);
    }

    function psShow(html) {
      psPanel.innerHTML = html;
      const count = psPanel.querySelectorAll('.ps-item').length;
      psPanel.hidden = count === 0 && !psPanel.querySelector('.ps-empty');
      psInput.setAttribute('aria-expanded', String(!psPanel.hidden));
      if (psStatus) {
        psStatus.textContent = count > 0
          ? count + (count === 1 ? ' suggestion' : ' suggestions') + ' available'
          : 'No suggestions';
      }
    }

    async function psFetch(term) {
      if (psCache.has(term)) { psShow(psCache.get(term)); return; }
      if (psAbort) psAbort.abort();
      psAbort = new AbortController();
      const url = psUrl
        + '?q=' + encodeURIComponent(term)
        + '&resources[type]=product,collection,query'
        + '&resources[limit]=6'
        + '&resources[options][unavailable_products]=last'
        + '&section_id=predictive-search';
      try {
        const res = await fetch(url, { signal: psAbort.signal });
        if (!res.ok) throw new Error('suggest failed');
        const html = await res.text();
        psCache.set(term, html);
        psShow(html);
      } catch (err) {
        // AbortError just means a newer keystroke won; anything else leaves the
        // panel closed so the form still submits as a normal search.
        if (err.name !== 'AbortError') psClose();
      }
    }

    psInput.addEventListener('input', () => {
      const term = psInput.value.trim();
      psDismissed = false;
      clearTimeout(psTimer);
      if (term.length < 2) { psClose(); return; }
      psTimer = setTimeout(() => psFetch(term), 220);
    });

    psInput.addEventListener('focus', () => {
      const term = psInput.value.trim();
      if (!psDismissed && term.length >= 2 && psPanel.hidden) psFetch(term);
    });

    // Arrow keys walk the suggestions, Escape returns to the input.
    psInput.addEventListener('keydown', e => {
      if (e.key === 'Escape') { psDismissed = true; psClose(); return; }
      if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
      const items = psItems();
      if (!items.length) return;
      e.preventDefault();
      (e.key === 'ArrowDown' ? items[0] : items[items.length - 1]).focus();
    });

    psPanel.addEventListener('keydown', e => {
      if (e.key === 'Escape') { psDismissed = true; psClose(); psInput.focus(); return; }
      if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
      const items = psItems();
      const i = items.indexOf(document.activeElement);
      if (i === -1) return;
      e.preventDefault();
      const next = e.key === 'ArrowDown' ? i + 1 : i - 1;
      if (next < 0) psInput.focus();
      else if (next < items.length) items[next].focus();
    });

    document.addEventListener('click', e => {
      if (!psPanel.hidden && !psPanel.contains(e.target) && e.target !== psInput) { psDismissed = true; psClose(); }
    });
    document.addEventListener('focusin', e => {
      if (!psPanel.hidden && !psPanel.contains(e.target) && e.target !== psInput) { psDismissed = true; psClose(); }
    });
  }

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
