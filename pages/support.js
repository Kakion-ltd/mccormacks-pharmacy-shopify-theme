// Minimal local runtime for the .dc.html design references.
// Implements the DCLogic component base, {{ }} hole interpolation,
// <sc-if>/<sc-for> structural tags, on* event holes, and style-hover/style-focus.
(() => {
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const HOLE = /\{\{\s*([\w$.]+)\s*\}\}/g;
  const SOLE_HOLE = /^\s*\{\{\s*([\w$.]+)\s*\}\}\s*$/;

  let template, mount, component;

  class DCLogic {
    constructor() {
      this.props = {};
    }
    setState(update) {
      const next = typeof update === 'function' ? update(this.state) : update;
      let changed = false;
      for (const k in next) {
        if (!Object.is(this.state[k], next[k])) { changed = true; break; }
      }
      Object.assign(this.state, next);
      if (changed) render();
    }
  }
  window.DCLogic = DCLogic;

  // Just enough React for the scripts' React.createElement('img', {...}) calls.
  window.React = window.React || {
    createElement(tag, props, ...children) {
      const el = document.createElement(tag);
      for (const [k, v] of Object.entries(props || {})) {
        if (k === 'style' && v && typeof v === 'object') {
          for (const [sk, sv] of Object.entries(v)) el.style[sk] = sv;
        } else if (k.startsWith('on') && typeof v === 'function') {
          el.addEventListener(k.slice(2).toLowerCase(), v);
        } else {
          el.setAttribute(k === 'className' ? 'class' : k, v);
        }
      }
      for (const c of children.flat()) {
        if (c != null) el.append(c instanceof Node ? c : String(c));
      }
      return el;
    },
  };

  // Hide the raw template (with visible {{ }} holes) until first render.
  document.head.appendChild(document.createElement('style')).textContent = 'x-dc{display:none}';

  function resolve(path, scopes) {
    if (path === 'true') return true;
    if (path === 'false') return false;
    const [head, ...rest] = path.split('.');
    for (let i = scopes.length - 1; i >= 0; i--) {
      if (scopes[i] != null && head in scopes[i]) {
        return rest.reduce((v, k) => (v == null ? undefined : v[k]), scopes[i][head]);
      }
    }
    return undefined;
  }

  function interp(str, scopes) {
    return str.replace(HOLE, (_, p) => {
      const v = resolve(p, scopes);
      return v == null ? '' : v;
    });
  }

  function soleValue(str, scopes) {
    const m = str.match(SOLE_HOLE);
    return m ? resolve(m[1], scopes) : undefined;
  }

  // style-hover / style-focus: overlay extra declarations on the base inline style.
  function wireOverlay(el, kind, extra, onEvt, offEvt) {
    if (!el._ov) {
      el._ov = { base: null, hover: false, focus: false, hoverCss: '', focusCss: '' };
    }
    el._ov[kind + 'Css'] = extra;
    const apply = () => {
      if (el._ov.base == null) el._ov.base = el.getAttribute('style') || '';
      el.setAttribute('style', el._ov.base +
        (el._ov.hover ? ';' + el._ov.hoverCss : '') +
        (el._ov.focus ? ';' + el._ov.focusCss : ''));
    };
    el.addEventListener(onEvt, () => { el._ov[kind] = true; apply(); });
    el.addEventListener(offEvt, () => { el._ov[kind] = false; apply(); });
  }

  function build(node, scopes, out, ns) {
    if (node.nodeType === Node.TEXT_NODE) {
      const sole = node.nodeValue.match(SOLE_HOLE);
      const v = sole && resolve(sole[1], scopes);
      if (v instanceof Node) out.appendChild(v);
      else out.appendChild(document.createTextNode(interp(node.nodeValue, scopes)));
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    const tag = node.tagName.toLowerCase();

    if (tag === 'sc-if') {
      if (soleValue(node.getAttribute('value') || '', scopes)) {
        for (const c of node.childNodes) build(c, scopes, out, ns);
      }
      return;
    }
    if (tag === 'sc-for') {
      const list = soleValue(node.getAttribute('list') || '', scopes) || [];
      const name = node.getAttribute('as') || 'item';
      list.forEach((item, index) => {
        const scope = { [name]: item, index };
        for (const c of node.childNodes) build(c, scopes.concat(scope), out, ns);
      });
      return;
    }
    if (tag === 'script' || tag === 'helmet') return;

    const childNs = tag === 'svg' ? SVG_NS : ns;
    const el = childNs ? document.createElementNS(childNs, tag) : document.createElement(tag);

    for (const attr of node.attributes) {
      const { name, value } = attr;
      if (name.startsWith('hint-')) continue;
      if (name === 'style-hover') { wireOverlay(el, 'hover', interp(value, scopes), 'mouseenter', 'mouseleave'); continue; }
      if (name === 'style-focus') { wireOverlay(el, 'focus', interp(value, scopes), 'focus', 'blur'); continue; }
      if (name === 'defaultchecked') { if (soleValue(value, scopes)) el.checked = true; continue; }
      if (name.startsWith('on') && SOLE_HOLE.test(value)) {
        const fn = soleValue(value, scopes);
        if (typeof fn === 'function') el.addEventListener(name.slice(2), fn);
        continue;
      }
      el.setAttribute(name, interp(value, scopes));
    }

    for (const c of node.childNodes) build(c, scopes, el, childNs);
    out.appendChild(el);
  }

  // Re-renders replace the whole tree; keep scroll positions, form values, and focus.
  function fieldKey(el) {
    const base = el.name || el.id;
    if (!base) return null;
    return el.type === 'radio' ? base + ':' + el.value : base;
  }

  function snapshot() {
    const s = { scrolls: [], fields: new Map(), focus: null };
    mount.querySelectorAll('[id]').forEach(el => {
      if (el.scrollLeft || el.scrollTop) s.scrolls.push([el.id, el.scrollLeft, el.scrollTop]);
    });
    mount.querySelectorAll('input, textarea, select').forEach(el => {
      const key = fieldKey(el);
      if (!key) return;
      const checkable = el.type === 'checkbox' || el.type === 'radio';
      s.fields.set(key, checkable ? el.checked : el.value);
      if (el === document.activeElement) {
        s.focus = { key };
        try { s.focus.start = el.selectionStart; s.focus.end = el.selectionEnd; } catch (_) {}
      }
    });
    return s;
  }

  function restore(s) {
    for (const [id, left, top] of s.scrolls) {
      const el = document.getElementById(id);
      if (el) { el.scrollLeft = left; el.scrollTop = top; }
    }
    mount.querySelectorAll('input, textarea, select').forEach(el => {
      const key = fieldKey(el);
      if (key == null || !s.fields.has(key)) return;
      const v = s.fields.get(key);
      if (el.type === 'checkbox' || el.type === 'radio') el.checked = v;
      else el.value = v;
      if (s.focus && s.focus.key === key) {
        el.focus({ preventScroll: true });
        if (s.focus.start != null) {
          try { el.setSelectionRange(s.focus.start, s.focus.end); } catch (_) {}
        }
      }
    });
  }

  function render() {
    const vals = component.renderVals();
    const snap = mount.childElementCount ? snapshot() : null;
    const frag = document.createDocumentFragment();
    for (const c of template.childNodes) build(c, [vals], frag, null);
    mount.replaceChildren(frag);
    if (snap) restore(snap);
  }

  document.addEventListener('DOMContentLoaded', () => {
    const xdc = document.querySelector('x-dc');
    if (!xdc) return;

    const helmet = xdc.querySelector('helmet');
    if (helmet) {
      [...helmet.children].forEach(c => document.head.appendChild(c));
      helmet.remove();
    }

    const logic = document.querySelector('script[data-dc-script]');
    const Component = new Function('DCLogic', logic.textContent + '\nreturn Component;')(DCLogic);
    logic.remove();

    template = xdc;
    mount = document.createElement('div');
    xdc.replaceWith(mount);
    component = new Component();
    render();
  });
})();
