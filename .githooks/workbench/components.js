/* Delivery Workbench component library.
 *
 * Vanilla Web Components (Custom Elements v1). No Shadow DOM, no external
 * dependencies, no build step. All components render light DOM and rely on
 * the design tokens declared in style.css.
 *
 * Load via <script src="components.js"></script> — every component self-
 * registers through customElements.define().
 */

/* ------------------------------------------------------------------ */
/* Component: dw-button                                                */
/* ------------------------------------------------------------------ */
class DwButton extends HTMLElement {
  static get observedAttributes() {
    return ['variant', 'disabled', 'loading'];
  }

  connectedCallback() { this._render(); }
  attributeChangedCallback() { this._render(); }

  _render() {
    const variant  = this.getAttribute('variant') || 'secondary';
    const disabled = this.hasAttribute('disabled');
    const loading  = this.hasAttribute('loading');
    const label    = this.getAttribute('label') || this.textContent.trim() || '';

    // Preserve any inner HTML that was set declaratively on first render
    if (!this._label && label) this._label = label;
    const text = this._label || label;

    this.innerHTML = '';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.disabled = disabled || loading;
    btn.setAttribute('aria-disabled', String(disabled || loading));
    if (loading) btn.setAttribute('aria-busy', 'true');

    if (loading) {
      const spinner = document.createElement('span');
      spinner.className = 'dw-btn-spinner';
      spinner.setAttribute('aria-hidden', 'true');
      btn.appendChild(spinner);
    }

    const span = document.createElement('span');
    span.textContent = text;
    btn.appendChild(span);

    btn.addEventListener('click', (e) => {
      if (disabled || loading) { e.preventDefault(); e.stopPropagation(); }
    });

    this.appendChild(btn);
  }
}
customElements.define('dw-button', DwButton);


/* ------------------------------------------------------------------ */
/* Component: dw-card                                                  */
/* ------------------------------------------------------------------ */
class DwCard extends HTMLElement {
  static get observedAttributes() { return ['elevated']; }

  connectedCallback() { this._render(); }
  attributeChangedCallback() { this._render(); }

  _render() {
    // Only wrap on first connect — after that the user manages the slots
    if (this._initialized) return;
    this._initialized = true;

    const fragment = document.createDocumentFragment();

    // Header slot: look for [slot="header"]
    const headerSlot = this.querySelector('[slot="header"]');
    if (headerSlot) {
      const header = document.createElement('div');
      header.className = 'dw-card-header';
      headerSlot.removeAttribute('slot');
      header.appendChild(headerSlot);
      fragment.appendChild(header);
    }

    // Body: everything not slotted goes here
    const body = document.createElement('div');
    body.className = 'dw-card-body';
    const footerSlot = this.querySelector('[slot="footer"]');
    // Move remaining children to body
    while (this.firstChild) {
      if (this.firstChild === footerSlot) break;
      body.appendChild(this.firstChild);
    }
    fragment.appendChild(body);

    // Footer slot
    if (footerSlot) {
      const footer = document.createElement('div');
      footer.className = 'dw-card-footer';
      footerSlot.removeAttribute('slot');
      footer.appendChild(footerSlot);
      fragment.appendChild(footer);
    }

    this.appendChild(fragment);
  }
}
customElements.define('dw-card', DwCard);


/* ------------------------------------------------------------------ */
/* Component: dw-panel                                                 */
/* ------------------------------------------------------------------ */
class DwPanel extends HTMLElement {
  static get observedAttributes() {
    return ['title', 'collapsible', 'collapsed', 'resizable', 'min-width', 'max-width'];
  }

  connectedCallback() {
    this._render();
    this._boundKeydown = this._onKeydown.bind(this);
  }

  disconnectedCallback() {
    document.removeEventListener('keydown', this._boundKeydown);
  }

  attributeChangedCallback(name) {
    if (name === 'collapsed') {
      this._syncCollapsed();
    } else {
      this._render();
    }
  }

  _render() {
    if (this._initialized) return;
    this._initialized = true;

    const title       = this.getAttribute('title') || '';
    const collapsible = this.hasAttribute('collapsible');
    const resizable   = this.hasAttribute('resizable');
    const minW        = this.getAttribute('min-width');
    const maxW        = this.getAttribute('max-width');

    if (minW) this.style.minWidth = minW;
    if (maxW) this.style.maxWidth = maxW;

    // Collect existing children before restructuring
    const existingToolbar = this.querySelector('[slot="toolbar"]');
    const existingChildren = [];
    while (this.firstChild) {
      existingChildren.push(this.removeChild(this.firstChild));
    }

    // Header
    const header = document.createElement('div');
    header.className = 'dw-panel-header';

    const titleEl = document.createElement('h3');
    titleEl.className = 'dw-panel-title';
    titleEl.textContent = title;
    header.appendChild(titleEl);

    if (collapsible) {
      const toggle = document.createElement('button');
      toggle.className = 'dw-panel-toggle';
      toggle.type = 'button';
      toggle.setAttribute('aria-label', 'Toggle panel');
      toggle.setAttribute('aria-expanded', String(!this.hasAttribute('collapsed')));
      toggle.textContent = '▼';
      toggle.addEventListener('click', () => this._toggle());
      header.appendChild(toggle);
    }

    this.appendChild(header);

    // Toolbar
    if (existingToolbar) {
      const toolbar = document.createElement('div');
      toolbar.className = 'dw-panel-toolbar';
      existingToolbar.removeAttribute('slot');
      toolbar.appendChild(existingToolbar);
      this.appendChild(toolbar);
    }

    // Body
    const body = document.createElement('div');
    body.className = 'dw-panel-body';
    existingChildren.forEach(child => {
      if (child !== existingToolbar) body.appendChild(child);
    });
    this.appendChild(body);

    // Resize handle
    if (resizable) {
      const handle = document.createElement('div');
      handle.className = 'dw-panel-resize-handle';
      handle.setAttribute('role', 'separator');
      handle.setAttribute('aria-orientation', 'vertical');
      handle.setAttribute('aria-label', 'Resize panel');
      handle.setAttribute('tabindex', '0');
      this.appendChild(handle);
      this._initResize(handle);
    }

    this._syncCollapsed();
  }

  _syncCollapsed() {
    const toggle = this.querySelector('.dw-panel-toggle');
    if (toggle) {
      toggle.setAttribute('aria-expanded', String(!this.hasAttribute('collapsed')));
    }
  }

  _toggle() {
    if (this.hasAttribute('collapsed')) {
      this.removeAttribute('collapsed');
    } else {
      this.setAttribute('collapsed', '');
    }
    this.dispatchEvent(new CustomEvent('panel-toggle', {
      bubbles: true,
      detail: { collapsed: this.hasAttribute('collapsed') }
    }));
  }

  _initResize(handle) {
    let startX, startW;

    const onMove = (e) => {
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const delta = clientX - startX;
      const newW = Math.max(0, startW + delta);
      this.style.width = newW + 'px';
      this.dispatchEvent(new CustomEvent('panel-resize', {
        bubbles: true,
        detail: { width: newW }
      }));
    };

    const onUp = () => {
      handle.classList.remove('active');
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      document.removeEventListener('touchmove', onMove);
      document.removeEventListener('touchend', onUp);
    };

    const onDown = (e) => {
      e.preventDefault();
      startX = e.touches ? e.touches[0].clientX : e.clientX;
      startW = this.getBoundingClientRect().width;
      handle.classList.add('active');
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
      document.addEventListener('touchmove', onMove);
      document.addEventListener('touchend', onUp);
    };

    handle.addEventListener('mousedown', onDown);
    handle.addEventListener('touchstart', onDown, { passive: false });
  }

  _onKeydown(e) {
    if (e.key === 'Escape' && this.hasAttribute('collapsible') && !this.hasAttribute('collapsed')) {
      this._toggle();
    }
  }
}
customElements.define('dw-panel', DwPanel);


/* ------------------------------------------------------------------ */
/* Component: dw-status-pill                                           */
/* ------------------------------------------------------------------ */
class DwStatusPill extends HTMLElement {
  static get observedAttributes() { return ['status']; }

  connectedCallback() { this._render(); }
  attributeChangedCallback() { this._render(); }

  _render() {
    const status = this.getAttribute('status') || 'backlog';
    const labels = {
      'backlog': 'Backlog',
      'ready': 'Ready',
      'in-progress': 'In Progress',
      'blocked': 'Blocked',
      'on-hold': 'On Hold',
      'done': 'Done'
    };
    this.textContent = labels[status] || status;
    this.setAttribute('role', 'status');
    this.setAttribute('aria-label', 'Status: ' + (labels[status] || status));
  }
}
customElements.define('dw-status-pill', DwStatusPill);


/* ------------------------------------------------------------------ */
/* Component: dw-badge                                                 */
/* ------------------------------------------------------------------ */
class DwBadge extends HTMLElement {
  static get observedAttributes() { return ['count', 'variant']; }

  connectedCallback() { this._render(); }
  attributeChangedCallback() { this._render(); }

  _render() {
    const count   = this.getAttribute('count');
    const variant = this.getAttribute('variant') || 'default';

    const display = count != null ? count : '';
    this.textContent = display;

    this.setAttribute('role', 'status');
    if (count != null) {
      this.setAttribute('aria-label', count + (count === '1' ? ' notification' : ' notifications'));
    }
    if (variant === 'needs-you') {
      this.setAttribute('aria-label', (count || '') + ' needs your attention');
    }
  }
}
customElements.define('dw-badge', DwBadge);


/* ------------------------------------------------------------------ */
/* Component: dw-fold                                                  */
/* ------------------------------------------------------------------ */
class DwFold extends HTMLElement {
  static get observedAttributes() { return ['label', 'open']; }

  connectedCallback() {
    this._render();
    this._boundKeydown = this._onKeydown.bind(this);
    document.addEventListener('keydown', this._boundKeydown);
  }

  disconnectedCallback() {
    document.removeEventListener('keydown', this._boundKeydown);
  }

  attributeChangedCallback() { this._render(); }

  _render() {
    if (this._initialized) return;
    this._initialized = true;

    const label = this.getAttribute('label') || 'Technical details';

    // Preserve existing content
    const content = document.createDocumentFragment();
    while (this.firstChild) content.appendChild(this.firstChild);

    // Trigger button
    const trigger = document.createElement('button');
    trigger.className = 'dw-fold-trigger';
    trigger.type = 'button';
    trigger.setAttribute('aria-expanded', String(this.hasAttribute('open')));
    trigger.textContent = label;
    trigger.addEventListener('click', () => this._toggle());
    this.appendChild(trigger);

    // Content wrapper
    const body = document.createElement('div');
    body.className = 'dw-fold-content';
    body.setAttribute('role', 'region');
    body.appendChild(content);
    this.appendChild(body);
  }

  _toggle() {
    if (this.hasAttribute('open')) {
      this.removeAttribute('open');
    } else {
      this.setAttribute('open', '');
    }
    const trigger = this.querySelector('.dw-fold-trigger');
    if (trigger) {
      trigger.setAttribute('aria-expanded', String(this.hasAttribute('open')));
    }
  }

  _onKeydown(e) {
    if (e.key === 'Escape' && this.hasAttribute('open')) {
      this._toggle();
      const trigger = this.querySelector('.dw-fold-trigger');
      if (trigger) trigger.focus();
    }
  }
}
customElements.define('dw-fold', DwFold);


/* ------------------------------------------------------------------ */
/* Component: dw-skeleton                                              */
/* ------------------------------------------------------------------ */
class DwSkeleton extends HTMLElement {
  static get observedAttributes() { return ['lines', 'variant']; }

  connectedCallback() { this._render(); }
  attributeChangedCallback() { this._render(); }

  _render() {
    const lines   = parseInt(this.getAttribute('lines'), 10) || 3;
    const variant = this.getAttribute('variant') || 'text';

    this.setAttribute('role', 'status');
    this.setAttribute('aria-label', 'Loading');

    this.innerHTML = '';
    for (let i = 0; i < lines; i++) {
      const line = document.createElement('div');
      line.className = 'dw-skeleton-line';
      line.setAttribute('aria-hidden', 'true');

      // Vary widths for text variant to look natural
      if (variant === 'text' && i < lines - 1) {
        line.style.width = (85 + Math.floor(Math.random() * 15)) + '%';
      }

      this.appendChild(line);
    }
  }
}
customElements.define('dw-skeleton', DwSkeleton);


/* ------------------------------------------------------------------ */
/* Component: dw-empty-state                                           */
/* ------------------------------------------------------------------ */
class DwEmptyState extends HTMLElement {
  static get observedAttributes() {
    return ['icon', 'heading', 'message', 'action-label', 'action-href'];
  }

  connectedCallback() { this._render(); }
  attributeChangedCallback() { this._render(); }

  _render() {
    const icon        = this.getAttribute('icon') || '';
    const heading     = this.getAttribute('heading') || '';
    const message     = this.getAttribute('message') || '';
    const actionLabel = this.getAttribute('action-label');
    const actionHref  = this.getAttribute('action-href');

    this.setAttribute('role', 'status');
    this.innerHTML = '';

    if (icon) {
      const iconEl = document.createElement('div');
      iconEl.className = 'dw-empty-icon';
      iconEl.setAttribute('aria-hidden', 'true');
      iconEl.textContent = icon;
      this.appendChild(iconEl);
    }

    if (heading) {
      const h = document.createElement('h3');
      h.className = 'dw-empty-heading';
      h.textContent = heading;
      this.appendChild(h);
    }

    if (message) {
      const p = document.createElement('p');
      p.className = 'dw-empty-message';
      p.textContent = message;
      this.appendChild(p);
    }

    if (actionLabel && actionHref) {
      const a = document.createElement('a');
      a.className = 'dw-empty-action';
      a.href = actionHref;
      a.textContent = actionLabel;
      this.appendChild(a);
    }
  }
}
customElements.define('dw-empty-state', DwEmptyState);


/* ------------------------------------------------------------------ */
/* Component: dw-stream-line                                           */
/* ------------------------------------------------------------------ */
class DwStreamLine extends HTMLElement {
  static get observedAttributes() { return ['type', 'timestamp']; }

  connectedCallback() { this._render(); }
  attributeChangedCallback() { this._render(); }

  _render() {
    if (this._initialized) return;
    this._initialized = true;

    const type      = this.getAttribute('type') || 'text';
    const timestamp = this.getAttribute('timestamp') || '';

    // Preserve existing content
    const content = document.createDocumentFragment();
    while (this.firstChild) content.appendChild(this.firstChild);

    // Timestamp column
    const ts = document.createElement('time');
    ts.className = 'dw-stream-ts';
    if (timestamp) {
      ts.dateTime = timestamp;
      ts.textContent = this._formatTime(timestamp);
    }
    this.appendChild(ts);

    // Body column
    const body = document.createElement('div');
    body.className = 'dw-stream-body';
    body.appendChild(content);
    this.appendChild(body);

    // ARIA
    if (type === 'question') {
      this.setAttribute('role', 'alert');
    }
  }

  _formatTime(ts) {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch (_) {
      return ts;
    }
  }
}
customElements.define('dw-stream-line', DwStreamLine);


/* ------------------------------------------------------------------ */
/* Component: dw-toast                                                 */
/* ------------------------------------------------------------------ */
class DwToast extends HTMLElement {
  static get observedAttributes() { return ['variant', 'duration', 'dismissible']; }

  connectedCallback() {
    this._render();
    this._startTimer();
  }

  disconnectedCallback() {
    this._clearTimer();
  }

  attributeChangedCallback() {
    if (this._initialized) this._render();
  }

  _render() {
    if (this._initialized) return;
    this._initialized = true;

    const variant     = this.getAttribute('variant') || 'info';
    const dismissible = this.hasAttribute('dismissible');

    this.setAttribute('role', 'alert');
    this.setAttribute('aria-live', 'assertive');

    const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌' };

    // Preserve existing content
    const content = document.createDocumentFragment();
    while (this.firstChild) content.appendChild(this.firstChild);

    // Icon
    const iconEl = document.createElement('span');
    iconEl.className = 'dw-toast-icon';
    iconEl.setAttribute('aria-hidden', 'true');
    iconEl.textContent = icons[variant] || icons.info;
    this.appendChild(iconEl);

    // Content
    const contentEl = document.createElement('div');
    contentEl.className = 'dw-toast-content';
    contentEl.appendChild(content);
    this.appendChild(contentEl);

    // Dismiss button
    if (dismissible) {
      const btn = document.createElement('button');
      btn.className = 'dw-toast-dismiss';
      btn.type = 'button';
      btn.setAttribute('aria-label', 'Dismiss notification');
      btn.textContent = '✕';
      btn.addEventListener('click', () => this._dismiss());
      this.appendChild(btn);
    }
  }

  _startTimer() {
    const duration = parseInt(this.getAttribute('duration'), 10) || 4000;
    if (duration > 0) {
      this._timer = setTimeout(() => this._dismiss(), duration);
    }
  }

  _clearTimer() {
    if (this._timer) {
      clearTimeout(this._timer);
      this._timer = null;
    }
  }

  _dismiss() {
    this._clearTimer();
    this.classList.add('dw-toast-out');
    const onEnd = () => {
      this.dispatchEvent(new CustomEvent('toast-dismiss', { bubbles: true }));
      this.remove();
    };
    this.addEventListener('animationend', onEnd, { once: true });
    // Fallback if animation is disabled
    setTimeout(onEnd, 200);
  }
}
customElements.define('dw-toast', DwToast);
